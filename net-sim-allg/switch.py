# The code is subject to Purdue University copyright policies.
# Do not share, distribute, or post online.

# import sys
# import queue
# import hashlib
# from link import Link
# import math
# import copy

# class Switch():
#     """Switch class"""

#     def __init__(self, addr, num_tor_ports, num_agg_ports, hosts_per_rack):
#         """Initialize parameters"""
#         self.addr = addr  # address of switch
#         self.links = {}   # links indexed by port, i.e., {port:link, ......, port:link}
#         self.queues = {}  # list of virtual output queues (of type queue.Queue) per port
#                           # indexed by port, i.e., {port:[queue], ......, port:[queue]}
#                           # each virtual output queue is a FIFO queue of infinite size
#         self.voq_rr = {}  # stores the VOQ per port to be serviced next
#         self.per_port_max_qsize = 5  # in terms of number of 1500B packets
#                                        # threshold for ECN marking (in terms of number of packets)
#         self.flag = 0
#         self.num_tor_ports = num_tor_ports
#         self.num_agg_ports = num_agg_ports
#         self.hosts_per_rack = hosts_per_rack
#         self.tor_buff_size = self.per_port_max_qsize * self.num_tor_ports # in terms of number of packets
#         self.agg_buff_size = self.per_port_max_qsize * self.num_agg_ports # in terms of number of packets
#         self.packet_dropped = 0
#         self.port_qsize = {}  # number of packets queued per port
#         self.priority_classes = 3

        
#         if self.addr[0] == 't':
#             self.K = 4
#             self.ports = num_tor_ports
#             self.total_buffer_size = self.per_port_max_qsize*num_tor_ports
#             self.N = 1 if num_tor_ports < 1 else 2 ** ((num_tor_ports - 1).bit_length())
#             self.voq_port_qsize = [[0 for i in range(self.priority_classes)] for _ in range(self.N)]
#             print(num_tor_ports)
#         elif self.addr[0] == 'a':
#             self.K = 4
#             self.ports = num_agg_ports
#             self.total_buffer_size = self.per_port_max_qsize*num_agg_ports
#             self.N = 1 if num_agg_ports < 1 else 2 ** ((num_agg_ports - 1).bit_length())
#             self.voq_port_qsize = [[0 for i in range(self.priority_classes)] for _ in range (self.N)]
#             print(num_agg_ports)
            

#         #########################################################################################################
#         self.total_usage = 0 
#         self.final_add = [0 for i in range(self.N)]
#         self.T = self.total_buffer_size
#         self.sent = 0
#         self.alpha = 2
#         self.t = 0
#         self.k = 0
#         self.t_track = 0
#         self.buffer = [[-1,-1] for i in range(self.N)]
#         self.priority_packet_count = [0,0,0]
#         self.dropped = []

#     def runSwitch(self, currTimeslot):
#         """Main loop of switch"""
#         self.t+=1
#         self.l_uni = []
#         self.dropped = []
#         for port in self.links.keys():  # in each timeslot, send a packet
#                                         # at the head of a VOQ at each port.
#                                         # VOQs at each port are scheduled in
#                                         # round robin manner
#             flag_1 = 0
#             for i in range(1,2):
#                 # print(self.queues)
#                 # breakpoint()
#                 if not self.queues[port][i].empty():
#                     for j in range(0,self.queues[port][i].qsize()):
#                         packet = self.queues[port][i].get_nowait()
#                         if packet.invalid == 0:
#                             packet.hops +=1
#                             self.links[port].send(packet, self.addr, currTimeslot)
                            
#                             # print(f"sending packet from {i} when other prioritites have length = {self.voq_port_qsize[port-1]}")
#                             # if i == 0:
#                             #     breakpoint()
#                             self.port_qsize[port] -= 1
#                             self.sent+=1
#                             self.total_usage-=1 
#                             self.voq_port_qsize[port-1][i]-=1
#                             flag_1 = 1
#                             assert(self.port_qsize[port] >= 0)
#                             break
#                         else:
#                             self.dropped.append((packet.dstAddr,packet.srcAddr,packet.srcPort,packet.dstPort,packet.seqNum))

