#!/bin/bash
ALGO="net-sim-abm"
BASE_DIR="/home/dan/LQD/obm-sim/obm-sim/$ALGO"
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
rm -rf "$LOG_DIR"/*
# cd net-sim-abm/
# echo python3 network.py 144-host-2-tier-fattree.json workloads/incast-trace-100G-degree-0.2.csv.processed 100000
# python3 network.py 144-host-2-tier-fattree.json workloads/incast-trace-100G-degree-0.2.csv.processed 0.2 100000
# cd ..
# echo workloads/incast-trace-100G-degree-0.2.csv.processed > stats_abm.txt
# python3 stats.py abm 0.2
# python3 stats.py abm 0.2 >> stats_abm.txt

# cd net-sim-abm/
# echo python3 network.py 144-host-2-tier-fattree.json workloads/incast-trace-100G-degree-0.4.csv.processed 100000
# python3 network.py 144-host-2-tier-fattree.json workloads/incast-trace-100G-degree-0.4.csv.processed 0.4 100000
# cd ..
# echo workloads/incast-trace-100G-degree-0.4.csv.processed >> stats_abm.txt
# python3 stats.py abm 0.4
# python3 stats.py abm 0.4 >> stats_abm.txt

# cd net-sim-abm/
# echo python3 network.py 144-host-2-tier-fattree.json workloads/incast-trace-100G-degree-0.6.csv.processed 100000
# python3 network.py 144-host-2-tier-fattree.json workloads/incast-trace-100G-degree-0.6.csv.processed 0.62 100000
# cd ..
# echo workloads/incast-trace-100G-degree-0.6.csv.processed >> stats_abm.txt
# python3 stats.py abm 0.62
# python3 stats.py abm 0.62 >> stats_abm.txt

# cd net-sim-abm/
# echo python3 network.py 144-host-2-tier-fattree.json workloads/incast-trace-100G-degree-0.8.csv.processed 100000
# python3 network.py 144-host-2-tier-fattree.json workloads/incast-trace-100G-degree-0.8.csv.processed 0.8 100000
# cd ..
# echo workloads/incast-trace-100G-degree-0.8.csv.processed >> stats_abm.txt
# python3 stats.py abm 0.8
# python3 stats.py abm 0.8 >> stats_abm.txt

# cd net-sim-abm/
# echo python3 network.py 144-host-2-tier-fattree.json workloads/websearch-trace-100G-load-0.3.csv.processed 100000
# python3 network.py 144-host-2-tier-fattree.json workloads/websearch-trace-100G-load-0.3.csv.processed 0.3 100000
# mkdir -p "$NEW_FOLDER"
# cd ..
# echo workloads/websearch-trace-100G-load-0.3.csv.processed >> stats_abm.txt
# python3 stats.py abm 0.3
# python3 stats.py abm 0.3 >> stats_abm.txt
# mv "$LOG_DIR/recvd-flows-0.3.txt" "$NEW_FOLDER/"
# cp "$SWITCH_FILE" "$NEW_FOLDER/"

# cd net-sim-abm/
# echo python3 network.py 144-host-2-tier-fattree.json workloads/websearch-trace-100G-load-0.6.csv.processed 100000
# python3 network.py 144-host-2-tier-fattree.json workloads/websearch-trace-100G-load-0.6.csv.processed 0.6 100000
# mkdir -p "$NEW_FOLDER"
# cd ..
# echo workloads/websearch-trace-100G-load-0.6.csv.processed >> stats_abm.txt
# python3 stats.py abm 0.6
# python3 stats.py abm 0.6 >> stats_abm.txt
# mv "$LOG_DIR/recvd-flows-0.6.txt" "$NEW_FOLDER/"
# cp "$SWITCH_FILE" "$NEW_FOLDER/"

cd net-sim-abm/
echo python3 network.py 144-host-2-tier-fattree.json workloads/websearch-trace-100G-load-0.9.csv.processed 100000
python3 network.py 144-host-2-tier-fattree.json workloads/websearch-trace-100G-load-0.9.csv.processed 0.9 100000
mkdir -p "$NEW_FOLDER"
cd ..
echo workloads/websearch-trace-100G-load-0.9.csv.processed >> stats_abm.txt
python3 stats.py abm 0.9
python3 stats.py abm 0.9 >> stats_abm.txt
mv "$LOG_DIR/recvd-flows-0.9.txt" "$NEW_FOLDER/"
cp "$SWITCH_FILE" "$NEW_FOLDER/"
