# The code is subject to Purdue University copyright policies.
# Do not share, distribute, or post online.

import sys
import os
sys.path.append(os.getcwd())
import glob
from collections import defaultdict
import json
import queue
import numpy as np
from host import Host
from link import Link
from switch import Switch

class Network:
    """Network class maintains all hosts, switches, and links"""

    def __init__(self, netJsonFilepath):
        """Create a new network from the parameters in the file at netJsonFilepath"""

        # parse configuration details
        netJsonFile = open(netJsonFilepath, 'r')
        netJson = json.load(netJsonFile)

        self.num_tor_ports = netJson["num_tor_ports"]
        self.num_agg_ports = netJson["num_agg_ports"]
        self.hosts_per_rack = netJson["hosts_per_rack"]

        # parse and create switches, hosts, and links
        self.switches = self.parseswitches(netJson["switches"])
        self.hosts = self.parseHosts(netJson["hosts"])
        self.links = self.parseLinks(netJson["links"])
        self.reordering_cnt = defaultdict(lambda: defaultdict(int))
        self.reordering_pairs = defaultdict(lambda: defaultdict(list))
        self.drops = self.parseswitches(netJson["switches"])
        self.dropped = {}
        netJsonFile.close()

    def parseswitches(self, switchParams):
        """Parse switches from switchParams dict"""
        switches = {}
        for addr in switchParams:
            switches[addr] = Switch(addr, self.num_tor_ports, self.num_agg_ports, self.hosts_per_rack)
        return switches


    def parseHosts(self, hostParams):
        """Parse hosts from hostParams dict"""
        hosts = {}
        for addr in hostParams:
            hosts[addr] = Host(addr)
        return hosts


    def parseLinks(self, linkParams):
        """Parse links from linkParams dict"""
        links = {}
        for addr1, addr2, p1, p2 in linkParams:
            link = Link(addr1, addr2)
            links[(addr1,addr2)] = (p1, p2, link)
        return links


    def addLinks(self):
        """Add links to hosts and switches"""
        for addr1, addr2 in self.links:
            p1, p2, link = self.links[(addr1, addr2)]
            if addr1 in self.hosts:
                self.hosts[addr1].link = link
                self.hosts[addr1].packetLogFile = open("logs/"+addr1+"-recvd-packets.txt", "a")
            if addr2 in self.hosts:
                self.hosts[addr2].link = link
                self.hosts[addr2].packetLogFile = open("logs/"+addr2+"-recvd-packets.txt", "a")
            if addr1 in self.switches:
                self.switches[addr1].links[p1] = link
                if addr1[0] == 't': 
                    self.switches[addr1].queues[p1] = [queue.Queue() for _ in range(self.num_tor_ports)]
                elif addr1[0] == 'a':
                    self.switches[addr1].queues[p1] = [queue.Queue() for _ in range(self.num_agg_ports)]
                self.switches[addr1].voq_rr[p1] = 0
                self.switches[addr1].port_qsize[p1] = 0 
            if addr2 in self.switches:
                self.switches[addr2].links[p2] = link
                if addr2[0] == 't': 
                    self.switches[addr2].queues[p2] = [queue.Queue() for _ in range(self.num_tor_ports)]
                elif addr2[0] == 'a':
                    self.switches[addr2].queues[p2] = [queue.Queue() for _ in range(self.num_agg_ports)]
                self.switches[addr2].voq_rr[p2] = 0
                self.switches[addr2].port_qsize[p2] = 0


    def run(self, flowtrace, endTimeslot, flowLogFile):
        """Run the network"""
        self.addLinks()

        ackQueues = {}
        for h in self.hosts:
            ackQueues[h] = queue.Queue()

        currTimeslot = 0

        totalPktSent = [0]
        totalPktRecvd = [0]
        totalFlowsFinished = [0]

        f = open(flowtrace, "r")
        line = f.readline()
        line = f.readline()
        tokens = line.split(',')
        if len(tokens) != 7:
            sys.stdout.write("Wrong flowtrace file format.\n")
            return
        Id = int(tokens[0])
        src = tokens[1]
        dst = tokens[2]
        sport = int(tokens[3])
        dport = int(tokens[4])
        flowsize = int(tokens[5])
        startTimeslot = int(tokens[6].strip())
        if float(logname) == 0.6:
            cwindw = 20
            breakpoint()
        else:
            cwindw = 50
        eof = False

        while currTimeslot < endTimeslot:
            if currTimeslot % 100 == 0:
                sys.stdout.write("current timeslot: " + str(currTimeslot) + " total packets sent: " + str(totalPktSent[0]) + " total packets received: " + str(totalPktRecvd[0]) + " total flows finished: " + str(totalFlowsFinished[0]) + "\n")

            while not eof and currTimeslot == startTimeslot:
                self.hosts[src].sFlows[(dst,sport,dport)] = [flowsize, 0, 0, 0]
                if flowsize < 100:
                    self.hosts[src].priority[(dst,sport,dport)] = 1 # 1,2,3
                elif flowsize > 1000:
                    self.hosts[src].priority[(dst,sport,dport)] = 3
                else:
                    self.hosts[src].priority[(dst,sport,dport)] = 2
                self.hosts[dst].rFlows[(src,sport,dport)] = [Id, flowsize, 0, startTimeslot, 0, 0]
                self.hosts[src].rrSched.append((dst,sport,dport))
                self.hosts[src].retransmissionCnt[(dst,sport,dport)] = 0
                self.hosts[src].lastDecrease[(dst,sport,dport)] = 0
                self.hosts[src].cwnd[(dst,sport,dport)] = cwindw
                self.hosts[src].alpha[(dst,sport,dport)] = 0
                self.hosts[src].targetdelay[(dst,sport,dport)] = 0
                self.hosts[src].numPktSentInCurrWin[(dst,sport,dport)] = 0
                self.hosts[src].lastDecreaseRTT[(dst,sport,dport)] = 0
                self.hosts[src].initialized[(dst,sport,dport)] = False
                self.hosts[src].srtt[(dst,sport,dport)] = 0.0
                self.hosts[src].rttvar[(dst,sport,dport)] = 0.0
                self.hosts[src].base_rtt[(dst,sport,dport)] = 0.0
                self.hosts[src].rto_min[(dst,sport,dport)] = 0.0
                self.hosts[src].rto_max[(dst,sport,dport)] = 0.0
                self.hosts[src].RTO[(dst,sport,dport)] = 1000

                line = f.readline()
                if not line:
                    eof = True
                    break
                tokens = line.split(',')
                if len(tokens) != 7:
                    sys.stdout.write("Wrong flowtrace file format.\n")
                    return
                Id = int(tokens[0])
                src = tokens[1]
                dst = tokens[2]
                sport = int(tokens[3])
                dport = int(tokens[4])
                flowsize = int(tokens[5])
                startTimeslot = int(tokens[6].strip())

            for h in self.hosts:
                counts_delta, events = self.hosts[h].runHost(currTimeslot, flowLogFile,
                                                 ackQueues, totalPktSent,
                                                 totalPktRecvd, totalFlowsFinished)
                # if you want a flat per-host list of all (next_expected, received) events:
                self.reordering_pairs[h] = {fk: list(v) for fk, v in events.items()}
            for s in self.switches:
                self.drops[s],counts_delta = self.switches[s].runSwitch(currTimeslot)
                for dstAddr, srcAddr, srcPort, dstPort, seqNum in counts_delta:
                    key = (dstAddr, srcAddr, srcPort, dstPort)
                    self.dropped.setdefault(key, []).append(seqNum)

            currTimeslot += 1

            # break if finished reading entire flowtrace file and all flows have finished
            count = 0
            for h in self.hosts:
                if len(self.hosts[h].rFlows) == 0:
                    count += 1
            if eof and count == len(self.hosts):
                sys.stdout.write("current timeslot: " + str(currTimeslot) + " total packets sent: " + str(totalPktSent[0]) + " total packets received: " + str(totalPktRecvd[0]) + " total flows finished: " + str(totalFlowsFinished[0]) + "\n")
                sys.stdout.write("Ending simulation as all flows have finished.\n")
                nwTput = (totalPktRecvd[0] * 1500 * 8.0) / (currTimeslot * 120.0)  # Assuming 100G link and 1500B packets
                sys.stdout.write("Network throughput (assuming 100G link and 1500B pkt): " + str(round(nwTput,3)) + "Gbps\n")
                with open("reordering_obm_per_flow.txt", "a", encoding="utf-8") as f:
                    for h, events_by_flow in self.reordering_pairs.items():
                        for (dst, src, dport, sport), pairs in events_by_flow.items():
                            for item in pairs:
                                if len(item) == 3:
                                    ne, seq, pri = item
                                else:  # len == 3 → (fk, ne, seq)
                                    _, ne, seq = item
                                f.write(f"{h},{src},{dst},{sport},{dport},{ne},{seq},{pri}\n")
                    f.write("@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@\n")
                with open("drop_events_obm.txt", "w", encoding="utf-8") as f:
                    for (dst, src, sport, dport), seqs in self.dropped.items():
                        f.write(f"{src},{dst},{sport},{dport}," + ",".join(map(str, seqs)) + "\n")
                with open("reordering_obm.txt", "a", encoding="utf-8") as f:
                    f.write(f"drop count = {sum(self.drops.values())}\n")
                break

        if currTimeslot >= endTimeslot:
            sys.stdout.write("current timeslot: " + str(currTimeslot) + " total packets sent: " + str(totalPktSent[0]) + " total packets received: " + str(totalPktRecvd[0]) + " total flows finished: " + str(totalFlowsFinished[0]) + "\n")
            sys.stdout.write("Ending simulation as end timeslot reached.\n")
            nwTput = (totalPktRecvd[0] * 1500 * 8.0) / (currTimeslot * 120.0)  # Assuming 100G link and 1500B packets
            sys.stdout.write("Network throughput (assuming 100G link and 1500B pkt): " + str(round(nwTput,3)) + "Gbps\n")
            with open("reordering_obm_per_flow.txt", "a", encoding="utf-8") as f:
                for h, events_by_flow in self.reordering_pairs.items():
                    for (dst, src, dport, sport), pairs in events_by_flow.items():
                        for item in pairs:
                            if len(item) == 3:
                                ne, seq, pri = item
                            else:  # len == 3 → (fk, ne, seq)
                                _, ne, seq = item
                            f.write(f"{h},{src},{dst},{sport},{dport},{ne},{seq},{pri}\n")
                f.write("@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@\n")
            with open("drop_events_obm.txt", "w", encoding="utf-8") as f:
                    for (dst, src, sport, dport), seqs in self.dropped.items():
                        f.write(f"{src},{dst},{sport},{dport}," + ",".join(map(str, seqs)) + "\n")
            with open("reordering_obm.txt", "a", encoding="utf-8") as f:
                    f.write(f"drop count = {sum(self.drops.values())}\n")
        for h in self.hosts:
            self.hosts[h].packetLogFile.close()

        f.close()
        return


def main():
    """Main function parses command line arguments and runs the network"""
    global logname
    if len(sys.argv) < 4:
        sys.stdout.write("Usage: python3 network.py [networkSimulationFile.json] [flowtrace.dat] [endtimeslot]\n")
        return
    netCfgFilepath = sys.argv[1]
    flowtrace = sys.argv[2]
    logname = sys.argv[3]
    endTimeslot = int(sys.argv[4])
    net = Network(netCfgFilepath)
    protected = set(glob.glob(os.path.join('logs', 'recvd-flows-*.txt')))
    files = glob.glob('logs/*')
    for f in files: 
        if f not in protected:
            os.remove(f)
    flowLogFile = open(f"logs/recvd-flows-{logname}.txt", "a")
    net.run(flowtrace, endTimeslot, flowLogFile)
    flowLogFile.close()
    return


if __name__ == "__main__":
    main()

