import os
import traceback
from pytube import YouTube
from google.cloud import storage
from google.oauth2 import service_account
from concurrent.futures import ThreadPoolExecutor


class YoutubeVideo:
    def __init__(self, videos: list = None):
        self.videos = videos
        self.credentials = service_account.Credentials.from_service_account_file(os.environ["FILE_NAME"])

    def download_video(self, video):
        try:
            file_name = f"{video['VideoId']}.mp4"
            video = YouTube(video["VideoUrl"])
        except VideoUnavailable:
            print(f"Video {video_url} is unavaialable, skipping.")
        except Exception as e:
            print('The Exception message is: Download failed - ', e)
            traceback.print_exc()
        else:
            print(f"Downloading - {video.title}...")
            video.streams.filter(progressive=True, file_extension="mp4").order_by("resolution").desc().first() \
                .download("app/download", filename=file_name)
            print(f'File "{video.title}" downloaded successfully.')
            self.upload_blob(file_name)

    def download(self):
        try:
            with ThreadPoolExecutor(max_workers=len(self.videos)) as executor:
                executor.map(self.download_video, [video for video in self.videos])
        except Exception as e:
            print('The Exception message is: Download failed - ', e)
            traceback.print_exc()

    def upload_blob(self, source_file_name, bucket_name: str = "staging.back-end-app-67f2d.appspot.com"):
        """
        Uploads a file to the google cloud bucket.
        Returns : Name's of the file uploaded to Google Cloud Bucket
        """
        try:
            print(f"Uploading - {source_file_name}...")
            destination_blob_name = f"youtube_video/{source_file_name}"
            source_file_name = f"app/download/{source_file_name}"
            storage_client = storage.Client(credentials=self.credentials)
            bucket = storage_client.bucket(bucket_name)
            blob = bucket.blob(destination_blob_name)
            blob.upload_from_filename(source_file_name)
            os.remove(source_file_name)
            print(f"File {source_file_name} uploaded to {destination_blob_name}.")
        except Exception as e:
            print('The Exception message is: Upload failed - ', e)
            traceback.print_exc()

    def download_blob(self, video_id):
        """
        Uploads a file to the google cloud bucket.
        Returns : Name's of the file uploaded to Google Cloud Bucket
        """
        try:
            print(f"Downloading - {video_id}.mp4")
            bucket_name: str = "staging.back-end-app-67f2d.appspot.com"
            source_file_name = f"youtube_video/{video_id}.mp4"
            destination_file_name = f"app/download/{video_id}.mp4"
            storage_client = storage.Client(credentials=self.credentials)
            bucket = storage_client.bucket(bucket_name)
            blob = bucket.blob(source_file_name)
            blob.download_to_filename(destination_file_name)
            print(f"File {video_id}.mp4 downloaded to {destination_file_name}.")
        except Exception as e:
            print('The Exception message is: Upload failed - ', e)
            traceback.print_exc()

    def upload(self):
        try:
            with ThreadPoolExecutor(max_workers=len(self.videos)) as executor:
                executor.map(self.upload_blob, [f for f in os.listdir("app/download")])
        except Exception as e:
            print('The Exception message is: Upload failed - ', e)
            traceback.print_exc()