#                     if flag_1:
#                         break

#                 else:
#                     continue
#         self.k = 0
        
#         self.largest_index = max(self.port_qsize, key=self.port_qsize.get)
#         #print(f"The largest q is {self.largest_index}")
#         #print(f"port qsize = {self.port_qsize}")
#         for port in self.links.keys():  # in each timeslot, receive a
#                                         # pa cket (if any) on each input
#                                         # port and handle it
#             packet = self.links[port].recv(self.addr, currTimeslot)
#             if packet:
#                 self.handleRecvdPacket(port, packet, currTimeslot)
        
#         for b in self.buffer:
#             if b[1] != -1:
#                 self.k+=1
#         # for different priority classes coming into picture the conditions for priority encoder check becomes a little different
#         if self.k>0:
#             self.lvoq = self.priority_encoder(self.largest_index,self.k)
#             #print(f"self.lvoq = {self.lvoq}")
#             #breakpoint()
#             mem = self.fetch()
#             self.allct(mem)
        
#         #if self.t > self.t_track:
#         #    self.t_track+=200
#         #    if self.addr == 't9':
#         #        print(f"switch {self.addr}, usage = {self.total_usage}, total = {self.total_buffer_size}")
#         return self.packet_dropped,self.dropped

#     def setECNFlag(self, packet, outPort):
#         if self.port_qsize[outPort] > self.K:
#             packet.ecnFlag = 1
#             # if packet.srcAddr == 'h85' and packet.dstPort == 943:
#             #     print(f"switch marking congestion - {self.addr}")
#                 #breakpoint()


#     def ecmp(self, packet):
#         flowid = packet.srcAddr + packet.dstAddr + str(packet.srcPort) + str(packet.dstPort)
#         outPort = int(hashlib.sha256(flowid.encode('utf-8')).hexdigest(), 16) % (self.num_tor_ports - self.hosts_per_rack) + (self.hosts_per_rack + 1)
#         return outPort


#     def getOutPort(self, switchId, packet):
#         dst_id = int(packet.dstAddr[1:])  # e.g. "h9" -> 9

#         # ----- Top-of-Rack switches -----
#         if switchId[0] == 't':
#             # rack index from ToR name: "t1" -> 1, "t2" -> 2, ...
#             rack_id = int(switchId[1:])

#             # host ID range owned by this rack
#             rack_start = (rack_id - 1) * self.hosts_per_rack + 1
#             rack_end   = rack_id * self.hosts_per_rack

#             # if destination host is in this rack, send down to host port
#             if rack_start <= dst_id <= rack_end:
#                 # map h[rack_start..rack_end] -> ports 1..hosts_per_rack
#                 return dst_id - (rack_start - 1)
#             else:
#                 # otherwise send up toward agg using ECMP
#                 return self.ecmp(packet)

#         # ----- Aggregation / spine switches -----
#         elif switchId[0] == 'a':
#             # which rack owns this host? (1-based)
#             rack_index = (dst_id - 1) // self.hosts_per_rack + 1
#             # assume ports 1..num_racks connect to t1..t<num_racks>
#             return rack_index

# ######################################################################## Additional ######################################################################################

#     def find_index_of_largest(self):
#         elements = []
#         queue_instance = self.port_qsize
        
#         # Dequeue all elements and keep them in a list
#         while not queue_instance.empty():
#             elements.append(queue_instance.get())
        
#         # Find the index of the largest element
#         index_of_largest = elements.index(max(elements))
        
#         # Restore the elements back to the queue
#         for item in elements:
#             queue_instance.put(item)
        
#         return index_of_largest

