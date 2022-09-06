import traceback
from pytube import YouTube
from concurrent.futures import ThreadPoolExecutor


class YoutubeVideo:
    @staticmethod
    def download_video(video_url):
        try:
            video = YouTube(video_url)
        except VideoUnavailable:
            print(f"Video {video_url} is unavaialable, skipping.")
        except Exception as e:
            print('The Exception message is: Download failed - ', e)
            traceback.print_exc()
        else:
            print(f"Downloading - {video.title}...")
            video.streams.filter(progressive=True, file_extension="mp4").order_by("resolution").desc().first() \
                .download("app/download")
            print(f"Downloaded - {video.title}")

    @staticmethod
    def download(videos):
        try:
            with ThreadPoolExecutor(max_workers=len(videos)) as executor:
                executor.map(YoutubeVideo.download_video, [video["videoUrl"] for video in videos])
        except Exception as e:
            print('The Exception message is: Download failed - ', e)
            traceback.print_exc()
