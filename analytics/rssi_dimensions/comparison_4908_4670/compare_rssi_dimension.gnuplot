set terminal postscript enhanced eps color font "Helvetica,14" size 3in,3in

data_4670 = "../sairohit_day3_1045_1130/rssi_view.dat"
data_4908 = "../brghena_day2_1900_2100/rssi_view.dat"
avg_4670 = "sairohit_4670_averaged.dat"
avg_4908 = "brghena_4908_averaged.dat"

set style line 1 lt 2 ps 0.5 pt 7 lw 3 lc rgb "black" #"#7e2f8e" # purple
set style line 2 lt 2 ps 0.5 pt 7 lw 3 lc rgb "black" #"#0072bd" # blue
set style line 3 lt 2 ps 0.5 pt 7 lw 3 lc rgb "black" #"#d95319" # orange
set style line 4 lt 2 ps 0.5 pt 7 lw 3 lc rgb "black" #"#77ac30" # green
set style line 5 lt 2 ps 0.5 pt 7 lw 3 lc rgb "black" #"#4dbeee" # light-blue
set style line 6 lt 2 ps 0.5 pt 7 lw 3 lc rgb "black" #"#a2142f" # red
set style line 11 lt 1 ps 0.5 pt 7 lw 1 lc rgb "#7e2f8e" # purple
set style line 12 lt 1 ps 0.5 pt 7 lw 1 lc rgb "#0072bd" # blue
set style line 13 lt 1 ps 0.5 pt 7 lw 1 lc rgb "#edb120" # yellow
set style line 14 lt 1 ps 0.5 pt 7 lw 1 lc rgb "#77ac30" # green
set style line 15 lt 1 ps 0.5 pt 7 lw 1 lc rgb "#4dbeee" # light-blue
set style line 16 lt 1 ps 0.5 pt 7 lw 1 lc rgb "#a2142f" # red

set style line 23 lt 1 ps 0.5 pt 13 lw 1 lc rgb "#0072bd" # green
set style line 26 lt 1 ps 0.5 pt 13 lw 1 lc rgb "#77ac30" # purple

set border 3
set key opaque box
set size square

set xlabel "RSSI 4908"
set xtics nomirror
set xrange[-100:-60]

set ylabel "RSSI 4670"
set ytics nomirror 
set yrange [-100:-60]

set arrow nohead from -100,-100 to -60,-60 lt 2 lc rgb "grey"

set output "compare_rssi_dimension.eps"
plot \
    data_4670 u ($2+0.1):($4) w p ls 13 title "Raw in 4670", \
    data_4908 u ($2-0.1):($4) w p ls 16 title "Raw in 4908", \
    avg_4670  u ($2):($4+0.1) w p ls 23 title "Avg in 4670", \
    avg_4908  u ($2):($4-0.1) w p ls 26 title "Avg in 4908", \

set output "compare_rssi_dimension_raw.eps"
plot \
    data_4670 u ($2+0.1):($4) w p ls 13 title "User in 4670", \
    data_4908 u ($2-0.1):($4) w p ls 16 title "User in 4908", \

set output "compare_rssi_dimension_avg.eps"
plot \
    avg_4670  u ($2):($4+0.1) w p ls 23 title "User in 4670", \
    avg_4908  u ($2):($4-0.1) w p ls 26 title "User in 4908", \

