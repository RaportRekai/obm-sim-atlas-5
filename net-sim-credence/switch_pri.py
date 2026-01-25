# The code is subject to Purdue University copyright policies.
# Do not share, distribute, or post online.

import sys
import queue
import hashlib
from link import Link
import math
import copy
import joblib
import numpy as np
import re
import os
# Import the FastForest class
from FastForest import FastForest

class Switch():
    """
    Switch class implementing CREDENCE logic adapted for SWIFT.
    Features:
    - ML-based Admission Control (FastForest)
    - Virtual LQD State Tracking
    - SWIFT specific: Hop counting increment on departure
    """

    def __init__(self, addr, num_tor_ports, num_agg_ports, hosts_per_rack):
        """Initialize parameters"""
        self.addr = addr
        self.links = {}
        self.queues = {}
        self.voq_rr = {}
        self.per_port_max_qsize = 5
        self.K = 25 # ECN Threshold

        self.num_tor_ports = num_tor_ports
        self.num_agg_ports = num_agg_ports
        self.hosts_per_rack = hosts_per_rack
        self.tor_buff_size = self.per_port_max_qsize * self.num_tor_ports
        self.agg_buff_size = self.per_port_max_qsize * self.num_agg_ports
        self.packet_dropped = 0
        self.port_qsize = {}  # Physical Queue Length per port
        self.priority_classes = 3
        
        # --- CREDENCE INITIALIZATION ---
        self.model = None
        # EWMA Parameters
        self.ewma_alpha = 2 / (30 + 1)
        self.avg_q_len = {}          # Moving average of Queue Length per port
        self.avg_shared_occ = 0.0    # Moving average of Shared Buffer Occupancy
        
        # Virtual LQD State
        self.virtual_T = {} 
        self.virtual_gamma = 0       # Sum of all virtual thresholds
        # -------------------------------

        if self.addr[0] == 't':
            self.ports = num_tor_ports
            self.total_buffer_size = self.per_port_max_qsize * num_tor_ports
            self.N = self.ports
            self.voq_port_qsize = [[0 for i in range(self.priority_classes)] for _ in range(self.N)]
        elif self.addr[0] == 'a':
            self.ports = num_agg_ports
            self.total_buffer_size = self.per_port_max_qsize * num_agg_ports
            self.N = self.ports
            self.voq_port_qsize = [[0 for i in range(self.priority_classes)] for _ in range(self.N)]

        # Initialize tracking dicts
        for i in range(1, self.N + 1):
            self.virtual_T[i] = 0
            self.avg_q_len[i] = 0.0
            
        self.total_usage = 0 
        self.final_add = [0 for i in range(self.N)]
        self.sent = 0
        self.t = 0
        self.track = 0

        # --- LOAD ML MODEL ---
        try:
            jobfile = re.compile(f"model_ports{self.ports}_")
            found = False
            for filename in os.listdir('.'):
                if jobfile.match(filename):
                    print(f"Loading raw model for {self.addr}: {filename}...")
                    raw_model = joblib.load(filename)
                    # Convert to FastForest
                    self.model = FastForest(raw_model)
                    del raw_model 
                    print(f"CREDENCE: Optimized model ready for {self.addr}.")
                    found = True
                    break
            if not found:
                print(f"WARNING: No matching model found for {self.addr} (ports={self.ports})")
        except Exception as e:
            print(f"Error loading model: {e}")

    def _update_virtual_lqd(self, port_idx, event_type):
        """
        Updates the virtual thresholds T according to LQD logic.
        This simulates what LQD *would* do, to generate features for the ML model.
        """
        if event_type == 'arrival':
            if self.virtual_gamma == self.total_buffer_size:
                # Push-out simulation
                if self.virtual_T:
                    j = max(self.virtual_T, key=self.virtual_T.get)
                    self.virtual_T[j] -= 1
                    self.virtual_T[port_idx] += 1
            else:
                self.virtual_T[port_idx] += 1
                self.virtual_gamma += 1
                
        elif event_type == 'departure':
            if self.virtual_T[port_idx] > 0:
                self.virtual_T[port_idx] -= 1
                self.virtual_gamma -= 1

    def _update_ewma(self, port_idx):
        """Updates exponentially weighted moving averages"""
        curr_q = self.port_qsize[port_idx]
        curr_occ = self.total_usage
        
        self.avg_q_len[port_idx] = (self.ewma_alpha * curr_q) + \
                                   ((1 - self.ewma_alpha) * self.avg_q_len[port_idx])
        
        self.avg_shared_occ = (self.ewma_alpha * curr_occ) + \
                              ((1 - self.ewma_alpha) * self.avg_shared_occ)

    def runSwitch(self, currTimeslot):
        """Main loop of switch"""
        self.t += 1
        
        # --- SENDING PHASE (DEPARTURES) ---
        for port in self.links.keys():
            flag_1 = 0
            for i in range(self.priority_classes):
                if not self.queues[port][i].empty():
                    for j in range(0, self.queues[port][i].qsize()):
                        packet = self.queues[port][i].get_nowait()
                        if packet.invalid == 0:
                            
                            # --- SWIFT MODIFICATION START ---
                            # Increment hop count before sending
                            packet.hops += 1
                            # --- SWIFT MODIFICATION END ---
                            
                            self.links[port].send(packet, self.addr, currTimeslot)
                            
                            self.port_qsize[port] -= 1
                            self.sent += 1
                            self.total_usage -= 1 
                            self.voq_port_qsize[port-1][i] -= 1
                            
                            # [CREDENCE HOOK] Update Virtual LQD on departure
                            self._update_virtual_lqd(port, 'departure')
                            
                            flag_1 = 1
                            assert(self.port_qsize[port] >= 0)
                            break
                    if flag_1:
                        break
                else:
                    continue

        # --- RECEIVING PHASE (ARRIVALS) ---
        for port in self.links.keys():
            packet = self.links[port].recv(self.addr, currTimeslot)
            if packet:
                self.handleRecvdPacket(packet, currTimeslot)
            else:
                self.final_add[port-1] = 0
        
        return self.packet_dropped, [] # Return empty list for dropped details if not tracking
        
    def setECNFlag(self, packet, outPort):
        if self.port_qsize[outPort] > self.K:
            packet.ecnFlag = 1

    def ecmp(self, packet):
        flowid = packet.srcAddr + packet.dstAddr + str(packet.srcPort) + str(packet.dstPort)
        outPort = int(hashlib.sha256(flowid.encode('utf-8')).hexdigest(), 16) % (self.num_tor_ports - self.hosts_per_rack) + (self.hosts_per_rack + 1)
        return outPort

    def getOutPort(self, switchId, packet):
        if switchId[0] == 't':
            if int(packet.dstAddr[1:]) >= int(switchId[1])*16-15 and int(packet.dstAddr[1:]) <= int(switchId[1])*16:
                return int(packet.dstAddr[1:])-((int(switchId[1])-1)*16)
            else:
                return self.ecmp(packet)
        elif switchId[0] == 'a':
            return int((int(packet.dstAddr[1:])-1)/16)+1

    def handleRecvdPacket(self, packet, arrivalTime):
        """
        Handle the packet received using CREDENCE logic.
        """
        outPort = self.getOutPort(self.addr, packet)
        
        # 1. Update Virtual Thresholds
        self._update_virtual_lqd(outPort, 'arrival')
        
        # 2. Update Stats
        self._update_ewma(outPort)
        
        decision = "DROP"
        
        # --- CREDENCE LOGIC START ---
        
        # Safeguard Condition
        longest_queue_len = 0
        if len(self.port_qsize) > 0:
            longest_queue_len = max(self.port_qsize.values())

        safeguard_threshold = self.total_buffer_size / self.N
        
        if longest_queue_len < safeguard_threshold:
            decision = "ACCEPT"
        else:
            # Threshold Check
            current_q_len = self.port_qsize.get(outPort, 0)
            virtual_threshold = self.virtual_T[outPort]
            
            if current_q_len < virtual_threshold:
                if self.total_usage < self.total_buffer_size:
                    # ML Prediction
                    if self.model:
                        prediction = self.model.predict(
                            current_q_len, 
                            self.total_usage, 
                            self.avg_q_len[outPort], 
                            self.avg_shared_occ
                        )
                        if prediction == 0:
                            decision = "ACCEPT"
                        else:
                            decision = "DROP"
                    else:
                        # Fallback if model failed to load
                        decision = "ACCEPT"
                else:
                    decision = "DROP" # Physically full
            else:
                decision = "DROP" # Exceeds virtual threshold
                
        # --- EXECUTE DECISION ---
        if decision == "ACCEPT":
            if self.total_usage < self.total_buffer_size:
                inPort_priority = packet.priority
                self.total_usage += 1
                self.queues[outPort][inPort_priority-1].put(packet)
                self.port_qsize[outPort] += 1
                self.voq_port_qsize[outPort-1][inPort_priority-1] += 1
                self.setECNFlag(packet, outPort)
            else:
                self.packet_dropped += 1
        else:
            self.packet_dropped += 1