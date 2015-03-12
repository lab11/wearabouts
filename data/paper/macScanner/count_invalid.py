import ast

strs = ['4908', '4901', '4670']
total = 0
invalues = []

for loc in strs:
    with open(loc+'.data') as f:
        for line in f:
            loaded_data = ast.literal_eval(line)
            rssi = loaded_data['rssi']
            if rssi < -100 or -20 < rssi:
                total += 1
                invalues.append(rssi)
                #print(str(rssi))

print total
print set(invalues)
