set terminal postscript enhanced eps color font "Helvetica,14" size 6in,3in
set output "twodays.eps"

set style line 1 lt 1  ps 1.5 pt 7 lw 5 lc rgb "#d7191c"
set style line 2 lt 1  ps 1.2 pt 2 lw 5 lc rgb "#fdae61"
set style line 3 lt 1  ps 1.2 pt 3 lw 5 lc rgb "#abdda4"
set style line 4 lt 1  ps 0.5 pt 7 lw 0.5 lc rgb "#2b83ba"
set style line 5 lt 3  ps 1.2 pt 7 lw 3 lc rgb "#000000"

set border 3
set key opaque box

set multiplot layout 2,1


# plot 1
set xlabel "Time"
set xtics 21600000 nomirror \
        ("18:00" 14400000, "0:00" 36000000, "6:00" 57600000, "12:00" 79200000, "18:00" 100800000, "0:00" 122400000, "6:00" 144000000, "12:00" 165600000, "18:00" 187200000, "0:00" 208800000, "6:00" 230400000, "12:00" 252000000, "18:00" 273600000, "0:00" 295200000, "6:00" 316800000, "12:00" 338400000, "18:00" 360000000, "0:00" 381600000, "6:00" 403200000, "12:00" 424800000, "18:00" 446400000, "0:00" 468000000, "6:00" 489600000, "12:00" 511200000, "18:00" 532800000, "0:00" 554400000, "6:00" 576000000, "12:00" 597600000) \
        font ", 14"
set xrange[457200000:608400000]

set ylabel "RSSI"
set yrange[-100:-50]
set ytics nomirror

plot 'twodays.dat' u ($1):($2) w lp ls 4 lc rgb "#2b83ba" title "1929 Plymouth"


# plot 2
#plot 'twodays.dat' u ($1):($5) w l ls 4 lc rgb "#2b83ba" title "1929 Plymouth"


# plot 3
set ylabel "Seconds since last packet"
set yrange[0:60]

unset key

plot 'twodays.dat' u ($1):($4) w l ls 4 lc rgb "#d7191c" notitle


unset multiplot

