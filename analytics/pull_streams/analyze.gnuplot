set terminal postscript enhanced eps color font "Helvetica,14" size 6in,6in
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

set multiplot layout 5,1

# plot the data
#   Note: this ternary operator is a hack. Essentially it means to plot only
# the data that matches the selected location ID
plot 'data_rssi.dat' u ($1):($3==0?$2:-200) w p ls 4 lc rgb "#d7191c" title "4908"
plot 'data_rssi.dat' u ($1):($3==1?$2:-200) w p ls 4 lc rgb "#fdae61" title "4901"
plot 'data_rssi.dat' u ($1):($3==2?$2:-200) w p ls 4 lc rgb "#abdda4" title "4670"
plot 'data_rssi.dat' u ($1):($3==3?$2:-200) w p ls 4 lc rgb "#2b83ba" title "4916"
plot 'data_rssi.dat' u ($1):($3==4?$2:-200) w p ls 4 lc rgb "#522b72" title "4776"
#plot 'data_rssi.dat' u ($1):($3==5?$2:-200) w lp ls 4 lc rgb "#2b83ba" title "1929 Plymouth"

