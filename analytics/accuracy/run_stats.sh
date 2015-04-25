

#command="rssi_data_4908only_seen"
command="rssi_data_allRooms_seen"
#command="rssi_data_allRooms_threshold"

rm -f results.stats

for i in 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 20 25 30 35 40 45 50 55 60 120 180 240 300;
do
    echo $i
    ./parse_$command.py $i
    mv $command.dat wb_rssi_data.dat
    ./determine_accuracy.py $i
    cat accuracy.stats >> results.stats
done
