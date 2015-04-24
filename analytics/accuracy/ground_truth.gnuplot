set terminal postscript enhanced eps color font "Helvetica,14" size 6in,6in
set output "ground_truth.eps"

set style line 1 lt 1 ps 0.5 pt 7 lw 0.5 lc rgb "#0072bd" # blue
set style line 2 lt 1 ps 0.5 pt 7 lw 0.5 lc rgb "#d95319" # orange
set style line 3 lt 1 ps 0.5 pt 7 lw 0.5 lc rgb "#7e2f8e" # purple
set style line 4 lt 1 ps 0.5 pt 7 lw 0.5 lc rgb "#77ac30" # green
set style line 5 lt 1 ps 0.5 pt 7 lw 0.5 lc rgb "#4dbeee" # light-blue
set style line 6 lt 1 ps 0.5 pt 7 lw 0.5 lc rgb "#a2142f" # red

set border 3
set key opaque box


set xlabel "Time"
set xtics nomirror \
        ("10:00" -173, "11:00" 3427, "12:00" 7027, "13:00" 10627, "14:00" 14277, \
        "15:00" 17827, "16:00" 21427, "17:00" 25027, "18:00" 28627, "19:00" 32227, \
        "20:00" 35827, "21:00" 39427, "22:00" 43027)
set xrange[-173:43216]

set ylabel "Presence"
set ytics nomirror \
        ("Absent" 0.5, "Present" 1.5, "Absent" 2.5, "Present" 3.5, "Absent" 4.5, \
        "Present" 5.5, "Absent" 6.5, "Present" 7.5, "Absent" 8.5, "Present" 9.5, \
        "Absent" 10.5, "Present" 11.5)
set yrange [0:12]

plot 'ground_truth_parsed.dat' u ($2):($3+10.5) w l ls 1 title "sarparis", \
    'ground_truth_parsed.dat' u ($2):($5+8.5) w l ls 3 title "nealjack", \
    'ground_truth_parsed.dat' u ($2):($8+6.5) w l ls 6 title "bpkempke", \
    'ground_truth_parsed.dat' u ($2):($6+4.5) w l ls 4 title "adkinsjd", \
    'ground_truth_parsed.dat' u ($2):($4+2.5) w l ls 2 title "samkuo", \
    'ground_truth_parsed.dat' u ($2):($7+0.5) w l ls 5 title "brghena", \


