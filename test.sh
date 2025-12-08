cd net-sim-obm/
echo python3 network.py 144-host-2-tier-fattree.json workloads/websearch-trace-100G-load-0.6.csv.processed 1000000
python3 network.py 144-host-2-tier-fattree.json workloads/websearch-trace-100G-load-0.6.csv.processed 1000000
cd ..
echo workloads/websearch-trace-100G-load-0.6.csv.processed >> stats_obm.txt
python3 stats.py obm
python3 stats.py obm >> stats_obm.txt