set terminal postscript enhanced eps color font "Helvetica,14" size 12in,6in
set output "wearabouts_data.eps"

camera_data_file = "../camera/camera_plottable.dat"
#camera_data_file = "../rfid/rfid_plottable.dat"
data_file = "wearabouts_plottable.dat"

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

set xlabel "Time"
set xtics nomirror font "Helvetica,8" rotate \
("18:00" -1663, "19:00" 1937, "20:00" 5537, "21:00" 9137, "22:00" 12737, "23:00" 16337, "00:00" 19937, "01:00" 23537, "02:00" 27137, "03:00" 30737, "04:00" 34337, "05:00" 37937, "06:00" 41537, "07:00" 45137, "08:00" 48737, "09:00" 52337, "10:00" 55937, "11:00" 59537, "12:00" 63137, "13:00" 66737, "14:00" 70337, "15:00" 73937, "16:00" 77537, "17:00" 81137, "18:00" 84737, "19:00" 88337, "20:00" 91937, "21:00" 95537, "22:00" 99137, "23:00" 102737, "00:00" 106337, "01:00" 109937, "02:00" 113537, "03:00" 117137, "04:00" 120737, "05:00" 124337, "06:00" 127937, "07:00" 131537, "08:00" 135137, "09:00" 138737, "10:00" 142337, "11:00" 145937, "12:00" 149537, "13:00" 153137, "14:00" 156737, "15:00" 160337, "16:00" 163937, "17:00" 167537, "18:00" 171137, "19:00" 174737, "20:00" 178337, "21:00" 181937, "22:00" 185537, "23:00" 189137, "00:00" 192737, "01:00" 196337, "02:00" 199937, "03:00" 203537, "04:00" 207137, "05:00" 210737, "06:00" 214337, "07:00" 217937, "08:00" 221537, "09:00" 225137, "10:00" 228737, "11:00" 232337, "12:00" 235937, "13:00" 239537, "14:00" 243137, "15:00" 246737, "16:00" 250337, "17:00" 253937, "18:00" 257537, "19:00" 261137, "20:00" 264737)
set xrange[-1663:261137]

set ylabel "Presence"
set ytics nomirror \
        ("Absent" 0.5, "brghena" 1, "Present" 1.5, \
        "Absent" 2.5, "samkuo" 3, "Present" 3.5, \
        "Absent" 4.5, "azhen" 5, "Present" 5.5, \
        "Absent" 6.5, "bradjc" 7, "Present" 7.5, \
        "Absent" 8.5, "sdebruin" 9, "Present" 9.5)
set yrange [0:10]

#plot data_file u ($2):(($4==0?1:0)+0.5) w l ls 16 title "4908 camera", \
#    \
#    data_file u ($2):(($3==0?1:0)+2.5) w l ls 16 notitle, \
#    \
#    data_file u ($2):(($5==0?1:0)+4.5) w l ls 16 notitle, \
#    \
#    data_file u ($2):(($6==0?1:0)+6.5) w l ls 16 notitle, \
#    \
#    data_file u ($2):(($9==0?1:0)+8.5) w l ls 16 notitle, \
#    \


plot \
    camera_data_file u ($2):(($4==0?1:0)+0.5) w l ls 6 title "4908 camera", \
    data_file u ($2):(($4==0?1:0)+0.5) w l ls 16 title "4908 wearabouts", \
    \
    camera_data_file u ($2):(($3==0?1:0)+2.5) w l ls 6 notitle, \
    data_file u ($2):(($3==0?1:0)+2.5) w l ls 16 notitle, \
    \
    camera_data_file u ($2):(($5==0?1:0)+4.5) w l ls 6 notitle, \
    data_file u ($2):(($5==0?1:0)+4.5) w l ls 16 notitle, \
    \
    camera_data_file u ($2):(($6==0?1:0)+6.5) w l ls 6 notitle, \
    data_file u ($2):(($6==0?1:0)+6.5) w l ls 16 notitle, \
    \
    camera_data_file u ($2):(($9==0?1:0)+8.5) w l ls 6 notitle, \
    data_file u ($2):(($9==0?1:0)+8.5) w l ls 16 notitle, \
    \

