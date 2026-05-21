#!/bin/bash
BASE_DIR="/home/dan/LQD/obm-sim/obm-sim/net-sim-lqd-ideal"
LOG_DIR="$BASE_DIR/logs"
ARCHIVE_DIR="$BASE_DIR/prev_logs/all_logs"
SWITCH_FILE="$BASE_DIR/switch.py"
# Find next run number

mkdir -p "$LOG_DIR"
mkdir -p "$ARCHIVE_DIR"

NEXT_NUM=1
while [ -d "$ARCHIVE_DIR/run_$NEXT_NUM" ]; do
    ((NEXT_NUM++))
done
NEW_FOLDER="$ARCHIVE_DIR/run_$NEXT_NUM"

# Incast
cd net-sim-lqd-ideal
python3 network.py 144-host-2-tier-fattree.json "workloads/incast-trace-100G-degree-0.2.csv.processed" 0.2 1000000
mkdir -p "$NEW_FOLDER"
cd ..
echo workloads/incast-trace-100G-degree-0.2.csv.processed >> stats_lqd_ideal.txt
python3 stats.py lqd-ideal 0.2
python3 stats.py lqd-ideal 0.2 >> stats_lqd_ideal.txt
mv "$LOG_DIR/recvd-flows-0.2.txt" "$NEW_FOLDER/"
cp "$SWITCH_FILE" "$NEW_FOLDER/"

cd net-sim-lqd-ideal
python3 network.py 144-host-2-tier-fattree.json "workloads/incast-trace-100G-degree-0.4.csv.processed" 0.4 1000000
mkdir -p "$NEW_FOLDER"
cd ..
echo workloads/incast-trace-100G-degree-0.4.csv.processed >> stats_lqd_ideal.txt
python3 stats.py lqd-ideal 0.4
python3 stats.py lqd-ideal 0.4 >> stats_lqd_ideal.txt
mv "$LOG_DIR/recvd-flows-0.4.txt" "$NEW_FOLDER/"
cp "$SWITCH_FILE" "$NEW_FOLDER/"

cd net-sim-lqd-ideal
python3 network.py 144-host-2-tier-fattree.json "workloads/incast-trace-100G-degree-0.6.csv.processed" 0.62 1000000
mkdir -p "$NEW_FOLDER"
cd ..
echo workloads/incast-trace-100G-degree-0.6.csv.processed >> stats_lqd_ideal.txt
python3 stats.py lqd-ideal 0.62
python3 stats.py lqd-ideal 0.62 >> stats_lqd_ideal.txt
mv "$LOG_DIR/recvd-flows-0.62.txt" "$NEW_FOLDER/"
cp "$SWITCH_FILE" "$NEW_FOLDER/"

cd net-sim-lqd-ideal
python3 network.py 144-host-2-tier-fattree.json "workloads/incast-trace-100G-degree-0.8.csv.processed" 0.8 1000000
mkdir -p "$NEW_FOLDER"
cd ..
echo workloads/incast-trace-100G-degree-0.8.csv.processed >> stats_lqd_ideal.txt
python3 stats.py lqd-ideal 0.8
python3 stats.py lqd-ideal 0.8 >> stats_lqd_ideal.txt
mv "$LOG_DIR/recvd-flows-0.8.txt" "$NEW_FOLDER/"
cp "$SWITCH_FILE" "$NEW_FOLDER/"