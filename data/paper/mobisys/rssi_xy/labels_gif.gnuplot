set terminal postscript enhanced eps color font "Helvetica,14" size 8in,6in

set style line 1 lt 1  ps 1.5 pt 7 lw 5 lc rgb "#d7191c"
set style line 2 lt 1  ps 1.2 pt 2 lw 5 lc rgb "#fdae61"
set style line 3 lt 1  ps 1.2 pt 3 lw 5 lc rgb "#abdda4"
set style line 4 lt 1  ps 9   pt 7 lw 5 lc rgb "#2b83ba"
set style line 5 lt 3  ps 1.2 pt 7 lw 3 lc rgb "#000000"

set border 3

set xlabel "X (feet)"
set xtics nomirror
set xrange [0:13]

set ylabel "Y (feet)"
set ytics nomirror
set yrange [-1:13]

#set grid
#set key top left
unset key

#set cblabel "RSSI"
unset colorbox

set palette model RGB defined ( -110 '#aaaaaa', -60 '#086fa1', -30 '#000000' )
#set palette model RGB defined ( -110 '#66a3d2', -30 '#033e6b' )
#set palette model RGB defined ( -110 '#F00000', -30 '#fdae61' )

set output "labels_0.eps"
#plot "rssis_0.data" u ($1):($2):($3):($3) w labels font ",30" tc palette
plot "rssis_0.data" u ($1):($2):($3):($3) w p ls 4 palette

set output "labels_1.eps"
#plot "rssis_1.data" u ($1):($2):($3):($3) w labels font ",30" tc palette
plot "rssis_1.data" u ($1):($2):($3):($3) w p ls 4 palette

set output "labels_2.eps"
#plot "rssis_2.data" u ($1):($2):($3):($3) w labels font ",30" tc palette
plot "rssis_2.data" u ($1):($2):($3):($3) w p ls 4 palette

set output "labels_3.eps"
#plot "rssis_3.data" u ($1):($2):($3):($3) w labels font ",30" tc palette
plot "rssis_3.data" u ($1):($2):($3):($3) w p ls 4 palette

set output "labels_4.eps"
#plot "rssis_4.data" u ($1):($2):($3):($3) w labels font ",30" tc palette
plot "rssis_4.data" u ($1):($2):($3):($3) w p ls 4 palette

set output "labels_5.eps"
#plot "rssis_5.data" u ($1):($2):($3):($3) w labels font ",30" tc palette
plot "rssis_5.data" u ($1):($2):($3):($3) w p ls 4 palette

set output "labels_6.eps"
#plot "rssis_6.data" u ($1):($2):($3):($3) w labels font ",30" tc palette
plot "rssis_6.data" u ($1):($2):($3):($3) w p ls 4 palette

set output "labels_7.eps"
#plot "rssis_7.data" u ($1):($2):($3):($3) w labels font ",30" tc palette
plot "rssis_7.data" u ($1):($2):($3):($3) w p ls 4 palette

set output "labels_8.eps"
#plot "rssis_8.data" u ($1):($2):($3):($3) w labels font ",30" tc palette
plot "rssis_8.data" u ($1):($2):($3):($3) w p ls 4 palette

set output "labels_9.eps"
#plot "rssis_9.data" u ($1):($2):($3):($3) w labels font ",30" tc palette
plot "rssis_9.data" u ($1):($2):($3):($3) w p ls 4 palette

