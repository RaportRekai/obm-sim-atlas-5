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

        netJsonFile = open(netJsonFilepath, 'r')
        netJson = json.load(netJsonFile)

        self.num_tor_ports = netJson["num_tor_ports"]
        self.num_agg_ports = netJson["num_agg_ports"]
        self.hosts_per_rack = netJson["hosts_per_rack"]

        self.flows_complete = {}
        self.switches = self.parseswitches(netJson["switches"])
        self.hosts = self.parseHosts(netJson["hosts"])
        self.links = self.parseLinks(netJson["links"])

        self.reordering_cnt = defaultdict(lambda: defaultdict(int))
        self.reordering_pairs = defaultdict(lambda: defaultdict(list))

        self.drops = self.parseswitches(netJson["switches"])
        self.dropped = {}

        netJsonFile.close()

    def parseswitches(self, switchParams):
        switches = {}
        for addr in switchParams:
            switches[addr] = Switch(addr, self.num_tor_ports, self.num_agg_ports, self.hosts_per_rack)
        return switches

    def parseHosts(self, hostParams):
        hosts = {}
        for addr in hostParams:
            self.flows_complete[addr] = 0
            hosts[addr] = Host(addr)
        return hosts

    def parseLinks(self, linkParams):
        links = {}
        for addr1, addr2, p1, p2 in linkParams:
            link = Link(addr1, addr2)
            links[(addr1, addr2)] = (p1, p2, link)
        return links

    def addLinks(self):
        for addr1, addr2 in self.links:
            p1, p2, link = self.links[(addr1, addr2)]

            if addr1 in self.hosts:
                self.hosts[addr1].link = link
                self.hosts[addr1].packetLogFile = open("logs/" + addr1 + "-recvd-packets.txt", "a")
            if addr2 in self.hosts:
                self.hosts[addr2].link = link
                self.hosts[addr2].packetLogFile = open("logs/" + addr2 + "-recvd-packets.txt", "a")

            if addr1 in self.switches:
                self.switches[addr1].links[p1] = link
                if addr1[0] == 't':
                    self.switches[addr1].queues[p1] = [queue.Queue() for _ in range(self.num_tor_ports)]
                elif addr1[0] == 'a':
                    self.switches[addr1].queues[p1] = [queue.Queue() for _ in range(3)]
                self.switches[addr1].voq_rr[p1] = 0
                self.switches[addr1].port_qsize[p1] = 0

            if addr2 in self.switches:
                self.switches[addr2].links[p2] = link
                if addr2[0] == 't':
                    self.switches[addr2].queues[p2] = [queue.Queue() for _ in range(self.num_tor_ports)]
                elif addr2[0] == 'a':
                    self.switches[addr2].queues[p2] = [queue.Queue() for _ in range(3)]
                self.switches[addr2].voq_rr[p2] = 0
                self.switches[addr2].port_qsize[p2] = 0

    def run(self, flowtrace, endTimeslot, flowLogFile):
        """Run the network"""

        def parse_flow_line(line):
            toks = [t.strip() for t in line.split(",")]
            if len(toks) not in (7, 8):
                raise ValueError("Wrong flowtrace file format. Expected 7 or 8 columns.")
            Id = int(toks[0])
            src = toks[1]
            dst = toks[2]
            sport = int(toks[3])
            dport = int(toks[4])
            flowsize = int(toks[5])
            startTimeslot = int(toks[6])
            broadcast = None
            if len(toks) == 8:
                b = toks[7].strip()
                if b and b.lower() not in ("none", "na", "-", "0"):
                    broadcast = b
            return (Id, src, dst, sport, dport, flowsize, startTimeslot, broadcast)

        def launch_flow(flow, actual_start):
            """Create sender/receiver state for a single flow (unicast or broadcast)."""
            Id, src, dst, sport, dport, flowsize, _start, broadcast = flow

            # sender state
            self.hosts[src].sFlows[(dst, sport, dport)] = [flowsize, 0, 0, 0, broadcast]

            # priority assignment (keep your policy)
            if flowsize < 100:
                self.hosts[src].priority[(dst, sport, dport)] = 2
            elif flowsize > 1000:
                self.hosts[src].priority[(dst, sport, dport)] = 3
            else:
                self.hosts[src].priority[(dst, sport, dport)] = 2

            # receiver state(s)
            if broadcast is not None:
                recv_hosts = self.hosts[src].broadcast_groups.get(broadcast, [])
                if not recv_hosts:
                    sys.stdout.write(f"Broadcast group {broadcast} not found on host {src}\n")
                    raise RuntimeError("Missing broadcast group")

                # per-receiver ACK tracking at sender
                self.hosts[src].broad[(dst, sport, dport)] = {h: 0 for h in recv_hosts}

                # rFlows for every receiver
                for r in recv_hosts:
                    self.hosts[r].rFlows[(src, sport, dport)] = [Id, flowsize, 0, actual_start, 0, 0, broadcast]
            else:
                self.hosts[dst].rFlows[(src, sport, dport)] = [Id, flowsize, 0, actual_start, 0, 0, broadcast]

            # scheduling + congestion-control init (your existing init)
            self.hosts[src].rrSched.append((dst, sport, dport))
            self.hosts[src].retransmissionCnt[(dst, sport, dport)] = 0
            self.hosts[src].lastDecrease[(dst, sport, dport)] = 0
            self.hosts[src].cwnd[(dst, sport, dport)] = 50
            self.hosts[src].alpha[(dst, sport, dport)] = 0
            self.hosts[src].targetdelay[(dst, sport, dport)] = 0
            self.hosts[src].numPktSentInCurrWin[(dst, sport, dport)] = 0
            self.hosts[src].lastDecreaseRTT[(dst, sport, dport)] = 0
            self.hosts[src].initialized[(dst, sport, dport)] = False
            self.hosts[src].srtt[(dst, sport, dport)] = 0.0
            self.hosts[src].rttvar[(dst, sport, dport)] = 0.0
            self.hosts[src].base_rtt[(dst, sport, dport)] = 0.0
            self.hosts[src].rto_min[(dst, sport, dport)] = 0.0
            self.hosts[src].rto_max[(dst, sport, dport)] = 0.0
            self.hosts[src].RTO[(dst, sport, dport)] = 1000

        def write_reordering_log():
            with open("reordering_obm_per_flow.txt", "a", encoding="utf-8") as outf:
                for h, events_by_flow in self.reordering_pairs.items():
                    for (dst, src, dport, sport), pairs in events_by_flow.items():
                        for item in pairs:
                            if len(item) == 3:
                                ne, seq, pri = item
                            else:
                                _, ne, seq = item
                                pri = -1
                            outf.write(f"{h},{src},{dst},{sport},{dport},{ne},{seq},{pri}\n")
                outf.write("@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@\n")

        # ----------------- setup -----------------
        self.addLinks()
        ackQueues = {h: queue.Queue() for h in self.hosts}

        currTimeslot = 0
        totalPktSent = [0]
        totalPktRecvd = [0]
        totalFlowsFinished = [0]

        # ----------------- pre-read stages (<=0) -----------------
        # CSV contract: 0 batch, then -1, -2, ... , then +ve flows at end.
        stage_flows = defaultdict(list)   # key: startTimeslot <= 0 ; value: list[flow tuples]
        pos_next = None
        pos_eof = False

        f = open(flowtrace, "r")
        _header = f.readline()  # skip header

        # Read all non-positive flows into stage_flows; stop at first positive (stream positives later).
        while True:
            line = f.readline()
            if not line:
                pos_eof = True
                break
            if not line.strip():
                continue
            flow = parse_flow_line(line)
            if flow[6] <= 0:
                stage_flows[flow[6]].append(flow)
            else:
                pos_next = flow
                break

        # Stage execution order: 0 must complete, then -1, then -2, ...
        stage_order = sorted(stage_flows.keys(), reverse=True)  # e.g. [0, -1, -2, ...]
        stage_idx = 0
        curr_stage = stage_order[stage_idx] if stage_order else None
        stage_started = False

        # Only track *stage* flows here (positives never included)
        stage_outstanding = set()  # {(src, dst, sport, dport)} for current stage only

        # ----------------- main loop -----------------
        while currTimeslot < endTimeslot:
            if currTimeslot % 100 == 0:
                sys.stdout.write(
                    "current timeslot: " + str(currTimeslot) +
                    " total packets sent: " + str(totalPktSent[0]) +
                    " total packets received: " + str(totalPktRecvd[0]) +
                    " total flows finished: " + str(totalFlowsFinished[0]) + "\n"
                )

            # (A) Stage completion check (ONLY current stage; ignore +ve flows completely)
            if stage_started and curr_stage is not None:
                done = True
                for (src, dst, sport, dport) in stage_outstanding:
                    if (dst, sport, dport) in self.hosts[src].sFlows:
                        done = False
                        break
                if done:
                    stage_idx += 1
                    curr_stage = stage_order[stage_idx] if stage_idx < len(stage_order) else None
                    stage_started = False
                    stage_outstanding.clear()

                    # NEW: If we just finished the LAST non-positive stage, stop immediately.
                    if curr_stage is None:
                        sys.stdout.write(
                            "current timeslot: " + str(currTimeslot) +
                            " total packets sent: " + str(totalPktSent[0]) +
                            " total packets received: " + str(totalPktRecvd[0]) +
                            " total flows finished: " + str(totalFlowsFinished[0]) + "\n"
                        )
                        sys.stdout.write("Ending simulation as all non-positive (-ve and 0) stages have finished.\n")
                        nwTput = (totalPktRecvd[0] * 1500 * 8.0) / (max(1, currTimeslot) * 120.0)
                        packet_drops = 0
                        for addr1 in self.switches:
                            packet_drops += self.switches[addr1].packet_dropped
                        sys.stdout.write("Total Packets dropped: " + str(packet_drops) + " x 1500B\n")
                        sys.stdout.write("Network throughput (assuming 100G link and 1500B pkt): " + str(round(nwTput, 3)) + "Gbps\n")
                        write_reordering_log()
                        break

            # (B) Start next stage if needed:
            #     - stage 0 starts at timeslot 0
            #     - negative stages start as soon as previous stage finishes (at the current timeslot)
            if (not stage_started) and (curr_stage is not None):
                if curr_stage == 0:
                    if currTimeslot == 0:
                        for flow in stage_flows[0]:
                            launch_flow(flow, actual_start=0)
                            _, src, dst, sport, dport, *_ = flow
                            stage_outstanding.add((src, dst, sport, dport))
                        stage_started = True
                else:
                    # curr_stage < 0
                    for flow in stage_flows[curr_stage]:
                        launch_flow(flow, actual_start=currTimeslot)
                        _, src, dst, sport, dport, *_ = flow
                        stage_outstanding.add((src, dst, sport, dport))
                    stage_started = True

            # (C) Start positive flows orthogonally while stages are running.
            #     They should NOT affect stage progression or termination.
            #     (If we terminated above, we never get here.)
            while pos_next is not None and pos_next[6] <= currTimeslot:
                launch_flow(pos_next, actual_start=currTimeslot)

                next_line = f.readline()
                while next_line and (not next_line.strip()):
                    next_line = f.readline()

                if not next_line:
                    pos_next = None
                    pos_eof = True
                    break

                nxt = parse_flow_line(next_line)
                if nxt[6] <= 0:
                    # CSV contract says this won't happen; ignore safely
                    stage_flows[nxt[6]].append(nxt)
                    pos_next = None
                else:
                    pos_next = nxt

                if pos_next is not None and pos_next[6] > currTimeslot:
                    break

            # (D) Run hosts/switches for this timeslot
            for h in self.hosts:
                counts_delta, events = self.hosts[h].runHost(
                    currTimeslot, flowLogFile, ackQueues,
                    totalPktSent, totalPktRecvd, totalFlowsFinished
                )
                self.reordering_pairs[h] = {fk: list(v) for fk, v in events.items()}

            for s in self.switches:
                self.drops[s] = self.switches[s].runSwitch(currTimeslot)

            currTimeslot += 1

        # endTimeslot reached (and stages not finished)
        if currTimeslot >= endTimeslot:
            sys.stdout.write(
                "current timeslot: " + str(currTimeslot) +
                " total packets sent: " + str(totalPktSent[0]) +
                " total packets received: " + str(totalPktRecvd[0]) +
                " total flows finished: " + str(totalFlowsFinished[0]) + "\n"
            )
            sys.stdout.write("Ending simulation as end timeslot reached.\n")
            nwTput = (totalPktRecvd[0] * 1500 * 8.0) / (max(1, currTimeslot) * 120.0)
            packet_drops = 0
            for addr1 in self.switches:
                packet_drops += self.switches[addr1]
            sys.stdout.write("Total Packets dropped: " + str(packet_drops) + "Gbps\n")
            sys.stdout.write("Network throughput (assuming 100G link and 1500B pkt): " + str(round(nwTput, 3)) + "Gbps\n")
            write_reordering_log()

        for h in self.hosts:
            self.hosts[h].packetLogFile.close()

        f.close()
        return


def main():
    """Main function parses command line arguments and runs the network"""
    if len(sys.argv) < 5:
        sys.stdout.write("Usage: python3 network.py [networkSimulationFile.json] [flowtrace.csv] [logname] [endtimeslot]\n")
        return

    netCfgFilepath = sys.argv[1]
    flowtrace = sys.argv[2]
    logname = sys.argv[3]
    endTimeslot = int(sys.argv[4])

    net = Network(netCfgFilepath)

    protected = set(glob.glob(os.path.join('logs', 'recvd-flows-*.txt')))
    files = glob.glob('logs/*')
    for fp in files:
        if fp not in protected:
            os.remove(fp)

    flowLogFile = open(f"logs/recvd-flows-{logname}.txt", "a")
    net.run(flowtrace, endTimeslot, flowLogFile)
    print("#################################")
    flowLogFile.close()
    return


if __name__ == "__main__":
    main()
