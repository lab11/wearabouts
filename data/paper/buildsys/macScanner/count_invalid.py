import ast

strs = ['4908', '4901', '4670']
total_invalid = 0
total = 0
invalues = []

for loc in strs:
    with open(loc+'.data') as f:
        for line in f:
            total += 1
            loaded_data = ast.literal_eval(line)
            rssi = loaded_data['avg_rssi']
            if rssi < -100 or -20 < rssi:
                total_invalid += 1
                invalues.append(rssi)
                #print(str(rssi))

print("Total: " + str(total) + "  Invalid: " + str(total_invalid))
print set(invalues)
