set terminal postscript enhanced eps color font "Helvetica,14" size 4in,2in

set style line 1 lt 1  ps 1.5 pt 7 lw 5 lc rgb "#d7191c"
set style line 2 lt 1  ps 1.2 pt 2 lw 5 lc rgb "#fdae61"
set style line 3 lt 1  ps 1.2 pt 3 lw 5 lc rgb "#abdda4"
set style line 4 lt 1  ps 0.5 pt 7 lw 5 lc rgb "#2b83ba"
set style line 5 lt 3  ps 1.2 pt 7 lw 3 lc rgb "#000000"

set border 3

set xlabel "X (feet)"
set xtics 15 nomirror
#set xrange [-1:30]

set ylabel "Y (feet)"
set ytics nomirror
#set yrange [0:0.3]

#set grid
#set key top left
unset key

set cblabel "RSSI"
set palette model RGB defined ( -110 '#aaaaaa', -60 '#086fa1', -30 '#000000' )
#set palette model RGB defined ( -110 '#66a3d2', -30 '#033e6b' )
#set palette model RGB defined ( -110 '#F00000', -30 '#fdae61' )

set output "labels_avg.eps"
plot "rssis_avg.data" u ($1):($2):($3):($3) w labels font ",10" tc palette
