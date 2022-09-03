import json
import time
import requests
from typing_extensions import Literal
from typing import Generator, List, Union


class YoutubeSearch:
    def get_channel(
            self,
            channel_id: str = None,
            channel_url: str = None,
            limit: int = None,
            sleep: int = 1,
            sort_by: Literal["newest", "oldest", "popular"] = "newest",
            ) -> Generator[dict, None, None]:

        sort_by_map = {"newest": "dd", "oldest": "da", "popular": "p"}
        url = "{url}/videos?view=0&sort={sort_by}&flow=grid".format(
            url=channel_url or f"https://www.youtube.com/channel/{channel_id}",
            sort_by=sort_by_map[sort_by],
        )
        api_endpoint = "https://www.youtube.com/youtubei/v1/browse"
        videos = self.get_videos(url, api_endpoint, "gridVideoRenderer", limit, sleep)
        for video in videos:
            yield video

    def get_search(
            self,
            query: str,
            limit: int = 1,
            sleep: int = 1,
            sort_by: Literal["relevance", "upload_date", "view_count", "rating"] = "relevance",
            results_type: Literal["video", "channel", "playlist", "movie"] = "channel",
            ) -> Generator[dict, None, None]:

        sort_by_map = {
            "relevance": "A",
            "upload_date": "I",
            "view_count": "M",
            "rating": "E",
        }

        results_type_map = {
            "video": ["B", "videoRenderer"],
            "channel": ["C", "channelRenderer"],
            "playlist": ["D", "playlistRenderer"],
            "movie": ["E", "videoRenderer"],
        }

        param_string = f"CA{sort_by_map[sort_by]}SAhA{results_type_map[results_type][0]}"
        url = f"https://www.youtube.com/results?search_query={query}&sp={param_string}"
        api_endpoint = "https://www.youtube.com/youtubei/v1/search"
        videos = self.get_videos(
            url, api_endpoint, results_type_map[results_type][1], limit, sleep
        )
        for video in videos:
            yield video

    def get_videos(
            self,
            url: str, api_endpoint: str, selector: str, limit: int, sleep: int
            ) -> Generator[dict, None, None]:

        session = requests.Session()
        session.headers[
            "User-Agent"
        ] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.101 Safari/537.36"
        is_first = True
        quit = False
        count = 0
        while True:
            if is_first:
                html = self.get_initial_data(session, url)
                client = json.loads(
                    self.get_json_from_html(html, "INNERTUBE_CONTEXT", 2, '"}},') + '"}}'
                )["client"]
                api_key = self.get_json_from_html(html, "innertubeApiKey", 3)
                session.headers["X-YouTube-Client-Name"] = "1"
                session.headers["X-YouTube-Client-Version"] = client["clientVersion"]
                data = json.loads(
                    self.get_json_from_html(html, "var ytInitialData = ", 0, "};") + "}"
                )
                next_data = self.get_next_data(data)
                is_first = False
            else:
                data = get_ajax_data(session, api_endpoint, api_key, next_data, client)
                next_data = self.get_next_data(data)
            for result in self.get_videos_items(data, selector):
                try:
                    count += 1
                    yield result
                    if count == limit:
                        quit = True
                        break
                except GeneratorExit:
                    quit = True
                    break

            if not next_data or quit:
                break

            time.sleep(sleep)

        session.close()

    def get_initial_data(self, session: requests.Session, url: str) -> str:
        session.cookies.set("CONSENT", "YES+cb", domain=".youtube.com")
        response = session.get(url)

        html = response.text
        return html

    def get_ajax_data(
            self,
            session: requests.Session,
            api_endpoint: str,
            api_key: str,
            next_data: dict,
            client: dict,
            ) -> dict:
        data = {
            "context": {"clickTracking": next_data["click_params"], "client": client},
            "continuation": next_data["token"],
        }
        response = session.post(api_endpoint, params={"key": api_key}, json=data)
        return response.json()

    def get_json_from_html(self, html: str, key: str, num_chars: int = 2, stop: str = '"') -> str:
        pos_begin = html.find(key) + len(key) + num_chars
        pos_end = html.find(stop, pos_begin)
        return html[pos_begin:pos_end]

    def get_next_data(self, data: dict) -> dict:
        raw_next_data = next(self.search_dict(data, "continuationEndpoint"), None)
        if not raw_next_data:
            return None
        next_data = {
            "token": raw_next_data["continuationCommand"]["token"],
            "click_params": {"clickTrackingParams": raw_next_data["clickTrackingParams"]},
        }

        return next_data

    def search_dict(self, partial: dict, search_key: str) -> Generator[dict, None, None]:
        stack = [partial]
        while stack:
            current_item = stack.pop(0)
            if isinstance(current_item, dict):
                for key, value in current_item.items():
                    if key == search_key:
                        yield value
                    else:
                        stack.append(value)
            elif isinstance(current_item, list):
                for value in current_item:
                    stack.append(value)

    def get_videos_items(self, data: dict, selector: str) -> Generator[dict, None, None]:
        return self.search_dict(data, selector)

    def get_value(self, source: dict, path: List[str]) -> Union[str, int, dict, None]:
        value = source
        for key in path:
            if type(key) is str:
                if key in value.keys():
                    value = value[key]
                else:
                    value = None
                    break
            elif type(key) is int:
                if len(value) != 0:
                    value = value[key]
                else:
                    value = None
                    break
        return value

    def get_channel_id(self, query: str = None) -> str:
        channel = self.get_search(query=query)
        channel_id = self.get_value(next(channel), ["channelId"])
        return channel_id

    def get_channel_name(self, query: str = None) -> str:
        channel = self.get_search(query=query)
        channel_name = self.get_value(next(channel), ["title", "simpleText"])
        return channel_name
        
