import os
import logging
import traceback
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS, cross_origin
from .database import Mongodb, Postgresdb
from .youtube_search import YoutubeSearch
from .youtube_comment import YoutubeComment
from .youtube_video_download import YoutubeVideo
# from .google_drive_video_upload import GoogleDrives

# Define the WSGI application object
app = Flask(__name__)

# Configurations
app.config.from_object('config')
# logging.basicConfig(filename='app/logs/app.log', level=logging.DEBUG,
#                     format=f'%(asctime)s %(levelname)s %(name)s %(threadName)s : %(message)s')


@app.route('/')
@cross_origin()
def index():
    return render_template("index.html"), 200


@app.route("/content", methods=["POST"])
@cross_origin()
def content():
    if request.method == "POST":
        try:
            data = list()
            youtube_data = list()
            youtube_search_object = YoutubeSearch()
            youtube_comment_object = YoutubeComment()
            search_text = request.form['content'].replace(" ", "")
            # search_limit = request.form['search_limit']
            channel_id = youtube_search_object.get_channel_id(query=search_text)
            channel_name = youtube_search_object.get_channel_name(query=search_text)
            videos = youtube_search_object.get_channel(channel_id=channel_id)
            # videos = youtube_search_object.get_channel(channel_id=channel_id, limit=int(search_limit))

            for video in videos:
                video_id = youtube_search_object.get_value(video, ["videoId"])
                title = youtube_search_object.get_value(video, ["title", "runs", 0, "text"])
                video_url = f"https://www.youtube.com/watch?v={video_id}"
                view_count_text = youtube_search_object.get_value(video, ["viewCountText", "simpleText"])
                rich_thumbnail_url = youtube_search_object.get_value(video, ["richThumbnail", "movingThumbnailRenderer",
                                                                             "movingThumbnailDetails", "thumbnails", 0,
                                                                             "url"])

                # no_of_comments = 10     # FOR DEBUG
                no_of_comments = youtube_comment_object.get_comments_details(video_id)

                save_data = {"VideoId": video_id, "ChannelId": channel_id, "ChannelName": channel_name,
                             "ChannelUrl": f"https://www.youtube.com/channel/{channel_id}", "Title": title,
                             "VideoUrl": video_url, "ViewCount": view_count_text.split()[0] if view_count_text is not None else 0,
                             "CommentCount": no_of_comments, "ThumbnailUrl": rich_thumbnail_url}

                # print(save_data)
                render_data = {"video_id": video_id, "title": title, "videoUrl": video_url,
                               "viewCountText": view_count_text, "no_of_comments": no_of_comments,
                               "richThumbnailUrl": rich_thumbnail_url}
                data.append(render_data)
                youtube_data.append(save_data)
            # YoutubeVideo.download(data)
            # GoogleDrives.upload()
            Postgresdb("youtube").insert(youtube_data)
            print(Postgresdb("youtube").select(channel_id))
            return render_template('results.html', data=data), 200
        except Exception as e:
            print('The Exception message is: ', e)
            traceback.print_exc()
            return 'something is wrong', 500
    else:
        return render_template("index.html"), 200


@app.route("/comments/<video_id>")
@cross_origin()
def comments(video_id):
    try:
        data = Mongodb("comments").get_comments(video_id)
    except Exception as e:
        print('The Exception message is: ', e)
        traceback.print_exc()
        return 'something is wrong', 500
    return render_template("comments.html", data=data), 200


@app.route("/cleanup/<id>")
@cross_origin()
def cleanup(id):
    try:
        if id == "101":
            for f in os.listdir("app/download"):
                os.remove(os.path.join("app/download", f))
                print(f"Deleted - {f}")
    except Exception as e:
        print('The Exception message is: ', e)
        traceback.print_exc()
        return 'something is wrong', 500
    return "OK", 200


# Sample HTTP error handling
@app.errorhandler(404)
@cross_origin()
def not_found(error):
    return render_template('404.html'), 404
