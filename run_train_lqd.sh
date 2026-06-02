BASE_DIR="net-sim-lqd"

cd "$BASE_DIR"
rm -rf logs/*

mkdir -p '../net-sim-lqd/training_logs/0.2'
rm -rf "../net-sim-lqd/training_logs/0.2/*"
python3 network.py 144-host-2-tier-fattree.json "workloads/incast-trace-100G-degree-0.2.csv.processed" 0.2 100000
cd ..
echo workloads/incast-trace-100G-degree-0.2.csv.processed >> stats_lqd.txt
python3 stats.py lqd 0.2
python3 stats.py lqd 0.2 >> stats_lqd.txt

# cd "$BASE_DIR"
# mkdir -p '../net-sim-lqd/training_logs/0.4'
# rm -rf "../net-sim-lqd/training_logs/0.4/*"
# python3 network.py 144-host-2-tier-fattree.json "workloads/incast-trace-100G-degree-0.4.csv.processed" 0.4 100000
# cd ..
# echo workloads/incast-trace-100G-degree-0.4.csv.processed >> stats_lqd.txt
# python3 stats.py lqd 0.4
# python3 stats.py lqd 0.4 >> stats_lqd.txt

# cd "$BASE_DIR"
# mkdir -p '../net-sim-lqd/training_logs/0.62'
# rm -rf "../net-sim-lqd/training_logs/0.62/*"
# python3 network.py 144-host-2-tier-fattree.json "workloads/incast-trace-100G-degree-0.6.csv.processed" 0.62 100000
# cd ..
# echo workloads/incast-trace-100G-degree-0.6.csv.processed >> stats_lqd.txt
# python3 stats.py lqd 0.62
# python3 stats.py lqd 0.62 >> stats_lqd.txt
# mv "$LOG_DIR/recvd-flows-0.62.txt" "$NEW_FOLDER/"
# cp "$SWITCH_FILE" "$NEW_FOLDER/"

# cd "$BASE_DIR"
# mkdir -p '../net-sim-lqd/training_logs/0.8'
# rm -rf "../net-sim-lqd/training_logs/0.8/*"
# python3 network.py 144-host-2-tier-fattree.json "workloads/incast-trace-100G-degree-0.8.csv.processed" 0.8 100000
# cd ..
# echo workloads/incast-trace-100G-degree-0.8.csv.processed >> stats_lqd.txt
# python3 stats.py lqd 0.8
# python3 stats.py lqd 0.8 >> stats_lqd.txt
# mv "$LOG_DIR/recvd-flows-0.8.txt" "$NEW_FOLDER/"
# cp "$SWITCH_FILE" "$NEW_FOLDER/"