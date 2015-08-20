set terminal postscript enhanced eps color font "Helvetica,14" size 6in,12in
set output "analyze.eps"

set style line 1 lt 1  ps 1.5 pt 7 lw 5 lc rgb "#d7191c"
set style line 2 lt 1  ps 1.2 pt 2 lw 5 lc rgb "#fdae61"
set style line 3 lt 1  ps 1.2 pt 3 lw 5 lc rgb "#abdda4"
set style line 4 lt 1  ps 0.5 pt 7 lw 0.5 lc rgb "#2b83ba"
set style line 5 lt 3  ps 1.2 pt 7 lw 3 lc rgb "#000000"

set border 3
set xlabel "Time"
set ylabel "RSSI"
set xtics nomirror
set yrange[-100:-50]
set ytics nomirror
set key opaque box

set multiplot layout 12,1

# plot the data
plot 'squall_pos1.dat' u ($1):($2) w p ls 4 lc rgb "#d7191c" title "pos1"
plot 'squall_pos2.dat' u ($1):($2) w p ls 4 lc rgb "#d7191c" title "pos2"
plot 'squall_pos3.dat' u ($1):($2) w p ls 4 lc rgb "#d7191c" title "pos3"
plot 'squall_pos4.dat' u ($1):($2) w p ls 4 lc rgb "#d7191c" title "pos4"
plot 'squall_pos5.dat' u ($1):($2) w p ls 4 lc rgb "#d7191c" title "pos5"
plot 'squall_pos6.dat' u ($1):($2) w p ls 4 lc rgb "#d7191c" title "pos6"

plot 'fitbit_pos1.dat' u ($1):($2) w p ls 4 lc rgb "#2b83ba" title "pos1"
plot 'fitbit_pos2.dat' u ($1):($2) w p ls 4 lc rgb "#2b83ba" title "pos2"
plot 'fitbit_pos3.dat' u ($1):($2) w p ls 4 lc rgb "#2b83ba" title "pos3"
plot 'fitbit_pos4.dat' u ($1):($2) w p ls 4 lc rgb "#2b83ba" title "pos4"
plot 'fitbit_pos5.dat' u ($1):($2) w p ls 4 lc rgb "#2b83ba" title "pos5"
plot 'fitbit_pos6.dat' u ($1):($2) w p ls 4 lc rgb "#2b83ba" title "pos6"