#plot \
#    camera_data_file u ($2):(($4==0?1:0)+0.5) w l ls 6 title "4908 camera", \
#    data_file u ($2):(($4==0?1:0)+0.5) w l ls 16 title "4908 wearabouts", \
#    data_file u ($2):(($4==1?1:0)+0.5) w l ls 11 title "4901 wearabouts", \
#    data_file u ($2):(($4==2?1:0)+0.5) w l ls 13 title "4670 wearabouts", \
#    \
#    camera_data_file u ($2):(($3==0?1:0)+2.5) w l ls 6 title "4908 camera", \
#    data_file u ($2):(($3==0?1:0)+2.5) w l ls 16 notitle, \
#    data_file u ($2):(($3==1?1:0)+2.5) w l ls 11 notitle, \
#    data_file u ($2):(($3==2?1:0)+2.5) w l ls 13 notitle, \
#    \
#    camera_data_file u ($2):(($5==0?1:0)+4.5) w l ls 6 title "4908 camera", \
#    data_file u ($2):(($5==0?1:0)+4.5) w l ls 16 notitle, \
#    data_file u ($2):(($5==1?1:0)+4.5) w l ls 11 notitle, \
#    data_file u ($2):(($5==2?1:0)+4.5) w l ls 13 notitle, \
#    \
#    camera_data_file u ($2):(($6==0?1:0)+6.5) w l ls 6 title "4908 camera", \
#    data_file u ($2):(($6==0?1:0)+6.5) w l ls 16 notitle, \
#    data_file u ($2):(($6==1?1:0)+6.5) w l ls 11 notitle, \
#    data_file u ($2):(($6==2?1:0)+6.5) w l ls 13 notitle, \
#    \
#    camera_data_file u ($2):(($9==0?1:0)+8.5) w l ls 6 title "4908 camera", \
#    data_file u ($2):(($9==0?1:0)+8.5) w l ls 16 notitle, \
#    data_file u ($2):(($9==1?1:0)+8.5) w l ls 11 notitle, \
#    data_file u ($2):(($9==2?1:0)+8.5) w l ls 13 notitle, \
#    \




#plot 'ground_truth_parsed.dat' u ($2):(($3==0?1:0)+6.5) w l ls 6 title "ground truth", \
#    data_file u ($2):(($3==0?1:0)+6.5) w l ls 16 title "4908 wearabouts", \
#    data_file u ($2):(($3==1?1:0)+6.5) w l ls 11 title "4901 wearabouts", \
#    data_file u ($2):(($3==2?1:0)+6.5) w l ls 13 title "4670 wearabouts", \
#    data_file u ($2):(($3==3?1:0)+6.5) w l ls 14 title "4916 wearabouts", \
#    data_file u ($2):(($3==4?1:0)+6.5) w l ls 15 title "4776 wearabouts", \
#    \
#    'ground_truth_parsed.dat' u ($2):(($6==0?1:0)+4.5) w l ls 6 notitle, \
#    data_file u ($2):(($6==0?1:0)+4.5) w l ls 16 notitle, \
#    data_file u ($2):(($6==1?1:0)+4.5) w l ls 11 notitle, \
#    data_file u ($2):(($6==2?1:0)+4.5) w l ls 13 notitle, \
#    data_file u ($2):(($6==3?1:0)+4.5) w l ls 14 notitle, \
#    data_file u ($2):(($6==4?1:0)+4.5) w l ls 15 notitle, \
#    \
#    'ground_truth_parsed.dat' u ($2):(($4==0?1:0)+2.5) w l ls 6 notitle, \
#    data_file u ($2):(($4==0?1:0)+2.5) w l ls 16 notitle, \
#    data_file u ($2):(($4==1?1:0)+2.5) w l ls 11 notitle, \
#    data_file u ($2):(($4==2?1:0)+2.5) w l ls 13 notitle, \
#    data_file u ($2):(($4==3?1:0)+2.5) w l ls 14 notitle, \
#    data_file u ($2):(($4==4?1:0)+2.5) w l ls 15 notitle, \
#    \
#    'ground_truth_parsed.dat' u ($2):(($7==0?1:0)+0.5) w l ls 6 notitle, \
#    data_file u ($2):(($7==0?1:0)+0.5) w l ls 16 notitle, \
#    data_file u ($2):(($7==1?1:0)+0.5) w l ls 11 notitle, \
#    data_file u ($2):(($7==2?1:0)+0.5) w l ls 13 notitle, \
#    data_file u ($2):(($7==3?1:0)+0.5) w l ls 14 notitle, \
#    data_file u ($2):(($7==4?1:0)+0.5) w l ls 15 notitle, \
#    \


