from pymongo import MongoClient
from config import MONGODB, MONGODB_URI
from pymongo.errors import ConnectionFailure


class Database:
    def __init__(self, collection_name):
        client = MongoClient(MONGODB_URI)
        db = client[MONGODB]
        self.collection = db[collection_name]

    def get_comments(self, video_id):
        try:
            record = self.collection.find({"video_id": video_id})
            return list(record)
        except ConnectionFailure:
            print("Server not available")

    def insert_comments(self, comment_with_commenter_name):
        try:
            result = self.collection.insert_many(comment_with_commenter_name)
            return result.acknowledged
        except ConnectionFailure:
            print("Server not available")
