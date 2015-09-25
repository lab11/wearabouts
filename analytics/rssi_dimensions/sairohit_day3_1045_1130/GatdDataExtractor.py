#! /usr/bin/env python

import ConfigParser
import pymongo
import os
import json
import time

class GatdDataExtractor():
    db = ''
    def __init__(self):
        config_file_path = os.path.realpath("../gatd.config")
        config = ConfigParser.SafeConfigParser()
        config.read(config_file_path)
        host = config.get('mongo', 'host')
        port = int(config.get('mongo', 'port'))
        db_username = config.get('mongo', 'username')
        db_password = config.get('mongo', 'password')

        client = pymongo.MongoClient(host, port)
        self.db = client[config.get('mongo', "database")]
        self.db.authenticate(db_username, db_password)

    def extract(self, parameters={}, sort_parameters="", collection='formatted_data'):
        """
        Lets users run arbitrary find queries on the gatd database
        """
        c = self.db[collection]

        #print(str(c.index_information()))
        #exit(1)

        cursor = c.find(spec=parameters)

        return cursor

    def test(self, collection='formatted_data'):
        c = self.db[collection]

        return c.find({"profile_id":"4wbddZCSIj"})


start_time = 1441060063

scan_start_time = start_time + 142337 + 45*60
scan_end_time = scan_start_time + 45*60

if __name__ == "__main__":
    tq = {"$and": [
                {"profile_id":"ySYH83QLG2"},
                {"time": {"$gt": scan_start_time*1000}},
                {"time": {"$lt": scan_end_time*1000}},
                {"experimental": {"$exists": True}},
                #{"ble_addr": 'f9:97:1e:8b:e7:27'}, # brghena
                #{"ble_addr": 'c4:26:da:a4:72:c3'}, # samkuo
                #{"ble_addr": 'c8:ee:59:3a:a0:16'}, # azhen
                #{"ble_addr": 'ee:b7:8c:0d:8d:4d'}, # bradjc
                #{"ble_addr": 'db:eb:52:c7:90:74'}, # sdebruin
                {"ble_addr": 'ca:28:2b:08:f3:f7'}, # sairohit
            ]}
    #tq = {"profile_id":"ySYH83QLG2"}
    #tq = {"$and": [{"profile_id":"ySYH83QLG2"}, {"time": {"$gt": 1424458044000}}]}
    #tq = {"$and": [{"profile_id":"ySYH83QLG2"}, {"experimental": {"$exists": True}}]}
    #tq = {"$and": [{"profile_id":"ySYH83QLG2"}, {"scanner_macAddr":"1C:BA:8C:9B:BC:57"}]}
    #tq = {"profile_id":"ySYH83QLG2", "scanner_macAddr":"6C:EC:EB:9F:70:53"}
    
    # check for output problems before querying mongo
    if os.path.isfile("gatd_extract.dat"):
        print("ERROR: gatd_extract.dat already exists!")
        exit()

    test = GatdDataExtractor()
    print("Extracting data...")
    n = test.extract(parameters=tq)
    print("Data found!")

    outfile = open("gatd_extract.dat", 'w')
    record_num = 0
    for row in n:
        if (record_num % 1000) == 0:
            print("Currently at: " + time.strftime('%H:%M:%S', time.localtime(row['time']/1000)))

        record_num += 1
        outfile.write(str(row) + '\n')

