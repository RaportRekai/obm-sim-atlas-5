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

    def __init__(self, addr, num_tor_ports, num_agg_ports, hosts_per_rack):
        """Initialize parameters"""
        self.addr = addr  # address of switch
        self.links = {}   # links indexed by port
        self.queues = {}  # list of virtual output queues per port
        self.voq_rr = {}  # stores the VOQ per port to be serviced next
        self.per_port_max_qsize = 5  # in terms of number of 1500B packets
        self.K = 4                   # threshold for ECN marking
        self.flag = 0
        self.num_tor_ports = num_tor_ports
        self.num_agg_ports = num_agg_ports
        self.hosts_per_rack = hosts_per_rack
        self.tor_buff_size = self.per_port_max_qsize * self.num_tor_ports 
        self.agg_buff_size = self.per_port_max_qsize * self.num_agg_ports 
        self.packet_dropped = 0
        self.port_qsize = {}  # number of packets queued per port
        self.priority_classes = 3
        
        if self.addr[0] == 't':
            self.ports = num_tor_ports
            self.total_buffer_size = self.per_port_max_qsize*num_tor_ports
            self.N = 1 if num_tor_ports < 1 else 2 ** ((num_tor_ports - 1).bit_length())
            self.voq_port_qsize = [[0 for i in range(self.priority_classes)] for _ in range(self.N)]
            print(num_tor_ports)
        elif self.addr[0] == 'a':
            self.ports = num_agg_ports
            self.total_buffer_size = self.per_port_max_qsize*num_agg_ports
            self.N = 1 if num_agg_ports < 1 else 2 ** ((num_agg_ports - 1).bit_length())
            self.voq_port_qsize = [[0 for i in range(self.priority_classes)] for _ in range (self.N)]
            print(num_agg_ports)

        self.total_usage = 0 
        self.final_add = [0 for i in range(self.N)]
        self.T = self.total_buffer_size
        self.sent = 0
        self.t = 0
        self.k = 0
        self.t_track = 0
        self.buffer = [[-1,-1] for i in range(self.N)]
        self.priority_max_q_l = 0
        self.dropped = []

        # --- DATA ACQUISITION / TRAINING VARIABLES (IMPORTED) ---
        self.avg_q_len = 0.0
        self.avg_occ = 0.0
        # Alpha for EWMA. Fixed RTT = 30 timestamps.
        # NOTE: Your target code originally had self.alpha = 2. 
        # I have replaced it with the Source code's alpha logic for proper moving averages.
        self.alpha = 2 / (30 + 1)

        # Switch-assigned unique ID for packet arrivals (per switch)
        self.arrival_uid = 0

        # The Master Log for Training Data
        # Format: { "switch_uid": [queueLength, sharedOccupancy, avgQ, avgOcc, drop_status] }
        self.packet_history = {}
        # --------------------------------------------------------

    def runSwitch(self, currTimeslot):
        """Main loop of switch"""
        self.t+=1
        self.dropped = []

        for port in self.links.keys():
            flag_1 = 0
            for i in range(self.priority_classes):
                if not self.queues[port][i].empty():
                    for j in range(0,self.queues[port][i].qsize()):
                        packet = self.queues[port][i].get_nowait()
                        if packet.invalid == 0:
                            packet.hops +=1
                            self.links[port].send(packet, self.addr, currTimeslot)
                            
                            self.port_qsize[port] -= 1
                            self.sent+=1
                            self.total_usage-=1 
                            self.voq_port_qsize[port-1][i]-=1
                            flag_1 = 1
                            assert(self.port_qsize[port] >= 0)
                            break
                        else:
                            # Packet was virtually dropped by LQD
                            self.dropped.append((packet.dstAddr,packet.srcAddr,packet.srcPort,packet.dstPort,packet.seqNum))

                    if flag_1:
                        break
                else:
                    continue

        self.k = 0
        self.buffer = [[-1,-1] for i in range(self.N)]
        
        # Check if port_qsize is not empty before finding max
        if self.port_qsize:
            self.largest_index = max(self.port_qsize, key=self.port_qsize.get)
        else:
            self.largest_index = None

        for port in self.links.keys():
            packet = self.links[port].recv(self.addr, currTimeslot)
            if packet:
                self.handleRecvdPacket(port, packet, currTimeslot)
        
        if self.k > 0:
            mem = self.fetch()
            self.allct(mem,currTimeslot)
        
        return self.packet_dropped, self.dropped
        
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

    def fetch(self):
        """
        Select up to self.k packets across per-class VOQs at self.largest_index.
        """
        mem_loc = []
        # Turn off debug for cleaner output or integration
        DEBUG = getattr(self, "debug_fetch", False) 

        if self.largest_index is None or self.largest_index not in self.queues:
            return mem_loc

        C = getattr(self, "priority_classes", 1)
        port_queues = self.queues[self.largest_index]

        ts  = [None] * C
        pos = [None] * C
        ptr = [-1] * C

        # Initialize candidates
        for i in range(C):
            if i >= len(port_queues): continue
            q = port_queues[i]
            n = q.qsize()
            j = n - 1
            while j >= 0:
                pkt = q.queue[j]
                if not getattr(pkt, "invalid", 0):
                    ts[i] = pkt.ArrivalTimeOnSwitch
                    pos[i] = j
                    ptr[i] = j - 1
                    break
                j -= 1
            if j < 0: ptr[i] = -1

        selected = 0
        while selected < self.k:
            best_i = None
            best_ts = None
            for i in range(C):
                if ts[i] is None: continue
                if (best_ts is None) or (ts[i] > best_ts):
                    best_ts = ts[i]
                    best_i = i

            if best_i is None: break

            # Mark packet as invalid (Virtual Drop)
            q_best = port_queues[best_i]
            idx    = pos[best_i]
            pkt    = q_best.queue[idx]
            pkt.invalid = 1
            self.packet_dropped += 1
            mem_loc.append(1)

            # --- DATA ACQUISITION: UPDATE LOG (PACKET EVICTED) ---
            victim_id = getattr(pkt, "switch_uid", None)
            if victim_id is not None and victim_id in self.packet_history:
                self.packet_history[victim_id][4] = 1
            # -----------------------------------------------------

            # Counter updates
            self.port_qsize[self.largest_index] -= 1
            self.voq_port_qsize[self.largest_index - 1][best_i] -= 1
            self.total_usage -= 1

            # Refresh chosen class
            j = ptr[best_i]
            found = False
            while j >= 0:
                pkt2 = q_best.queue[j]
                if not getattr(pkt2, "invalid", 0):
                    ts[best_i]  = pkt2.ArrivalTimeOnSwitch
                    pos[best_i] = j
                    ptr[best_i] = j - 1
                    found = True
                    break
                j -= 1
            if not found:
                ts[best_i]  = None
                pos[best_i] = None
                ptr[best_i] = -1

            selected += 1

        return mem_loc

    def allct(self, mem, currTimeslot):
        space = sum(mem)
        trk = 0
        for ind,i in enumerate(self.buffer):
            if i[1] != -1:
                i[0].ArrivalTimeOnSwitch = currTimeslot
                self.queues[i[1]][i[0].priority - 1].put(i[0])
                trk +=1
                self.total_usage +=1
                self.port_qsize[i[1]] += 1
                self.setECNFlag(i[0], i[1])
                self.voq_port_qsize[i[1]-1][i[0].priority - 1]+=1
            if trk == space:
                break

    def handleRecvdPacket(self, inPort, packet, currTimeslot):
        """Handle incoming packet and Log State for RF Training"""
        outPort = self.getOutPort(self.addr, packet)

        # --- DATA ACQUISITION LOGIC START ---
        # 1. Update Moving Averages (based on target outPort state)
        current_q = self.port_qsize.get(outPort, 0)
        current_occ = self.total_usage

        self.avg_q_len = (1 - self.alpha) * self.avg_q_len + (self.alpha * current_q)
        self.avg_occ = (1 - self.alpha) * self.avg_occ + (self.alpha * current_occ)

        # 2. Generate Switch-Assigned Unique ID (per arrival event)
        self.arrival_uid += 1
        unique_id = f"{self.addr}_{self.arrival_uid}"
        # Persist on the packet so fetch() can update the correct row later
        packet.switch_uid = unique_id

        # 3. Log Initial State (Default drop = 0)
        # Record the state *before* we make the drop/enqueue decision
        self.packet_history[unique_id] = [
            current_q,
            current_occ,
            round(self.avg_q_len, 4),
            round(self.avg_occ, 4),
            0
        ]
        # --- DATA ACQUISITION LOGIC END ---
        
        if self.total_buffer_size > self.total_usage:
            self.total_usage +=1
            packet.ArrivalTimeOnSwitch = currTimeslot
            self.queues[outPort][packet.priority - 1].put(packet)
            self.port_qsize[outPort] += 1
            self.voq_port_qsize[outPort-1][packet.priority - 1]+=1
            self.setECNFlag(packet, outPort)
        else:
            if self.largest_index is not None and outPort != (self.largest_index):
                self.buffer[inPort-1] = [packet, outPort]
                self.k +=1   
                # print("Initiated LQD")
            else:
                self.packet_dropped+=1
                self.dropped.append((packet.dstAddr,packet.srcAddr,packet.srcPort,packet.dstPort,packet.seqNum)) 
                
                # --- UPDATE LOG: PACKET DIED IMMEDIATELY ---
                self.packet_history[unique_id][4] = 1
                # -------------------------------------------

    def export_training_data(self, filename="training_data.csv"):
        """Call this at the end of the simulation to dump the CSV (space-separated)."""
        print(f"Exporting {len(self.packet_history)} records to {filename}...")
        try:
            with open(filename, "w") as f:
                # Header (space-separated)
                f.write("queueLength sharedOccupancy averageQueueLength averageOccupancy drop\n")

                # Rows
                for _, data in self.packet_history.items():
                    f.write(" ".join(map(str, data)) + "\n")

            print("Export complete.")
        except Exception as e:
            print(f"Failed to export data: {e}")