#     def priority_encoder(self,longest_ind,k):
#         for p_index in range(self.priority_classes):
            
#             if self.voq_port_qsize[longest_ind-1][self.priority_classes-1-p_index]>0:
#                 # if self.voq_port_qsize[longest_ind-1][self.priority_classes-1-p_index] < k:
#                 #     breakpoint()
#                 return self.priority_classes-1-p_index
            
#         for p_index in range(self.priority_classes):
            
#             if self.voq_port_qsize[longest_ind-1][self.priority_classes-1-p_index]>=1:
#                 #print(f"got {k} locations")
#                 #breakpoint()
#                 return self.priority_classes-1-p_index
            
#         breakpoint()
#         return self.priority_classes-1
    
#     def fetch(self):
#         mem_loc = []
#         target_queue = self.queues[self.largest_index][self.lvoq]
        
#         # if self.flag == 1:  
#         #     print(f"target queue = {target_queue.qsize()}") # actual q size
#         #     print(f"maxsize queue = {target_queue.maxsize}")
#         #print(k)
#         for h in range(self.k):
#             if not target_queue.empty():  # Ensure the queue is not empty
#                 #print(f"Have removed an element from voq [{self.largest_index-1},{self.lvoq}]")
#                 #print(f"Number of packets available: {self.voq_port_qsize[self.largest_index-1][self.lvoq]}")
                
#                 # Access the last element directly
#                 #print(f"In contrast we have only {target_queue.qsize()} packets")
#                 #last_element = target_queue.queue.pop()  # Access the last element
#                 #last_element.invalid = 1  # Mark it as invalid (or any custom modification)
#                 c = 0
#                 while target_queue.queue[target_queue.qsize()-c-1].invalid ==1 and c!=target_queue.qsize():
#                     c+=1
#                 if c==target_queue.qsize(): 
#                     self.flag = 1
#                     break
#                 target_queue.queue[target_queue.qsize()-c-1].invalid = 1
#                 mem_loc.append(1)  # Log the memory location (example)
#                 #self.packet_dropped+=1 
#                 # Optionally remove the last element
#                 #target_queue.queue.pop()  # Remove the last element if needed
#                 self.port_qsize[self.largest_index] -= 1
#                 self.voq_port_qsize[self.largest_index-1][self.lvoq] -= 1
#                 self.total_usage -= 1 
                
#             else:
#                 #print(f"Queue [{self.largest_index}][{ind}] is empty.")
#                 break  # Stop if the queue becomes empty
        
#         return mem_loc
    
#     def allct(self,mem):
#         space = sum(mem)
#         trk = 0
#         for ind,i in enumerate(self.buffer):
#             if i[1] != -1:
#                 self.queues[i[1]][i[0].priority-1].put(i[0])
#                 trk +=1
#                 self.total_usage +=1
#                 self.port_qsize[i[1]] += 1
#                 #self.setECNFlag(i[0], i[1])
#                 self.voq_port_qsize[i[1]-1][i[0].priority-1]+=1
#                 self.buffer[ind] = [-1,-1]
#             if trk == space:
#                 break
        
        

# ###############################################################################################################################################################

#     def handleRecvdPacket(self, inPort, packet, arrivalTime):
#         """Handle the packet received on the specified input port 'inPort'.
#            arrivalTime is the timeslot in which the packet was received"""
#         outPort = self.getOutPort(self.addr, packet)  # output port the packet needs to be sent out on
#         print(f"Packet received at switch {self.addr} on port {inPort} destined for port {outPort} at time {arrivalTime} with priority {packet.priority}")
#         #breakpoint()
# ################################################################################ BIT MAPPER ########################################################################################
#         if self.total_buffer_size > self.total_usage and self.buffer[inPort-1][1] == -1:

