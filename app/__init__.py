from flask import Flask, render_template, request, jsonify
from flask_cors import CORS, cross_origin
import traceback
from .youtube_search import YoutubeSearch
from .youtube_comment import YoutubeComment
from .youtube_video_download import YoutubeVideo

# Define the WSGI application object
app = Flask(__name__)

# Configurations
app.config.from_object('config')

SEARCH_LIMIT = 1


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
            youtube_search_object = YoutubeSearch()
            youtube_comment_object = YoutubeComment()
            search_text = request.form['content'].replace(" ", "")
            channel_id = youtube_search_object.get_channel_id(query=search_text)
            videos = youtube_search_object.get_channel(channel_id=channel_id, limit=SEARCH_LIMIT)

            for video in videos:
                video_id = youtube_search_object.get_value(video, ["videoId"])
                title = youtube_search_object.get_value(video, ["title", "runs", 0, "text"])
                video_url = f"https://www.youtube.com/watch?v={video_id}"
                view_count_text = youtube_search_object.get_value(video, ["viewCountText", "simpleText"])
                rich_thumbnail_url = youtube_search_object.get_value(video, ["richThumbnail", "movingThumbnailRenderer",
                                                                             "movingThumbnailDetails", "thumbnails", 0,
                                                                             "url"])

                comment_with_commenter_name = youtube_comment_object.get_comments_details(video_id)
                no_of_comments = len(comment_with_commenter_name)
                YoutubeVideo(video_url).download()

                # print(video_id)
                # print(channel_id)
                # print(title)
                # print(video_url)
                # print(view_count_text)
                # print(rich_thumbnail_url)
                # print(no_of_comments)
                # print(comment_with_commenter_name)
                # print()
                save_data = {"VideoId": video_id, "ChannelId": channel_id, "Title": title,
                             "VideoUrl": video_url, "ViewCount": view_count_text.split()[0],
                             "CommentCount": no_of_comments, "ThumbnailUrl": rich_thumbnail_url}

                # print(save_data)
                render_data = {"title": title, "videoUrl": video_url, "viewCountText": view_count_text,
                               "no_of_comments": no_of_comments, "richThumbnailUrl": rich_thumbnail_url}
                data.append(render_data)
            return render_template('results.html', data=data), 200
        except Exception as e:
            print('The Exception message is: ', e)
            traceback.print_exc()
            return 'something is wrong'
    else:
        return render_template("index.html"), 200


# Sample HTTP error handling
@app.errorhandler(404)
@cross_origin()
def not_found(error):
    return render_template('404.html'), 404
    