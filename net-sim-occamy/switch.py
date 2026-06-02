# The code is subject to Purdue University copyright policies.
# Do not share, distribute, or post online.

import sys
import queue
import hashlib
from link import Link
import math
import copy


class Switch():
    """Switch class"""

    def __init__(self, addr, num_tor_ports, num_agg_ports, hosts_per_rack,load):
        """Initialize parameters"""
        self.addr = addr  # address of switch
        self.links = {}   # links indexed by port
        self.queues = {}  # list of virtual output queues per port
        self.voq_rr = {}  # stores the VOQ per port to be serviced next
        self.per_port_max_qsize = 4  # in terms of number of size in Bytes
        self.K = 4                   # threshold for ECN marking

        self.num_tor_ports = num_tor_ports
        self.num_agg_ports = num_agg_ports
        self.hosts_per_rack = hosts_per_rack
        
        # Buffer sizes
        self.tor_buff_size = self.per_port_max_qsize * self.num_tor_ports 
        self.agg_buff_size = self.per_port_max_qsize * self.num_agg_ports 
        
        self.packet_dropped = 0
        self.port_qsize = {}  # number of packets queued per port
        self.priority_classes = 3

        if self.addr[0] == 't':
            self.ports = num_tor_ports
            self.total_buffer_size = self.per_port_max_qsize*num_tor_ports
            self.N = self.ports
            self.voq_port_qsize = [[0 for i in range(self.priority_classes)] for _ in range(self.N)]
            self.per_port_buffer = [[0 for _ in range(self.priority_classes)] for i in range(self.ports)]
            print(num_tor_ports)
        elif self.addr[0] == 'a':
            self.ports = num_agg_ports
            self.total_buffer_size = self.per_port_max_qsize*num_agg_ports
            self.N = self.ports
            self.voq_port_qsize = [[0 for i in range(self.priority_classes)] for _ in range (self.N)]
            self.per_port_buffer = [[0 for _ in range(self.priority_classes)] for i in range(self.ports)]
            print(num_agg_ports)
            

        #########################################################################################################
        self.total_usage = 0 
        self.final_add = [0 for i in range(self.N)]
        self.T = [self.total_buffer_size/(self.ports*self.priority_classes) for i in range(self.priority_classes)]
        self.sent = 0
        self.alpha_set = [[20,15,10],[20,15,10],[20,15,10]] #[[0.5,0.4,0.2],[0.5,0.4,0.2],[0.5,0.4,0.2]]#[[20,15,10],[8,6,4],[8,6,4]]
        self.alpha = [20,15,10] #self.alpha_set[int(load/0.3) -1] 
        self.t = 0
        self.track = 0

        # --- OCCAMY VARIABLES ---
        self.drop_timer = 0
        self.expulsion_rr_idx = 0 # To track Round Robin across ports for fairness

    def runSwitch(self, currTimeslot):
        """Main loop of switch"""
        self.t += 1
        
        # ---------------------------------------------------------------------
        # 1. OCCAMY EXPULSION LOGIC (Priority Aware)
        # ---------------------------------------------------------------------
        self.drop_timer += 1
        
        # Check for expulsion every 2 cycles (simulating latency)
        if self.drop_timer % 2 == 0:
            
            # Get list of ports to iterate over
            ports_list = sorted(list(self.links.keys()))
            num_ports = len(ports_list)
            packet_expelled = False
            
            # Iterate through ports starting from the last checked index (Round Robin)
            for i in range(num_ports):
                curr_port_idx = (self.expulsion_rr_idx + i) % num_ports
                port = ports_list[curr_port_idx]
                
                # PRIORITY AWARENESS:
                # Check priorities from Lowest (Index 2) to Highest (Index 0).
                # We want to drop low priority packets first if they are violating thresholds.
                for prio_idx in range(self.priority_classes - 1, -1, -1):
                    
                    # Check if this specific VOQ exceeds its specific Threshold T[prio_idx]
                    if self.voq_port_qsize[port-1][prio_idx] > self.T[prio_idx]:
                        
                        # Queue is over threshold, check if it has packets to drop
                        pq = self.queues[port][prio_idx]
                        
                        if hasattr(pq, 'queue') and len(pq.queue) > 0:
                            head_packet = pq.queue[0]
                            
                            # Only drop if not already dropped
                            if head_packet.invalid == 0 and head_packet.prvt == 0:
                                head_packet.invalid = 1 
                                
                                # Decrement usage counters immediately so space is "freed"
                                self.total_usage -= 1
                                self.port_qsize[port] -= 1
                                self.voq_port_qsize[port-1][prio_idx] -= 1
                                self.packet_dropped += 1
                                
                                # Update RR index for next time
                                self.expulsion_rr_idx = (curr_port_idx + 1) % num_ports
                                packet_expelled = True
                                break 
                
                if packet_expelled:
                    break

        # ---------------------------------------------------------------------
        # 2. PACKET SENDING LOGIC (Updated to skip Expelled Packets)
        # ---------------------------------------------------------------------
        for port in self.links.keys(): 
            
            flag_1 = 0
            for i in range(self.priority_classes):
                if not self.queues[port][i].empty():
                    
                    # We might encounter "invalid" packets at the head. 
                    # We must drain them until we find a valid one or the queue is empty.
                    while not self.queues[port][i].empty():
                        
                        # Get packet (peek is not standard in queue.Queue, so we get it)
                        packet = self.queues[port][i].get_nowait()
                        
                        # If packet was expelled (invalid), discard and loop again
                        if packet.invalid == 1:
                            continue 
                        
                        # VALID PACKET FOUND
                        else:
                            packet.hops +=1
                            if packet.prvt == 1:
                                if self.per_port_buffer[port-1][i]==1:
                                    self.per_port_buffer[port-1][i] = 0
                                else:
                                    breakpoint()
                            else:
                                if self.port_qsize[port] <=0:
                                    breakpoint()
                                self.port_qsize[port] -= 1
                                self.total_usage-=1 
                                self.voq_port_qsize[port-1][i]-=1
                            
                            

                            packet.prvt = 0
                            self.links[port].send(packet, self.addr, currTimeslot)
                            # print(f"sending packet from {i} when other prioritites have length = {self.voq_port_qsize[port-1]}")
                            # if i == 0:
                            #     breakpoint()
                            
                            self.sent+=1
                            
                            flag_1 = 1
                            try:
                                assert(self.port_qsize[port] >= 0)
                            except AssertionError:
                                print(f"Port {port} has negative queue size")
                                breakpoint()
                            break
                    
                    if flag_1:
                        break # Break the priority loop (one packet sent per port per timeslot)

                else:
                    continue

        # ---------------------------------------------------------------------
        # 3. PACKET RECEIVING LOGIC
        # ---------------------------------------------------------------------
        for port in self.links.keys():
            packet = self.links[port].recv(self.addr, currTimeslot)
            if packet:
                # Initialize invalid flag for Occamy
                packet.invalid = 0 
                self.handleRecvdPacket(packet, currTimeslot)
            else:
                self.final_add[port-1] = 0
        
        return self.packet_dropped
        
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
            
    ########################################################################
    # DYNAMIC THRESHOLD CALCULATION
    ########################################################################

    def threshold_calculate(self):
        # Recalculate T for each priority class based on remaining buffer
        for n2 in range(self.priority_classes):
            self.T[n2] = self.alpha[n2] * (self.total_buffer_size - self.total_usage)

    ########################################################################
    # PACKET ADMISSION CONTROL
    ########################################################################

    def handleRecvdPacket(self, packet, arrivalTime):
        """Handle the packet received on the specified input port."""
        outPort = self.getOutPort(self.addr, packet)
        
        # Check Global Buffer Space
        if self.per_port_buffer[outPort-1][packet.priority-1] == 0:
            self.per_port_buffer[outPort-1][packet.priority-1] = 1
            # we have to introduce a new field for packet.py
            packet.prvt = 1
            self.queues[outPort][packet.priority-1].put(packet)

        elif self.total_buffer_size > self.total_usage:
            
            # Map packet priority to VOQ index
            # Warning: Assuming packet.priority is 0, 1, or 2 based on your code's logic
            # Your code used 'inPort = packet.priority' effectively as the queue index
            prio_idx = packet.priority - 1
            
            # Dynamic Threshold Admission Check
            if self.voq_port_qsize[outPort-1][prio_idx] < self.T[prio_idx]:
                
                self.total_usage += 1
                self.queues[outPort][prio_idx].put(packet)
                self.port_qsize[outPort] += 1
                self.voq_port_qsize[outPort-1][prio_idx] += 1
                self.setECNFlag(packet, outPort)
                
            else:
                # Threshold Exceeded -> Drop
                print("Packet drop due to DT")
                self.packet_dropped += 1
        
        else:
            # Physical Space Exceeded -> Drop
            print("Packet drop due to space constraint")
            self.packet_dropped += 1
        
        # Recalculate Thresholds after every admission attempt
        self.threshold_calculate()