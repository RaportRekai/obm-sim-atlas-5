

# cd net-sim-obm/
# echo python3 network.py 144-host-2-tier-fattree.json workloads/incast-trace-100G-degree-0.2.csv.processed 1000000
# python3 network.py 144-host-2-tier-fattree.json workloads/incast-trace-100G-degree-0.2.csv.processed 0.2 1000000
# cd ..
# echo workloads/incast-trace-100G-degree-0.2.csv.processed > stats_obm.txt
# python3 stats.py obm 0.2
# python3 stats.py obm 0.2 >> stats_obm.txt

# # cd net-sim-obm/
# # echo python3 network.py 144-host-2-tier-fattree.json workloads/incast-trace-100G-degree-0.4.csv.processed 1000000
# # python3 network.py 144-host-2-tier-fattree.json workloads/incast-trace-100G-degree-0.4.csv.processed 0.4 1000000
# # cd ..
# echo workloads/incast-trace-100G-degree-0.4.csv.processed >> stats_obm.txt
# python3 stats.py obm 0.4
# python3 stats.py obm 0.4 >> stats_obm.txt

# # cd net-sim-obm/
# # echo python3 network.py 144-host-2-tier-fattree.json workloads/incast-trace-100G-degree-0.6.csv.processed 1000000
# # python3 network.py 144-host-2-tier-fattree.json workloads/incast-trace-100G-degree-0.6.csv.processed 0.62 1000000
# # cd ..
# echo workloads/incast-trace-100G-degree-0.6.csv.processed >> stats_obm.txt
# python3 stats.py obm 0.62
# python3 stats.py obm 0.62 >> stats_obm.txt

# # cd net-sim-obm/
# # echo python3 network.py 144-host-2-tier-fattree.json workloads/incast-trace-100G-degree-0.8.csv.processed 1000000
# # python3 network.py 144-host-2-tier-fattree.json workloads/incast-trace-100G-degree-0.8.csv.processed 0.8 1000000
# # cd ..
# echo workloads/incast-trace-100G-degree-0.8.csv.processed >> stats_obm.txt
# python3 stats.py obm 0.8
# python3 stats.py obm 0.8 >> stats_obm.txt

# cd net-sim-obm/
# echo python3 network.py 144-host-2-tier-fattree.json workloads/websearch-trace-100G-load-0.3.csv.processed 0.3 1000000
# python3 network.py 144-host-2-tier-fattree.json workloads/websearch-trace-100G-load-0.3.csv.processed 0.3 1000000
# cd ..
# echo workloads/websearch-trace-100G-load-0.3.csv.processed >> stats_obm.txt
# python3 stats.py obm 0.3
# python3 stats.py obm 0.3 >> stats_obm.txt

# # cd net-sim-obm/
# # echo python3 network.py 144-host-2-tier-fattree.json workloads/websearch-trace-100G-load-0.6.csv.processed 0.6 1000000
# # python3 network.py 144-host-2-tier-fattree.json workloads/websearch-trace-100G-load-0.6.csv.processed 0.6 1000000
# # cd ..
# echo workloads/websearch-trace-100G-load-0.6.csv.processed >> stats_obm.txt
# python3 stats.py obm 0.6
# python3 stats.py obm 0.6 >> stats_obm.txt

# cd net-sim-allg/
# echo python3 network.py small_net.json workloads/butterfly_allreduce_16.csv 100 1000000
# python3 network.py small_net.json workloads/butterfly_allreduce_16_seq.csv 100 1000000
# cd ..
# echo workloads/ring_allreduce_16.csv >> stats_obm.txt
# python3 stats.py allg 100
# python3 stats.py allg 100 >> stats_allg.txt

cd net-sim-allg/

# 100
echo python3 network.py small_net.json workloads/alt_hier_rd_broadcast_grad128_with_background.csv 100 1000000
python3 network.py small_net.json workloads/alt_hier_rd_broadcast_grad128_with_background.csv 100 1000000
cd ..
echo workloads/alt_hier_rd_broadcast_grad128_with_background.csv >> stats_allg.txt
python3 stats.py allg 100
python3 stats.py allg 100 >> stats_allg.txt
cd net-sim-allg/

# 101
echo python3 network.py small_net.json workloads/alt_hier_rd_broadcast_grad128.csv 101 1000000
python3 network.py small_net.json workloads/alt_hier_rd_broadcast_grad128.csv 101 1000000
cd ..
echo workloads/alt_hier_rd_broadcast_grad128.csv >> stats_allg.txt
python3 stats.py allg 101
python3 stats.py allg 101 >> stats_allg.txt
cd net-sim-allg/

