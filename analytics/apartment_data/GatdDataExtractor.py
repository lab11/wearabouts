import ConfigParser
import pymongo
import os
import json

class GatdDataExtractor():
    db = ''
    def __init__(self):
        config_file_path = os.path.realpath("gatd.config")
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


if __name__ == "__main__":
    tq = {"$and": [
                {"profile_id":"ySYH83QLG2"},
                {"time": {"$gt": 1424458044000}},
                {"experimental": {"$exists": True}},
                {"scanner_macAddr": "6C:EC:EB:9F:70:53"}
            ]}
    #tq = {"profile_id":"ySYH83QLG2"}
    #tq = {"$and": [{"profile_id":"ySYH83QLG2"}, {"time": {"$gt": 1424458044000}}]}
    #tq = {"$and": [{"profile_id":"ySYH83QLG2"}, {"experimental": {"$exists": True}}]}
    #tq = {"$and": [{"profile_id":"ySYH83QLG2"}, {"scanner_macAddr":"1C:BA:8C:9B:BC:57"}]}
    #tq = {"profile_id":"ySYH83QLG2", "scanner_macAddr":"6C:EC:EB:9F:70:53"}
    test = GatdDataExtractor()
    n = test.extract(parameters=tq)
    for row in n:
        print row