#             self.total_usage +=1
#             self.queues[outPort][packet.priority-1].put(packet)
#             self.port_qsize[outPort] += 1
#             self.voq_port_qsize[outPort-1][packet.priority-1]+=1
#             #self.setECNFlag(packet, outPort)
#             #print(f"voq length = {[self.voq_port_qsize[c][0] for c in range(0,self.N)]}")
#             # if packet.dstAddr == 'h13' and packet.srcPort == 943 and packet.dstPort == 943:
#             #     print(arrivalTime)
#             #     breakpoint()
#             #print(f"Packet placed = {self.addr} at {outPort-1} {inPort-1} at time {self.t}")
#             #print(f"port qsize = {self.port_qsize}")
#         #print("Packets scheduled via final add")
#         elif self.buffer[inPort-1][1] != -1 and self.total_buffer_size > self.total_usage:
#             self.total_usage +=1
#             self.queues[self.buffer[inPort-1][1]][self.buffer[inPort-1][0].priority-1].put(self.buffer[inPort-1][0])
#             self.port_qsize[self.buffer[inPort-1][1]] += 1
#             self.voq_port_qsize[self.buffer[inPort-1][1]-1][self.buffer[inPort-1][0].priority-1]+=1
#             self.buffer[inPort-1] = [-1,-1]
#             #self.setECNFlag(packet, outPort)

#         elif self.buffer[inPort-1][1] == -1:
#             enter = 0
#             if outPort == self.largest_index:
#                 for p in range(3,packet.priority,-1):
#                     if self.voq_port_qsize[outPort-1][p - 1]>0:
#                         enter = 1
#                         #breakpoint()
                    
#             if outPort != (self.largest_index) or (enter == 1):
#                 self.buffer[inPort-1] = [packet,outPort]
#                 self.packet_dropped+=1
                 
#                 # if packet.priority == 1:  
#                 #     #breakpoint()
#                 print("Initiated LQD")
#             else:
#                 self.packet_dropped+=1 
#                 self.dropped.append((packet.dstAddr,packet.srcAddr,packet.srcPort,packet.dstPort,packet.seqNum)) 
#                 # if packet.priority == 1:  
#                 #     breakpoint()

        
                
            
            
####################################################################################################################################################################################
                












# The code is subject to Purdue University copyright policies.
# Do not share, distribute, or post online.

import sys
import queue
import hashlib
from link import Link
import math
import copy
from packet import Packet