# 102
echo python3 network.py small_net.json workloads/butterfly_allreduce_16_seq_with_background.csv 102 1000000
python3 network.py small_net.json workloads/butterfly_allreduce_16_seq_with_background.csv 102 1000000
cd ..
echo workloads/butterfly_allreduce_16_seq_with_background.csv >> stats_allg.txt
python3 stats.py allg 102
python3 stats.py allg 102 >> stats_allg.txt
cd net-sim-allg/

# 103
echo python3 network.py small_net.json workloads/butterfly_allreduce_16_seq.csv 103 1000000
python3 network.py small_net.json workloads/butterfly_allreduce_16_seq.csv 103 1000000
cd ..
echo workloads/butterfly_allreduce_16_seq.csv >> stats_allg.txt
python3 stats.py allg 103
python3 stats.py allg 103 >> stats_allg.txt
cd net-sim-allg/

# 104
echo python3 network.py small_net.json workloads/hierarchical_butterfly_allreduce_16_seq_with_background.csv 104 1000000
python3 network.py small_net.json workloads/hierarchical_butterfly_allreduce_16_seq_with_background.csv 104 1000000
cd ..
echo workloads/hierarchical_butterfly_allreduce_16_seq_with_background.csv >> stats_allg.txt
python3 stats.py allg 104
python3 stats.py allg 104 >> stats_allg.txt
cd net-sim-allg/

# 105
echo python3 network.py small_net.json workloads/hierarchical_butterfly_allreduce_16_seq.csv 105 1000000
python3 network.py small_net.json workloads/hierarchical_butterfly_allreduce_16_seq.csv 105 1000000
cd ..
echo workloads/hierarchical_butterfly_allreduce_16_seq.csv >> stats_allg.txt
python3 stats.py allg 105
python3 stats.py allg 105 >> stats_allg.txt
cd net-sim-allg/

# 106
echo python3 network.py small_net.json workloads/reduce_scatter_allgather_16_seq_halved_with_background_traffic.csv 106 1000000
python3 network.py small_net.json workloads/reduce_scatter_allgather_16_seq_halved_with_background_traffic.csv 106 1000000
cd ..
echo workloads/reduce_scatter_allgather_16_seq_halved_with_background_traffic.csv >> stats_allg.txt
python3 stats.py allg 106
python3 stats.py allg 106 >> stats_allg.txt
cd net-sim-allg/

# 107
echo python3 network.py small_net.json workloads/reduce_scatter_allgather_16_seq_halved.csv 107 1000000
python3 network.py small_net.json workloads/reduce_scatter_allgather_16_seq_halved.csv 107 1000000
cd ..
echo workloads/reduce_scatter_allgather_16_seq_halved.csv >> stats_allg.txt
python3 stats.py allg 107
python3 stats.py allg 107 >> stats_allg.txt
cd net-sim-allg/

# 108
echo python3 network.py small_net.json workloads/strict_hierarchical_grad128_with_background.csv 108 1000000
python3 network.py small_net.json workloads/strict_hierarchical_grad128_with_background.csv 108 1000000
cd ..
echo workloads/strict_hierarchical_grad128_with_background.csv >> stats_allg.txt
python3 stats.py allg 108
python3 stats.py allg 108 >> stats_allg.txt
cd net-sim-allg/

# 109
echo python3 network.py small_net.json workloads/strict_hierarchical_grad128.csv 109 1000000
python3 network.py small_net.json workloads/strict_hierarchical_grad128.csv 109 1000000
cd ..
echo workloads/strict_hierarchical_grad128.csv >> stats_allg.txt
python3 stats.py allg 109
python3 stats.py allg 109 >> stats_allg.txt


cd net-sim-allg/
echo python3 network.py small_net.json workloads/ring_allreduce_16.csv 110 1000000
python3 network.py small_net.json workloads/ring_allreduce_16.csv 110 1000000
cd ..
echo workloads/ring_allreduce_16.csv >> stats_allg.txt
python3 stats.py allg 110
python3 stats.py allg 110 >> stats_allg.txt

cd net-sim-allg/
echo python3 network.py small_net.json workloads/ring_allreduce_16_with_background.csv 111 1000000
python3 network.py small_net.json workloads/ring_allreduce_16_with_background.csv 111 1000000
cd ..
echo workloads/ring_allreduce_16_with_background.csv >> stats_allg.txt
python3 stats.py allg 111
python3 stats.py allg 111 >> stats_allg.txt

# alt_hier_rd_broadcast_grad128_with_background
# alt_hier_rd_broadcast_grad128
# butterfly_allreduce_16_seq_with_background
# butterfly_allreduce_16_seq
# hierarchical_butterfly_allreduce_16_seq_with_background
# hierarchical_butterfly_allreduce_16_seq
# reduce_scatter_allgather_16_seq_halved_with_background_traffic
# reduce_scatter_allgather_16_seq_halved
# strict_hierarchical_grad128_with_background
# strict_hierarchical_grad128