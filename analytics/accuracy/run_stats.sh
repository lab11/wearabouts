
#command="rssi_data_4908only_seen"
#command="rssi_data_4908only_threshold"
#command="rssi_data_allRooms_seen"
#command="rssi_data_allRooms_threshold"
#command="rssi_data_allRooms_average"
command='training_allRooms_average'

rm -f results.stats
rm -f results_*.stats

# full training
#for i in 5 10 15 30 45 60 75 90 105 120 135 150 165 180; do
#    for j in `seq $((i/2)) -1 1`; do
# shorter training
#for i in 30 45 60 75 90 105 120; do
#    for j in `seq $((i/2)) -1 1`; do
# test an individual point
for i in 60; do
    for j in 10; do
        echo $i $j
        # wearabouts
        ./parse_$command.py $i -150 True $j
        # threshold all rooms
        #./parse_$command.py $i -150 False
        mv $command.dat wb_rssi_data.dat
        # not training mode
        #./determine_accuracy.py 'wb_rssi_data.dat' ${i} ${j} -150 False
        # training mode
        for k in 'adkinsjd' 'samkuo' 'brghena'; do
            ./determine_accuracy.py 'wb_rssi_data.dat' ${i} ${j} -150 True ${k}
            cat accuracy.stats >> results_$k.stats
        done
    done
done


#for i in 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 20 25 30 35 40 45 50 55 60 120 180 240 300;
#for i in `seq 10 2 100`; do
#i=60
#for j in 12 13 14 15; do
#    for k in `seq -100 1 -75`; do
#        echo $i $j $k
#        ./parse_$command.py $i $k True $j
#        mv $command.dat wb_rssi_data.dat
#        ./determine_accuracy.py 'wb_rssi_data.dat' ${i} ${j} ${k}
#        cat accuracy.stats >> results.stats
#    done
#done
#
#i=100
#for j in 24 25 26 27 28; do
#    for k in `seq -100 1 -75`; do
#        echo $i $j $k
#        ./parse_$command.py $i $k True $j
#        mv $command.dat wb_rssi_data.dat
#        ./determine_accuracy.py 'wb_rssi_data.dat' ${i} ${j} ${k}
#        cat accuracy.stats >> results.stats
#    done
#done



#for i in `seq -90 -73`;
#do
#    echo $i
#    ./parse_$command.py 60 $i False
#    mv $command.dat wb_rssi_data.dat
#    ./determine_accuracy.py 'wb_rssi_data.dat' $i
#    cat accuracy.stats >> results.stats
#done