class Switch():
    """Switch class"""

    def __init__(self, addr, num_tor_ports, num_agg_ports, hosts_per_rack):
        """Initialize parameters"""
        self.addr = addr  # address of switch
        self.links = {}   # links indexed by port, i.e., {port:link, ......, port:link}
        self.queues = {}  # list of virtual output queues (of type queue.Queue) per port
                          # indexed by port, i.e., {port:[queue], ......, port:[queue]}
                          # each virtual output queue is a FIFO queue of infinite size
        self.voq_rr = {}  # stores the VOQ per port to be serviced next
        self.per_port_max_qsize = 5  # in terms of number of size in Bytes
        self.K = 4                   # threshold for ECN marking (in terms of number of packets)

        self.num_tor_ports = num_tor_ports
        self.num_agg_ports = num_agg_ports
        self.hosts_per_rack = hosts_per_rack
        self.tor_buff_size = self.per_port_max_qsize * self.num_tor_ports # in terms of number of packets
        self.agg_buff_size = self.per_port_max_qsize * self.num_agg_ports # in terms of number of packets
        self.packet_dropped = 0
        self.port_qsize = {}  # number of packets queued per port
        self.priority_classes = 3

        
        if self.addr[0] == 't':
            self.ports = num_tor_ports
            self.total_buffer_size = self.per_port_max_qsize*num_tor_ports
            self.N = self.ports
            self.voq_port_qsize = [[0 for i in range(self.priority_classes)] for _ in range(self.N)]
            print(num_tor_ports)
        elif self.addr[0] == 'a':
            self.ports = num_agg_ports
            self.total_buffer_size = self.per_port_max_qsize*num_agg_ports
            self.N = self.ports
            self.voq_port_qsize = [[0 for i in range(self.priority_classes)] for _ in range (self.N)]
            print(num_agg_ports)
            

        #########################################################################################################
        self.total_usage = 0 
        self.final_add = [0 for i in range(self.N)]
        self.T = [self.total_buffer_size/(self.ports*self.priority_classes) for i in range(self.priority_classes)]
        self.sent = 0
        self.alpha = [4,2,1]#[12,10,8]#[10,8,6]#[0.5,0.4,0.2]#[8,2,1]
        self.t = 0
        self.track = 0

    def packets_dropped(self):
        return(self.packet_dropped)
    
    def runSwitch(self, currTimeslot):
        """Main loop of switch"""
        self.t+=1
        
        for port in self.links.keys():  # in each timeslot, send a packet
                                        # at the head of a VOQ at each port.
                                        # VOQs at each port are scheduled in
                                        # round robin manner
            flag_1 = 0
            for i in range(self.priority_classes):
                # print(port,i)
                # print(self.addr)
                # try:
                #     print(self.queues[port][i])
                # except:
                #     breakpoint()
                if not self.queues[port][i].empty():
                    for j in range(0,self.queues[port][i].qsize()):
                        packet = self.queues[port][i].get_nowait()
                        if packet.invalid == 0:
                            packet.hops+=1
                            self.links[port].send(packet, self.addr, currTimeslot)
                            # print(f"sending packet from {i} when other prioritites have length = {self.voq_port_qsize[port-1]}")
                            # if i == 0:
                            #     breakpoint()
                            
                            self.port_qsize[port] -= 1
                            self.sent+=1
                            self.total_usage-=1 
                            self.voq_port_qsize[port-1][i]-=1
                            flag_1 = 1
                            assert(self.port_qsize[port] >= 0)
                            break

                    if flag_1:
                        break

                else:
                    continue


        for port in self.links.keys():  # in each timeslot, receive a
                                        # pa cket (if any) on each input
                                        # port and handle it
            packet = self.links[port].recv(self.addr, currTimeslot)
            if packet:
                self.handleRecvdPacket(packet, currTimeslot)
            else:
                self.final_add[port-1] = 0
        
        #if self.t > self.track:
        #    self.track +=200
        #    if self.addr == 't9':
        #            print(f"usage = {self.total_usage}/{self.total_buffer_size}")
        #            print(f"dropped = {self.packet_dropped}")
        #            #print(f"nqa = {self.nqa}")
        #            print(f"occupancy = {self.port_qsize}")
        #            print(f"threshold = {self.T}")
        return self.packet_dropped
        
    def setECNFlag(self, packet, outPort):
        if self.port_qsize[outPort] > self.K:
            packet.ecnFlag = 1


    def ecmp(self, packet):
        flowid = packet.srcAddr + packet.dstAddr + str(packet.srcPort) + str(packet.dstPort)
        outPort = int(hashlib.sha256(flowid.encode('utf-8')).hexdigest(), 16) % (self.num_tor_ports - self.hosts_per_rack) + (self.hosts_per_rack + 1)
        return outPort


    def getOutPort(self, switchId, packet):
        dst_id = int(packet.dstAddr[1:])  # e.g. "h9" -> 9

        # ----- Top-of-Rack switches -----
        if switchId[0] == 't':
            # rack index from ToR name: "t1" -> 1, "t2" -> 2, ...
            rack_id = int(switchId[1:])

            # host ID range owned by this rack
            rack_start = (rack_id - 1) * self.hosts_per_rack + 1
            rack_end   = rack_id * self.hosts_per_rack

            # if destination host is in this rack, send down to host port
            if rack_start <= dst_id <= rack_end:
                # map h[rack_start..rack_end] -> ports 1..hosts_per_rack
                return dst_id - (rack_start - 1)
            else:
                # otherwise send up toward agg using ECMP
                return self.ecmp(packet)

        # ----- Aggregation / spine switches -----
        elif switchId[0] == 'a':
            # which rack owns this host? (1-based)
            rack_index = (dst_id - 1) // self.hosts_per_rack + 1
            # assume ports 1..num_racks connect to t1..t<num_racks>
            return rack_index
