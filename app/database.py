import os
import psycopg2
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError, ConnectionFailure


class Mongodb:
    def __init__(self, collection_name):
        client = MongoClient(os.environ['MONGODB_URL'])
        db = client['youtube']
        self.collection = db[collection_name]

    def get_comments(self, video_id):
        try:
            record = self.collection.find({"video_id": video_id})
            return list(record)
        except ConnectionFailure:
            print("Server not available")
        except Exception as error:
            print(error)

    def insert_comments(self, comment_with_commenter_name):
        try:
            result = self.collection.insert_one(comment_with_commenter_name)
            print(f"Inserted Count: {result.inserted_count}")
            return result.acknowledged
        except ConnectionFailure:
            print("Server not available")
        except DuplicateKeyError:
            try:
                result = self.collection.delete_one({"video_id": comment_with_commenter_name["video_id"]})
                print(f"Deleted Count: {result.deleted_count}")
                result = self.collection.insert_one(comment_with_commenter_name)
                return result.acknowledged
            except Exception as error:
                print(error)
        except Exception as error:
            print(error)


class Postgresdb:
    def __init__(self, table_name):
        self.table_name = table_name
        self.connection = psycopg2.connect(os.environ['POSTGRES_URL'], sslmode='require')

    def select(self, channel_id):
        try:
            cursor = self.connection.cursor()
            cursor.execute(f"SELECT * FROM YOUTUBE WHERE CHANNELID='{channel_id}'")
            result = cursor.fetchall()
            return result
        except psycopg2.DatabaseError as error:
            print(error)
        finally:
            cursor.close()
            self.connection.close()

    def update(self, no_of_comments, video_id):
        try:
            cursor = self.connection.cursor()
            cursor.execute("UPDATE YOUTUBE SET COMMENTCOUNT=%s WHERE VIDEOID=%s", (no_of_comments, video_id))
            print(f"No of comments({no_of_comments}) updated for video id({video_id})!")
        except psycopg2.DatabaseError as error:
            print(error)
        except Exception as error:
            print(error)
        else:
            self.connection.commit()
            cursor.close()
        finally:
            self.connection.close()

    def insert(self, data):
        try:
            cursor = self.connection.cursor()
            # cursor.execute("DROP TABLE YOUTUBE")
            # cursor.execute("DELETE FROM YOUTUBE")
            # cursor.execute(
            #     "CREATE TABLE YOUTUBE(VideoId VARCHAR(50) PRIMARY KEY, ChannelId VARCHAR(100) NOT NULL,"
            #     "ChannelName VARCHAR(100), ChannelUrl VARCHAR(200) NOT NULL, Title VARCHAR(500) NOT NULL,"
            #     "VideoUrl VARCHAR(200) NOT NULL, ViewCount VARCHAR(50) NOT NULL, CommentCount INTEGER,"
            #     "ThumbnailUrl VARCHAR(500))")
            cursor.executemany("INSERT INTO YOUTUBE(VideoId, ChannelId, ChannelName, ChannelUrl, Title, VideoUrl,"
                               "ViewCount, CommentCount, ThumbnailUrl)"
                               "VALUES (%(VideoId)s, %(ChannelId)s, %(ChannelName)s, %(ChannelUrl)s,"
                               "%(Title)s, %(VideoUrl)s, %(ViewCount)s, %(CommentCount)s, %(ThumbnailUrl)s) "
                               "ON CONFLICT DO NOTHING", data)
            rowcount = cursor.rowcount
            print(f"{rowcount} Rows Successfully Inserted!")
        except psycopg2.DatabaseError as error:
            print(error)
        except Exception as error:
            print(error)
        else:
            self.connection.commit()
            cursor.close()
        finally:
            self.connection.close()
