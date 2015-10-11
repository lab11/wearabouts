



rm -rf results/*

# full training
for i in 5 10 15 30 45 60 75 90 105 120 135 150 165 180 195 210 225 240 255 270 285 300; do
    for j in `seq $i -1 1`; do

# shorter training
#for i in 30 45 60 75 90 105 120; do
#    for j in `seq $((i/2)) -1 1`; do

# test an individual point
#for i in 75; do
#    for j in 12; do


        # Echo current test to user
        echo $i $j

        # wearabouts
        ./run_wearabouts.py $i $j

        # assemble into data file
        ./assemble_wearabouts_data.py

        # run stats
        ./run_stats.py $i $j
    done
done

echo "Roc curves complete!"