######################################################################## Additional ######################################################################################

    def threshold_calculate(self):
        
        # self.nqa = [0]*self.N
        # tot_al = 0
        # for n1 in range(0,self.ports):
        #     for n2 in range(0,self.priority_classes):
        #         if self.voq_port_qsize[n1][n2]>0.9*self.T[n2]:
        #             tot_al += self.alpha[n2]
        for n2 in range(self.priority_classes):
            self.T[n2]= self.alpha[n2]*(self.total_buffer_size - self.total_usage)

###############################################################################################################################################################

    def handleRecvdPacket(self, packet, arrivalTime):
        # --- Broadcast replication only at destination ToR ---
        if (self.addr[0] == 't'
            and packet.broadcast == self.addr
            and getattr(packet, "ackFlag", 0) == 0):
            #print(f"Broadcasting {packet.seqNum} from tor {self.addr}")
            rack_id = int(self.addr[1:])
            pr_idx = packet.priority - 1  # priority 1..3 -> index 0..2

            for host_port in range(1, self.hosts_per_rack + 1):
                # Optional: set dstAddr to the actual host for cleaner logs
                dst_host_id = (rack_id - 1) * self.hosts_per_rack + host_port
                dst_host = f"h{dst_host_id}"

                pkt_copy = Packet(
                    packet.srcAddr, dst_host,
                    packet.srcPort, packet.dstPort,
                    packet.seqNum, packet.ackNum,
                    packet.ackFlag, packet.ecnFlag,
                    packet.dstAddr
                )

                # carry metadata needed by host-side RTT/SWIFT logic + tracing
                pkt_copy.priority = packet.priority
                pkt_copy.hops = getattr(packet, "hops", 0)
                pkt_copy.sendTimeslot = getattr(packet, "sendTimeslot", 0)
                pkt_copy.route = list(getattr(packet, "route", []))
                pkt_copy.invalid = getattr(packet, "invalid", 0)

                # Admission: same logic as your existing DT admission, per copy
                if (self.total_buffer_size > self.total_usage and
                    self.voq_port_qsize[host_port - 1][pr_idx] < self.T[pr_idx]):

                    self.total_usage += 1
                    self.queues[host_port][pr_idx].put(pkt_copy)
                    self.port_qsize[host_port] += 1
                    self.voq_port_qsize[host_port - 1][pr_idx] += 1
                    self.setECNFlag(pkt_copy, host_port)
                    #print(f"I have admitted broadcast packet to the queue of {dst_host_id}")
                else:
                    self.packet_dropped += 1

            self.threshold_calculate()
            return  # IMPORTANT: stop here; don't forward the original onward

        # --- Normal unicast forwarding path (existing logic) ---
        outPort = self.getOutPort(self.addr, packet)
        if outPort is None:
            # defensive: should only happen for broadcast-to-self, which is handled above
            return

        # existing admission logic continues...
        inPort = packet.priority
        if self.total_buffer_size > self.total_usage:
            if self.voq_port_qsize[outPort-1][inPort-1] < self.T[inPort-1]:
                self.total_usage +=1
                self.queues[outPort][inPort-1].put(packet)
                self.port_qsize[outPort] += 1
                self.voq_port_qsize[outPort-1][inPort-1]+=1
                self.setECNFlag(packet, outPort)
            else:
                self.packet_dropped += 1
        else:
            self.packet_dropped += 1

        self.threshold_calculate()

            
                    
                
            
####################################################################################################################################################################################
                


