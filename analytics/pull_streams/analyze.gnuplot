set terminal postscript enhanced eps color font "Helvetica,14" size 6in,6in
set output "analyze.eps"

set style line 1 lt 1 ps 1 pt 7 lw 1 lc rgb "#7e2f8e" # purple
set style line 2 lt 1 ps 1 pt 7 lw 2 lc rgb "#a2142f" # red
set style line 3 lt 1 ps 1 pt 7 lw 1 lc rgb "#edb120" # yellow
set style line 4 lt 1 ps 1 pt 7 lw 1 lc rgb "#77ac30" # green
set style line 5 lt 1 ps 1 pt 7 lw 1 lc rgb "#4dbeee" # light-blue

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
plot 'data_rssi.dat' u ($1):($4==0?$3:-200) w p ls 2 title "4908"
plot 'data_rssi.dat' u ($1):($4==1?$3:-200) w p ls 1 title "4901"
plot 'data_rssi.dat' u ($1):($4==2?$3:-200) w p ls 3 title "4670"
plot 'data_rssi.dat' u ($1):($4==3?$3:-200) w p ls 4 title "4916"
plot 'data_rssi.dat' u ($1):($4==4?$3:-200) w p ls 5 title "4776"
#plot 'data_rssi.dat' u ($1):($4==5?$3:-200) w lp ls 4 lc rgb "#2b83ba" title "1929 Plymouth"

