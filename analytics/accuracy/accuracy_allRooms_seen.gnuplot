set terminal postscript enhanced eps color font "Helvetica,14" size 24in,12in
set output "accuracy_allRooms_seen.eps"

#wearabouts_file = "rssi_data_4908only_seen.dat"
wearabouts_file = "rssi_data_allRooms_seen.dat"

set style line 1 lt 2 ps 0.5 pt 7 lw 3 lc rgb "black" #"#7e2f8e" # purple
set style line 2 lt 2 ps 0.5 pt 7 lw 3 lc rgb "black" #"#0072bd" # blue
set style line 3 lt 2 ps 0.5 pt 7 lw 3 lc rgb "black" #"#d95319" # orange
set style line 4 lt 2 ps 0.5 pt 7 lw 3 lc rgb "black" #"#77ac30" # green
set style line 5 lt 2 ps 0.5 pt 7 lw 3 lc rgb "black" #"#4dbeee" # light-blue
set style line 6 lt 2 ps 0.5 pt 7 lw 3 lc rgb "black" #"#a2142f" # red
set style line 11 lt 1 ps 0.5 pt 7 lw 0.01 lc rgb "#7e2f8e" # purple
set style line 12 lt 1 ps 0.5 pt 7 lw 0.01 lc rgb "#0072bd" # blue
set style line 13 lt 1 ps 0.5 pt 7 lw 0.01 lc rgb "#d95319" # orange
set style line 14 lt 1 ps 0.5 pt 7 lw 0.01 lc rgb "#77ac30" # green
set style line 15 lt 1 ps 0.5 pt 7 lw 0.01 lc rgb "#4dbeee" # light-blue
set style line 16 lt 1 ps 0.5 pt 7 lw 0.01 lc rgb "#a2142f" # red

set border 3
set key opaque box


set xlabel "Time"
set xtics nomirror \
        ("10:00" -173, "11:00" 3427, "12:00" 7027, "13:00" 10627, "14:00" 14277, \
        "15:00" 17827, "16:00" 21427, "17:00" 25027, "18:00" 28627, "19:00" 32227, \
        "20:00" 35827, "21:00" 39427, "22:00" 43027)
#set xtics nomirror 1
set xrange[-1980:43216]
#set xrange[8520:8580]

set ylabel "Presence"
set ytics nomirror \
        ("Absent" 0.5, "Present" 1.5, "Absent" 2.5, "Present" 3.5, "Absent" 4.5, \
        "Present" 5.5, "Absent" 6.5, "Present" 7.5)
set yrange [0:8]

plot 'ground_truth_parsed.dat' u ($2):(($3==0?1:0)+6.5) w l ls 6 title "sarparis", \
    wearabouts_file u ($2):(($3==1?1:0)+6.5) w l ls 11 title "4901 guess", \
    wearabouts_file u ($2):(($3==2?1:0)+6.5) w l ls 13 title "4670 guess", \
    wearabouts_file u ($2):(($3==3?1:0)+6.5) w l ls 14 title "4916 guess", \
    wearabouts_file u ($2):(($3==4?1:0)+6.5) w l ls 15 title "4776 guess", \
    wearabouts_file u ($2):(($3==0?1:0)+6.5) w l ls 16 title "4908 guess", \
    \
    'ground_truth_parsed.dat' u ($2):(($6==0?1:0)+4.5) w l ls 6 title "adkinsjd", \
    wearabouts_file u ($2):(($6==1?1:0)+4.5) w l ls 11 notitle, \
    wearabouts_file u ($2):(($6==2?1:0)+4.5) w l ls 13 notitle, \
    wearabouts_file u ($2):(($6==3?1:0)+4.5) w l ls 14 notitle, \
    wearabouts_file u ($2):(($6==4?1:0)+4.5) w l ls 15 notitle, \
    wearabouts_file u ($2):(($6==0?1:0)+4.5) w l ls 16 notitle, \
    \
    'ground_truth_parsed.dat' u ($2):(($4==0?1:0)+2.5) w l ls 6 title "samkuo", \
    wearabouts_file u ($2):(($4==1?1:0)+2.5) w l ls 11 notitle, \
    wearabouts_file u ($2):(($4==2?1:0)+2.5) w l ls 13 notitle, \
    wearabouts_file u ($2):(($4==3?1:0)+2.5) w l ls 14 notitle, \
    wearabouts_file u ($2):(($4==4?1:0)+2.5) w l ls 15 notitle, \
    wearabouts_file u ($2):(($4==0?1:0)+2.5) w l ls 16 notitle, \
    \
    'ground_truth_parsed.dat' u ($2):(($7==0?1:0)+0.5) w l ls 6 title "brghena", \
    wearabouts_file u ($2):(($7==1?1:0)+0.5) w l ls 11 notitle, \
    wearabouts_file u ($2):(($7==2?1:0)+0.5) w l ls 13 notitle, \
    wearabouts_file u ($2):(($7==3?1:0)+0.5) w l ls 14 notitle, \
    wearabouts_file u ($2):(($7==4?1:0)+0.5) w l ls 15 notitle, \
    wearabouts_file u ($2):(($7==0?1:0)+0.5) w l ls 16 notitle, \
    \


