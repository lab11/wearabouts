
import time

start_stamp = 1404826500000
end_stamp = 1404869700000

def cur_datetime(time_num):
    return time.strftime("%m/%d/%Y %H:%M", time.localtime(time_num/1000))

for timestamp in range(start_stamp, end_stamp, 5*60*1000):
    print(cur_datetime(timestamp) + ':  ' + str(timestamp))
