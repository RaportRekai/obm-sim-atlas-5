import re
file_name_obm = "/home/dan/LQD/obm-sim/obm-sim/filtered_logs_obm.txt"
file_name_lqd = "/home/dan/LQD/obm-sim/obm-sim/filtered_logs_lqd_ideal.txt"
flows = {}

def read_file(file_name, flows):
    with open (file_name,'r') as f:
        for line in f:
            src_m = re.search('src: [^,]*', line.strip())
            src = src_m.group(0).split()[1]
            dst_m = re.search('dst: [^,]*', line.strip())
            dst = dst_m.group(0).split()[1]
            sport_m = re.search('sport: [^,]*', line.strip())
            sport = sport_m.group(0).split()[1]
            dport_m = re.search('dport: [^,]*', line.strip())
            dport = dport_m.group(0).split()[1]
            fct_m = re.search('fct: [^,]*', line.strip())
            fct = fct_m.group(0).split()[1]
            flows[(src,dst,sport,dport)] = fct
            #breakpoint()

flow_obm = {}
flow_lqd = {}
read_file(file_name=file_name_obm, flows=flow_obm)
read_file(file_name=file_name_lqd, flows=flow_lqd)

count = 0
count_adhere = 0
for key, value in flow_obm.items():
    if key not in flow_lqd:
        print("key not present")
        print(f"key: {key}")
    else:
        if int(flow_lqd[key])>int(value):
            count+=1
        elif int(flow_lqd[key])<int(value):
            count_adhere+=1
print(f"violation flows = {count}")
print(f"adherence flows = {count_adhere}")
print(f"total flows = {len(flow_obm)}")
        