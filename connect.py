import pymongo

# connect ke lokal
client = pymongo.MongoClient("mongodb://localhost:27017/")

db = client['db_sdgs']

sdgs_collection = db['data_kemiskinan']