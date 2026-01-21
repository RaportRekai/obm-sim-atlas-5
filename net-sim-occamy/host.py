# The code is subject to Purdue University copyright policies.
# Do not share, distribute, or post online.

import sys
import math
import queue
from packet import Packet

#updates to make - RTT and RTO and fast retransmit at 3 duplicate acks
#initialization of variables
#make changes in host
#clamp congestion windows
from dataclasses import dataclass
from math import fabs
from collections import defaultdict

class Host:
    """Host class"""

    def __init__(self, addr):
        """Inititalize parameters"""
        self.addr = addr
        self.link = None

        self.flow_track = {}
        self.reordering_count = 0
        self.initial_seq = 0
        self.reordering_cnt = defaultdict(int)        # per-flow cumulative count
        self._reorder_events_outbox = defaultdict(list)

        self.priority = {}  # a dictionary storing state for active flows sourced at this host
                            # key: 3-tuple (dst addr, src port, dst port)
                            # value: [flow size (in number of packets), next seq num to send, last ack num recvd, timer]
        self.sFlows = {}    # a dictionary storing state for active flows sourced at this host
                            # key: 3-tuple (dst addr, src port, dst port)
                            # value: [flow size (in number of packets), next seq num to send, last ack num recvd, timer]

        self.rFlows = {}    # a dictionary storing state for active flows destined to this host
                            # key: 3-tuple (src addr, src port, dst port)
                            # value: [id, flow size (in number of packets), next expected seq num, flow start time, time last pkt sent, dup ack sent]

        self.rrSched = []   # stores the list of active flows sourced at this host
                            # for round-robin scheduling

        self.rrPointer = 0  # points to the flow to be scheduled according to round-robin

        self.cwnd = {}      # a dictionary storing the congestion window for active flows
                            # key: 3-tuple (dst addr, src port, dst port)
                            # value: congestion window

        self.fut_cwnd = {}  # a dictionary storing the instantaneous congestion window calculation
                            # key: 3-tuple (dst addr, src port, dst port)
                            # value: instantaneous congestion window calculation

        self.alpha = {}     # a dictionary storing the alpha value for active flows
                            # key: 3-tuple (dst addr, src port, dst port)
                            # value: alpha values for congestion window calculation

        self.numPktSentInCurrWin = {}   # key: 3-tuple (dst addr, src port, dst port)
                                        # value: number of packets sent in current window

        self.packetLogFile = None

        self.numAckRecvdInCurrWin = {}     # key: 3-tuple (dst addr, src port, dst port)
                                           # value: number of acks received in current window
        
        self.lastDecrease = {}   # key: 3-tuple (dst addr, src port, dst port)
                                # value: bool to time of determine congestion window decrease 
        
        self.retransmissionCnt = {}   # key: 3-tuple (dst addr, src port, dst port)
                                # value: bool to determine number of timeout event occured 
        
        self.targetdelay = {}   # key: 3-tuple (dst addr, src port, dst port)
                                # value: target delay for congestion window calculation


        self.RTO = {}  # in unit of timeslots
        
        self.max_mdf = 0.5

        self.beta = 1

        self.AI = 1

        self.baseTarget   = 5        # timeslot   baseline one-hop target

        self.hopScaling   = 7        # timeslot   extra per additional hop

        self.fs_range     = 60       # timeslot   max cushion for heavy fan-in

        self.fs_min_cwnd  = 1        # pkts cwnd where cushion is full

        self.fs_max_cwnd  = 90      # pkts cwnd where cushion vanishes

        self.lastDecreaseRTT = {}    # This keeps track of RTT at the time of cwnd decrease 

        ################ state for RTO calculation ################
        self.initialized = {}
        self.srtt = {}
        self.rttvar = {}
        self.base_rtt = {}
        self.rto_min = {}
        self.rto_max = {}
        ###########################################################
    
    def _key(self, pkt):
        return (pkt.dstAddr, pkt.srcAddr, pkt.dstPort, pkt.srcPort)



    # reordering counter

    def on_packet(self, pkt) -> bool:
        key = self._key(pkt)
        st = self.flow_track.get(key)
        if st is None:
            st = {"next_expected": self.initial_seq, "ooo_set": set()}
            self.flow_track[key] = st

        seq = pkt.seqNum
        ne  = st["next_expected"]
        oset = st["ooo_set"]

        if seq == ne:
            ne += 1
            while ne in oset:
                oset.remove(ne)
                ne += 1
            st["next_expected"] = ne
            return False

        if seq < ne:
            return False

        # Out-of-order (first time for this early seq)
        if seq not in oset:
            oset.add(seq)
            self.reordering_cnt[key] += 1
            self._reorder_events_outbox[key].append((ne, seq, pkt.priority))  # ← store (next_expected, received)
            return True

        return False





    def update(self, rtt_sample: int, dst:str, sport:int, dport:int):
        # --- constants live here (no args) ---
        alpha = 1/8      # SRTT EWMA weight
        beta  = 1/4      # RTTVAR EWMA weight
        k     = 4.0      # variance multiplier
        min_factor = 2.0 # RTO_min = min_factor * baseRTT
        max_factor = 8.0 # RTO_max = max_factor * baseRTT
        # -------------------------------------
        
        if not self.initialized[(dst,sport,dport)]:
            self.initialized[(dst,sport,dport)] = True
            self.srtt[(dst,sport,dport)] = rtt_sample
            self.rttvar[(dst,sport,dport)] = rtt_sample / 2.0
            self.rto_min[(dst,sport,dport)] = min_factor * rtt_sample
            self.rto_max[(dst,sport,dport)] = max_factor * rtt_sample
        else:
            self.rttvar[(dst,sport,dport)] = (1 - beta) * self.rttvar[(dst,sport,dport)] + beta * abs(self.srtt[(dst,sport,dport)] - rtt_sample)
            self.srtt[(dst,sport,dport)]   = (1 - alpha) * self.srtt[(dst,sport,dport)]   + alpha * rtt_sample
            #print(self.srtt[(dst,sport,dport)])
        rto = self.srtt[(dst,sport,dport)] + k * self.rttvar[(dst,sport,dport)]
        
        rto = max(self.rto_min[(dst,sport,dport)], min(rto, self.rto_max[(dst,sport,dport)]))
        return rto

    def logPacket(self, packet):
        self.packetLogFile.write("src: " + packet.srcAddr + ", dst: " + packet.dstAddr)
        self.packetLogFile.write(", sport: " + str(packet.srcPort) + ", dport: " + str(packet.dstPort))
        self.packetLogFile.write(", seqNum: " + str(packet.seqNum) + ", ackNum: " + str(packet.ackNum))
        self.packetLogFile.write(", ackFlag: " + str(packet.ackFlag) + ", ecnFlag: " + str(packet.ecnFlag))
        self.packetLogFile.write(", route: ")
        self.packetLogFile.write('->'.join('(%s,%s,%s)' % x for x in packet.route))
        self.packetLogFile.write("\n\n")
        self.packetLogFile.flush()


    def runHost(self, currTimeslot, flowLogFile, ackQueues, totalPktSent, totalPktRecvd, totalFlowsFinished):
        """Main loop of host"""

        self.sendPacket(currTimeslot, totalPktSent)  # in each timeslot, send a
                                                     # packet (if any) out on the link

        self.handleRecvdAcks(ackQueues[self.addr], totalFlowsFinished,currTimeslot)  # handle received ACKs

        if self.link:  # in each timeslot, receive a
                       # packet (if any) from the link
                       # and handle it
            packet = self.link.recv(self.addr, currTimeslot)
            if packet:
                if packet.dstAddr != self.addr:
                    sys.stdout.write("Routing Error: Packet with dst " + packet.dstAddr + " was received at " + self.addr + "\n")
                    return
                packet.route.append((packet.node, packet.entryTimeslot, '-'))
                self.logPacket(packet)

                if packet.ackFlag == 0:
                    if (packet.srcAddr,packet.srcPort,packet.dstPort) not in self.rFlows:
                        pass
                    elif packet.seqNum < self.rFlows[(packet.srcAddr,packet.srcPort,packet.dstPort)][2]:
                        pass
                    elif packet.seqNum == self.rFlows[(packet.srcAddr,packet.srcPort,packet.dstPort)][2]:
                        totalPktRecvd[0] += 1
                        if packet.seqNum == self.rFlows[(packet.srcAddr,packet.srcPort,packet.dstPort)][1] - 1: # last packet
                            timeLastPktSent = int(packet.route[0][2])
                            self.rFlows[(packet.srcAddr,packet.srcPort,packet.dstPort)][4] = timeLastPktSent
                        self.handleRecvdPacket(packet, ackQueues)
                        self.rFlows[(packet.srcAddr,packet.srcPort,packet.dstPort)][2] += 1
                        self.rFlows[(packet.srcAddr,packet.srcPort,packet.dstPort)][5] = 0
                        # log finished flow
                        Id = self.rFlows[(packet.srcAddr,packet.srcPort,packet.dstPort)][0]
                        flowsize = self.rFlows[(packet.srcAddr,packet.srcPort,packet.dstPort)][1]
                        starttime = self.rFlows[(packet.srcAddr,packet.srcPort,packet.dstPort)][3]
                        timeLastPktSent = self.rFlows[(packet.srcAddr,packet.srcPort,packet.dstPort)][4]
                        if self.rFlows[(packet.srcAddr,packet.srcPort,packet.dstPort)][2] == flowsize:
                            flowLogFile.write(str(Id) + ", ")
                            flowLogFile.write("src: " + packet.srcAddr + ", dst: " + packet.dstAddr)
                            flowLogFile.write(", sport: " + str(packet.srcPort) + ", dport: " + str(packet.dstPort))
                            flowLogFile.write(", flowsize: " + str(flowsize))
                            flowLogFile.write(", starttime: " + str(starttime))
                            flowLogFile.write(", finishtime: " + str(currTimeslot))
                            fct = currTimeslot - starttime
                            flowLogFile.write(", fct: " + str(fct))
                            recvTput = (flowsize * 1500 * 8)/(fct * 120.0)
                            flowLogFile.write(", recvtput: " + str(round(recvTput,2)) + " Gbps")
                            assert(timeLastPktSent >= starttime)
                            timeToSendFlow = timeLastPktSent - starttime + 1
                            sendTput = (flowsize * 1500 * 8)/(timeToSendFlow * 120.0)
                            flowLogFile.write(", sendtput: " + str(round(sendTput,2)) + " Gbps")
                            flowLogFile.write("\n\n")
                            flowLogFile.flush()
                            # delete finished flow
                            del self.rFlows[(packet.srcAddr,packet.srcPort,packet.dstPort)]
                    elif packet.seqNum > self.rFlows[(packet.srcAddr,packet.srcPort,packet.dstPort)][2]:
                        self.on_packet(packet)    
                    
        return self.reordering_cnt,self._reorder_events_outbox

    def sendPacket(self, currTimeslot, totalPktSent):
        """Send one packet out on the link"""

        
        if len(self.rrSched) > 0:
            dst = "0"
            sport = 0
            dport = 0

            i = 0
            schedFlow = 0
            while i < len(self.rrSched):
                i += 1
                dst, sport, dport = self.rrSched[self.rrPointer]
                if self.numPktSentInCurrWin[(dst,sport,dport)] < self.cwnd[(dst,sport,dport)] and self.sFlows[(dst,sport,dport)][1] < self.sFlows[(dst,sport,dport)][0]:
                    schedFlow = 1
                    if self.numPktSentInCurrWin[(dst,sport,dport)] == 0:
                        self.numAckRecvdInCurrWin[(dst,sport,dport)] = 0
                    break
                elif currTimeslot - self.sFlows[(dst,sport,dport)][3] >= 1000:#self.RTO[(dst,sport,dport)]: # timer expired
                    #breakpoint()
                    self.sFlows[(dst,sport,dport)][1] = self.sFlows[(dst,sport,dport)][2]
                    self.numPktSentInCurrWin[(dst,sport,dport)] = 0
                    self.numAckRecvdInCurrWin[(dst,sport,dport)] = 0
                
                    assert(self.numPktSentInCurrWin[(dst,sport,dport)] >= 0)
                    ########## slashing down cwnd if retransmission cnt exceeds 3 ###########

                    self.retransmissionCnt[(dst,sport,dport)] += 1
                    if self.retransmissionCnt[(dst,sport,dport)] > 3: # timeout event after reaching retransmission count threshold
                        self.cwnd[(dst,sport,dport)] = 1
                        self.retransmissionCnt[(dst,sport,dport)] = 0
                        self.numPktSentInCurrWin[(dst,sport,dport)] = 0
                        self.lastDecrease[(dst,sport,dport)] = currTimeslot
                        #print("3 retransmission event")
                        #breakpoint()
                    else: # timeout event without reaching retransmission count threshold
                        self.cwnd[(dst,sport,dport)] = (1-self.max_mdf)*self.cwnd[(dst,sport,dport)]    
                        self.lastDecrease[(dst,sport,dport)] = currTimeslot 
                        self.cwnd[(dst,sport,dport)] = max(min(self.cwnd[(dst,sport,dport)], self.fs_max_cwnd), self.fs_min_cwnd)
                        #print("slashing cwnd for retransmission")
                        #breakpoint()
                    #print("Timer expired!")
                else:
                    self.rrPointer = (self.rrPointer + 1) % len(self.rrSched)


            if schedFlow == 1:
                # send one packet from the chosen flow
                # seqNum = self.sFlows[(dst, sport, dport)][1]
                # packet = Packet(self.addr, dst, sport, dport, seqNum, 0, 0, 0)
                # packet.priority = self.priority[(dst, sport, dport)]
                # packet.sendTimeslot = currTimeslot
                # self.link.send(packet, self.addr, currTimeslot)

                # self.sFlows[(dst, sport, dport)][1] += 1
                # self.sFlows[(dst, sport, dport)][3] = currTimeslot  # set the timer

                # totalPktSent[0] += 1
                # self.numPktSentInCurrWin[(dst, sport, dport)] += 1

                if self.numPktSentInCurrWin[(dst, sport, dport)] == 0:
                    self.sFlows[(dst, sport, dport)][3] = currTimeslot
                seqNum = self.sFlows[(dst, sport, dport)][1]
                packet = Packet(self.addr, dst, sport, dport, seqNum, 0, 0, 0)
                packet.priority = self.priority[(dst, sport, dport)]
                packet.sendTimeslot = currTimeslot
                self.link.send(packet, self.addr, currTimeslot)

                self.sFlows[(dst, sport, dport)][1] += 1
                #self.sFlows[(dst, sport, dport)][3] = currTimeslot  # set the timer

                totalPktSent[0] += 1
                self.numPktSentInCurrWin[(dst, sport, dport)] += 1

                    # if self.addr == 'h106':
                    #     print(f'sending data from {self.addr}')
                    #     print(f'ackNum = {seqNum}')
                    #     print(f"packet sent at {currTimeslot}")
                    #     print(f"RTO = {self.RTO}")

    def handleRecvdPacket(self, packet, ackQueues):
        """Handle the packet received on the link
           and send an ack packet for the received packet
           by enqueuing the ack packet into the right ackQueue"""
        ackPacket = Packet(packet.dstAddr, packet.srcAddr, packet.dstPort, packet.srcPort, 0, packet.seqNum+1, 1, packet.ecnFlag)
        ackPacket.hops = packet.hops
        ackPacket.sendTimeslot = packet.sendTimeslot
        ackQueues[packet.srcAddr].put(ackPacket)
        self.on_packet(packet)


    def handleRecvdAcks(self, ackQueue, totalFlowsFinished,currTimeslot):
        """Handle the received acks"""
        # the algorithm uses cumulative acks
        while not ackQueue.empty():
            ackPacket = ackQueue.get()
            assert(ackPacket.ackFlag == 1)

            # log recvd ACKs
            self.logPacket(ackPacket)

            dst = ackPacket.srcAddr
            sport = ackPacket.dstPort
            dport = ackPacket.srcPort
            self.RTO[(dst,sport,dport)] = self.update(currTimeslot - ackPacket.sendTimeslot,dst,sport,dport)
            assert(ackPacket.ackNum == self.sFlows[(dst,sport,dport)][2] or ackPacket.ackNum == self.sFlows[(dst,sport,dport)][2]+1)
            if ackPacket.ackNum == self.sFlows[(dst,sport,dport)][2]+1:
                self.sFlows[(dst,sport,dport)][2] += 1
                
                if (dst,sport,dport) in self.rrSched: # the flow exists

                    ################# Target Delay #############################
                    self.targetdelay[(dst,sport,dport)] = ackPacket.hops*self.hopScaling + max(0, min((self.fs_range / ((1/(self.fs_min_cwnd**0.5)) - (1/(self.fs_max_cwnd**0.5)))) * ((1/(self.cwnd[(dst,sport,dport)]**0.5)) - (1/(self.fs_max_cwnd**0.5))), self.fs_range))
                    # print(f"target delay = {self.targetdelay[(dst,sport,dport)]}")
                    # print(f"cwnd = {self.cwnd}")
                    # print(f"delay = {currTimeslot - ackPacket.sendTimeslot}")
                    # print(f"rto = {self.RTO[(dst,sport,dport)]}")
                    # print(f"packet sent in window = {self.numPktSentInCurrWin}")
                    # print(f"ack recvd in window = {self.numAckRecvdInCurrWin}")
                    # print(f"last packet sent at = {self.sFlows[(dst,sport,dport)][3]}")
                    # print(f"current timeslot = {currTimeslot}")


                    ################# SWIFT on receiving ACK ###################
                    self.retransmissionCnt[(dst,sport,dport)] = 0  
                    if self.targetdelay[(dst,sport,dport)] > currTimeslot - ackPacket.sendTimeslot:
                        if self.cwnd[(dst,sport,dport)] >= 1:
                            self.cwnd[(dst,sport,dport)] = self.cwnd[(dst,sport,dport)] + self.AI/self.cwnd[(dst,sport,dport)]
                            self.cwnd[(dst,sport,dport)] = max(min(self.cwnd[(dst,sport,dport)], self.fs_max_cwnd), self.fs_min_cwnd)
                        else:
                            self.cwnd[(dst,sport,dport)] = self.cwnd[(dst,sport,dport)] + self.AI
                            self.cwnd[(dst,sport,dport)] = max(min(self.cwnd[(dst,sport,dport)], self.fs_max_cwnd), self.fs_min_cwnd)
                    else:
                        if currTimeslot - self.lastDecrease[(dst,sport,dport)] >= self.lastDecreaseRTT[(dst,sport,dport)]:
                            #print(f"i have decreased cwnd from = {self.cwnd[(dst,sport,dport)]}")
                            self.cwnd[(dst,sport,dport)] = max(1-self.beta*((currTimeslot-ackPacket.sendTimeslot) - self.targetdelay[(dst,sport,dport)])/(currTimeslot-ackPacket.sendTimeslot), 
                                                               1-self.max_mdf)*self.cwnd[(dst,sport,dport)]
                            self.cwnd[(dst,sport,dport)] = max(min(self.cwnd[(dst,sport,dport)], self.fs_max_cwnd), self.fs_min_cwnd)
                            #print(f"i have decreased cwnd to = {self.cwnd[(dst,sport,dport)]}")
                            self.lastDecreaseRTT [(dst,sport,dport)] = currTimeslot - ackPacket.sendTimeslot  
                            self.lastDecrease[(dst,sport,dport)] = currTimeslot
                    
                    self.numPktSentInCurrWin[(dst,sport,dport)] -= 1
                    #assert(self.numPktSentInCurrWin[(dst,sport,dport)] >= 0)
                    self.numAckRecvdInCurrWin[(dst,sport,dport)] += 1
                    
                    if self.numAckRecvdInCurrWin[(dst,sport,dport)] == self.cwnd[(dst,sport,dport)]: # received all the acks for curr window of sent data
                        # Update the cwnd value below according to DCTCP algorithm 
                        # reset the values at the end
                        self.numAckRecvdInCurrWin[(dst,sport,dport)] = 0

            ###################### adding fast recovery ####################
            elif ackPacket.ackNum == self.sFlows[(dst,sport,dport)][2]: # dup ack
                if currTimeslot - self.lastDecrease[(dst,sport,dport)] >= self.lastDecreaseRTT [(dst,sport,dport)]:
                    self.sFlows[(dst,sport,dport)][1] = self.sFlows[(dst,sport,dport)][2]
                    self.retransmissionCnt[(dst,sport,dport)] = 0
                    self.numPktSentInCurrWin[(dst,sport,dport)] = 0
                    self.numAckRecvdInCurrWin[(dst,sport,dport)] = 0               
                    self.cwnd[(dst,sport,dport)] = (1-self.max_mdf)*self.cwnd[(dst,sport,dport)]
                    self.cwnd[(dst,sport,dport)] = max(min(self.cwnd[(dst,sport,dport)], self.fs_max_cwnd), self.fs_min_cwnd)
                    self.lastDecrease[(dst,sport,dport)] = currTimeslot
                    self.lastDecreaseRTT [(dst,sport,dport)] = currTimeslot - ackPacket.sendTimeslot
                    assert(self.numPktSentInCurrWin[(dst,sport,dport)] >= 0)
                    print("duplicate ack")
                    #breakpoint()
                #print("Dup ack recvd!")
            
            else:
                print("critical error!!!!!!!")
                breakpoint()

            """delete scheduled flow if acks for all packets from the flow have been received"""
            if self.sFlows[(dst,sport,dport)][0] == self.sFlows[(dst,sport,dport)][2]:
                del self.sFlows[(dst,sport,dport)]
                del self.cwnd[(dst,sport,dport)]
                del self.alpha[(dst,sport,dport)]
                del self.numPktSentInCurrWin[(dst,sport,dport)]
                self.rrSched.remove((dst,sport,dport))
                if self.rrPointer >= len(self.rrSched):
                    self.rrPointer = 0
                totalFlowsFinished[0] += 1

        
