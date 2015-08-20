set terminal postscript enhanced eps color font "Helvetica,14" size 4in,3in

set style line 1 lt 1  ps 1.5 pt 7 lw 5 lc rgb "#d7191c"
set style line 2 lt 1  ps 1.2 pt 2 lw 5 lc rgb "#fdae61"
set style line 3 lt 1  ps 1.2 pt 3 lw 5 lc rgb "#abdda4"
set style line 4 lt 1  ps 1 pt 7 lw 5 lc rgb "#2b83ba"
set style line 5 lt 3  ps 1.2 pt 7 lw 3 lc rgb "#000000"

set border 3

set xlabel "Distance (m)"
set xtics nomirror

set ylabel "RSSI"
set ytics nomirror

#set grid
#set key top left
unset key

plotname = "rssis"
set output plotname.".eps"
plot plotname.".data" u ($1):($2) w p ls 4

