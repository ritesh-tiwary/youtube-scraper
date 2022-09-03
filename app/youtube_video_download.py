from pytube import YouTube


class YoutubeVideo:
    def __init__(self, video_url):
        self.videoUrl = video_url

    def download(self):
        try:
            video = YouTube(self.videoUrl)
        except VideoUnavailable:
            print(f"Video {self.videoUrl} is unavaialable, skipping.")
        else:
            print(f"Downloading - {video.title}...")
            video.streams.filter(progressive=True, file_extension="mp4").order_by("resolution").desc().first()\
                .download("app/download")
                
