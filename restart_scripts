#!/bin/bash
# cause sometimes you don't want to do things elegantly and you just need a big stick
wearabouts_dir="/home/brghena/wearabouts/"
accessors_dir="/home/brghena/accessors/"

# grab list of current screens
screen_list=$(sudo screen -list)

# wearabouts scripts
if [ -n "$wearabouts_dir" ]
then
    cd $wearabouts_dir

    # check for bleScanner
    if echo $screen_list | grep -q "bleScanner"
    then
        echo "bleScanner already running"
    else
        cd bleScanner/
        sudo screen -dmS bleScanner python bleScanner.py --rabbit
        echo "Started bleScanner"
        cd ../
    fi

    # check for controller
    if echo $screen_list | grep -q "wearabouts"
    then
        echo "wearabouts already running"
    else
        cd controller/
        sudo screen -dmS wearaboutsController python wearabouts.py --rabbit
        echo "Started wearabouts"
        cd ../
    fi

    # check for eventGenerator
    if echo $screen_list | grep -q "eventGenerator"
    then
        echo "eventGenerator already running"
    else
        cd events/
        sudo screen -dmS eventGenerator python eventGenerator.py --rabbit
        echo "Started eventGenerator"
        cd ../
    fi

    # check for GATD forwarder
    if echo $screen_list | grep -q "gatdForwarder"
    then
        echo "gatdForwarder already running"
    else
        cd gatd/
        sudo screen -dmS gatdForwarder python gatdForwarder.py --rabbit
        echo "Started gatdForwarder"
        cd ../
    fi
fi

if [ -n "$accessors_dir" ]
then
    cd $accessors_dir

    # check for 4908 lighting control
    if echo $screen_list | grep -q "4908lighting"
    then
        echo "4908lighting already running"
    else
        cd applications/central/
        sudo screen -dmS 4908lighting forever --minUptime 1000 4908lighting.js 
        echo "Started 4908lighting"
        cd ../
    fi
fi

