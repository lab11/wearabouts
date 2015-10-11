set terminal postscript enhanced eps color font "Helvetica,14" size 12in,6in
set output "accuracy_with_errors.eps"

camera_data_file = "amalgamated_plottable.dat"
data_file = "../wearabouts/wearabouts_plottable.dat"
error_file = "../accuracy/results/assembled_errors_plottable.dat"

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
set style line 18 lt 1 ps 0.5 pt 7 lw 1 lc rgb "#0072bd" # blue

set border 15
set key opaque box at 40000,33.5

set xlabel "Time"
set xtics nomirror font "Helvetica,8" rotate \
("18:00" -1663, "19:00" 1937, "20:00" 5537, "21:00" 9137, "22:00" 12737, "23:00" 16337, "00:00" 19937, "01:00" 23537, "02:00" 27137, "03:00" 30737, "04:00" 34337, "05:00" 37937, "06:00" 41537, "07:00" 45137, "08:00" 48737, "09:00" 52337, "10:00" 55937, "11:00" 59537, "12:00" 63137, "13:00" 66737, "14:00" 70337, "15:00" 73937, "16:00" 77537, "17:00" 81137, "18:00" 84737, "19:00" 88337, "20:00" 91937, "21:00" 95537, "22:00" 99137, "23:00" 102737, "00:00" 106337, "01:00" 109937, "02:00" 113537, "03:00" 117137, "04:00" 120737, "05:00" 124337, "06:00" 127937, "07:00" 131537, "08:00" 135137, "09:00" 138737, "10:00" 142337, "11:00" 145937, "12:00" 149537, "13:00" 153137, "14:00" 156737, "15:00" 160337, "16:00" 163937, "17:00" 167537, "18:00" 171137, "19:00" 174737, "20:00" 178337, "21:00" 181937, "22:00" 185537, "23:00" 189137, "00:00" 192737, "01:00" 196337, "02:00" 199937, "03:00" 203537, "04:00" 207137, "05:00" 210737, "06:00" 214337, "07:00" 217937, "08:00" 221537, "09:00" 225137, "10:00" 228737, "11:00" 232337, "12:00" 235937, "13:00" 239537, "14:00" 243137, "15:00" 246737, "16:00" 250337, "17:00" 253937, "18:00" 257537, "19:00" 261137, "20:00" 264737)
set xrange[1937:261137]
set x2tics nomirror font "Helvetica,8" rotate \
("18:00" -1663, "19:00" 1937, "20:00" 5537, "21:00" 9137, "22:00" 12737, "23:00" 16337, "00:00" 19937, "01:00" 23537, "02:00" 27137, "03:00" 30737, "04:00" 34337, "05:00" 37937, "06:00" 41537, "07:00" 45137, "08:00" 48737, "09:00" 52337, "10:00" 55937, "11:00" 59537, "12:00" 63137, "13:00" 66737, "14:00" 70337, "15:00" 73937, "16:00" 77537, "17:00" 81137, "18:00" 84737, "19:00" 88337, "20:00" 91937, "21:00" 95537, "22:00" 99137, "23:00" 102737, "00:00" 106337, "01:00" 109937, "02:00" 113537, "03:00" 117137, "04:00" 120737, "05:00" 124337, "06:00" 127937, "07:00" 131537, "08:00" 135137, "09:00" 138737, "10:00" 142337, "11:00" 145937, "12:00" 149537, "13:00" 153137, "14:00" 156737, "15:00" 160337, "16:00" 163937, "17:00" 167537, "18:00" 171137, "19:00" 174737, "20:00" 178337, "21:00" 181937, "22:00" 185537, "23:00" 189137, "00:00" 192737, "01:00" 196337, "02:00" 199937, "03:00" 203537, "04:00" 207137, "05:00" 210737, "06:00" 214337, "07:00" 217937, "08:00" 221537, "09:00" 225137, "10:00" 228737, "11:00" 232337, "12:00" 235937, "13:00" 239537, "14:00" 243137, "15:00" 246737, "16:00" 250337, "17:00" 253937, "18:00" 257537, "19:00" 261137, "20:00" 264737)
set x2range[1937:261137]

set ylabel "Presence"
set ytics mirror \
        ("False Negative" 0, "False Positive" 2,  "Absent" 3,  "{/Helvetica-Bold brghena}"   4, "Present" 5, \
        "False Negative" 7,  "False Positive" 9,  "Absent" 10, "{/Helvetica-Bold samkuo}"   11, "Present" 12, \
        "False Negative" 14, "False Positive" 16, "Absent" 17, "{/Helvetica-Bold azhen}"    18, "Present" 19, \
        "False Negative" 21, "False Positive" 23, "Absent" 24, "{/Helvetica-Bold bradjc}"   25, "Present" 26, \
        "False Negative" 28, "False Positive" 30, "Absent" 31, "{/Helvetica-Bold sdebruin}" 32, "Present" 33)
#"False Negative" 35, "False Positive" 37, "Absent" 38,  "{/Helvetica-Bold sairohit}" 39, "Present" 40)
set yrange [-1:34]

plot \
    camera_data_file u ($2):(($4==0?1:-1)+4) w l ls 6 title "4908 Ground Truth", \
    data_file u ($2):(($4==0?1:-1)+4) w l ls 16 title "4908 Wearabouts", \
    error_file u ($2):(($4)+1) w l ls 18 title "Error", \
    \
    camera_data_file u ($2):(($3==0?1:-1)+11) w l ls 6 notitle, \
    data_file u ($2):(($3==0?1:-1)+11) w l ls 16 notitle, \
    error_file u ($2):(($3)+8) w l ls 18 notitle, \
    \
    camera_data_file u ($2):(($5==0?1:-1)+18) w l ls 6 notitle, \
    data_file u ($2):(($5==0?1:-1)+18) w l ls 16 notitle, \
    error_file u ($2):(($5)+15) w l ls 18 notitle, \
    \
    camera_data_file u ($2):(($6==0?1:-1)+25) w l ls 6 notitle, \
    data_file u ($2):(($6==0?1:-1)+25) w l ls 16 notitle, \
    error_file u ($2):(($6)+22) w l ls 18 notitle, \
    \
    camera_data_file u ($2):(($9==0?1:-1)+32) w l ls 6 notitle, \
    data_file u ($2):(($9==0?1:-1)+32) w l ls 16 notitle, \
    error_file u ($2):(($9)+29) w l ls 18 notitle, \
    \

