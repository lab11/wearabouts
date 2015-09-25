set terminal postscript enhanced eps color font "Helvetica,14" size 3in,3in
set output "rssi_dimension.eps"

data_file = "rssi_view.dat"

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

set border 3
set key opaque box
set size square

set xlabel "RSSI 4908"
set xtics nomirror
set xrange[-100:-50]

set ylabel "RSSI other"
set ytics nomirror 
set yrange [-100:-50]

plot data_file u ($3):($2) w p ls 11 title "vs 4908", \
     data_file u ($3):($4) w p ls 13 title "vs 4670", \
     data_file u ($3):($5) w p ls 14 title "vs 4916", \
     data_file u ($3):($6) w p ls 15 title "vs 4776", \

