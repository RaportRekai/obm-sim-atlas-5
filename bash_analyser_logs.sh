# Usage python bash_analyser_logs.py <path for log file>
# import sys
# import os
# import re
# file_name = sys.argv[1]
# with open (file_name,'r') as f:
#     for line in f:
#         print(line.strip())
#         breakpoint()

if [[ -f "filtered_logs_obm.txt" ]]; then
  rm filtered_logs_obm.txt
  echo "removing file filtered_logs_obm.txt"
fi
if [[ -f "filtered_logs_lqd_ideal.txt" ]]; then
  rm filtered_logs_lqd_ideal.txt
  echo "removing file filtered_logs_lqd_ideal.txt"
fi
file_name_obm="/home/dan/LQD/obm-sim/obm-sim/net-sim-obm/prev_logs/all_logs/run_49/recvd-flows-0.9.txt"
file_name_lqd="/home/dan/LQD/obm-sim/obm-sim/net-sim-lqd-ideal/logs/recvd-flows-0.9.txt"

while IFS= read -r line; do
  flowsize=$(echo "$line" | grep -o 'flowsize: .[^,]*' | awk '{print $2}')
  if [[ -n $flowsize && $flowsize -le 100 ]]; then
    echo "$line" >> filtered_logs_obm.txt
  fi
done < "$file_name_obm"

while IFS= read -r line; do
  flowsize=$(echo "$line" | grep -o 'flowsize: .[^,]*' | awk '{print $2}')
  if [[ -n $flowsize && $flowsize -le 100 ]]; then
    echo "$line" >> filtered_logs_lqd_ideal.txt
  fi
done < "$file_name_lqd"