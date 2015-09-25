#!/usr/bin/env python

# start time = 18:27:43
# seconds to 19:00:00 = 1937
# seconds to 18:00:00 = -1663

# end time = 19:41:09
# seconds to 20:00:00 = 1131
# seconds from start to 20:00:00 = 264737
# 74 hours total

curr_hour = 18
curr_min = 0

seconds_elapsed = -1663

out_string = '('

while seconds_elapsed  <= 264737:
    out_string += '"'
    out_string += ('0' if curr_hour < 10 else '') + str(curr_hour)
    out_string += ':00" '
    out_string += str(seconds_elapsed)
    out_string += ', '

    curr_hour += 1
    if curr_hour == 24:
        curr_hour = 0

    seconds_elapsed += 3600

# overwrite last comma and space
out_string = out_string[:-2] + ')'

print(out_string)


