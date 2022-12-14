from __future__ import print_function

import json
import re
import time
import dateparser
import requests

import traceback
from .database import Mongodb, Postgresdb
from concurrent.futures import ThreadPoolExecutor

SORT_BY_POPULAR = 0
SORT_BY_RECENT = 1
YOUTUBE_VIDEO_URL = 'https://www.youtube.com/watch?v={video_id}'

YT_CFG_RE = r'ytcfg\.set\s*\(\s*({.+?})\s*\)\s*;'
YT_INITIAL_DATA_RE = r'(?:window\s*\[\s*["\']ytInitialData["\']\s*\]|ytInitialData)\s*=\s*({.+?})\s*;\s*(?:var\s+meta|</script|\n)'
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.130 Safari/537.36'


class YoutubeComment:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers['User-Agent'] = USER_AGENT

    def ajax_request(self, endpoint, ytcfg, retries=5, sleep=20):
        url = 'https://www.youtube.com' + endpoint['commandMetadata']['webCommandMetadata']['apiUrl']

        data = {'context': ytcfg['INNERTUBE_CONTEXT'],
                'continuation': endpoint['continuationCommand']['token']}

        for _ in range(retries):
            response = self.session.post(url, params={'key': ytcfg['INNERTUBE_API_KEY']}, json=data)
            if response.status_code == 200:
                return response.json()
            if response.status_code in [403, 413]:
                return {}
            else:
                time.sleep(sleep)

    def get_comments(self, video_id, *args, **kwargs):
        return self.get_comments_from_url(YOUTUBE_VIDEO_URL.format(video_id=video_id), *args, **kwargs)

    def get_comments_from_url(self, youtube_url, sort_by=SORT_BY_RECENT, language=None, sleep=.1):
        response = self.session.get(youtube_url)

        if 'uxe=' in response.request.url:
            self.session.cookies.set('CONSENT', 'YES+cb', domain='.youtube.com')
            response = self.session.get(youtube_url)

        html = response.text
        ytcfg = json.loads(self.regex_search(html, YT_CFG_RE, default=''))
        if not ytcfg:
            return  # Unable to extract configuration
        if language:
            ytcfg['INNERTUBE_CONTEXT']['client']['hl'] = language

        data = json.loads(self.regex_search(html, YT_INITIAL_DATA_RE, default=''))

        section = next(self.search_dict(data['contents'], 'itemSectionRenderer'), None)
        renderer = next(self.search_dict(section, 'continuationItemRenderer'), None) if section else None
        if not renderer:
            # Comments disabled?
            return

        needs_sorting = sort_by != SORT_BY_POPULAR
        continuations = [renderer['continuationEndpoint']]
        while continuations:
            continuation = continuations.pop()
            response = self.ajax_request(continuation, ytcfg)

            if not response:
                break

            error = next(self.search_dict(response, 'externalErrorMessage'), None)
            if error:
                raise RuntimeError('Error returned from server: ' + error)

            if needs_sorting:
                sort_menu = next(self.search_dict(response, 'sortFilterSubMenuRenderer'), {}).get('subMenuItems', [])
                if sort_by < len(sort_menu):
                    continuations = [sort_menu[sort_by]['serviceEndpoint']]
                    needs_sorting = False
                    continue
                raise RuntimeError('Failed to set sorting')

            actions = list(self.search_dict(response, 'reloadContinuationItemsCommand')) + \
                list(self.search_dict(response, 'appendContinuationItemsAction'))
            for action in actions:
                for item in action.get('continuationItems', []):
                    if action['targetId'] == 'comments-section':
                        # Process continuations for comments and replies.
                        continuations[:0] = [ep for ep in self.search_dict(item, 'continuationEndpoint')]
                    if action['targetId'].startswith('comment-replies-item') and 'continuationItemRenderer' in item:
                        # Process the 'Show more replies' button
                        continuations.append(next(self.search_dict(item, 'buttonRenderer'))['command'])

            for comment in reversed(list(self.search_dict(response, 'commentRenderer'))):
                result = {'cid': comment['commentId'],
                          'text': ''.join([c['text'] for c in comment['contentText'].get('runs', [])]),
                          'time': comment['publishedTimeText']['runs'][0]['text'],
                          'author': comment.get('authorText', {}).get('simpleText', ''),
                          'channel': comment['authorEndpoint']['browseEndpoint'].get('browseId', ''),
                          'votes': comment.get('voteCount', {}).get('simpleText', '0'),
                          'photo': comment['authorThumbnail']['thumbnails'][-1]['url'],
                          'heart': next(self.search_dict(comment, 'isHearted'), False)}

                try:
                    result['time_parsed'] = dateparser.parse(result['time'].split('(')[0].strip()).timestamp()
                except AttributeError:
                    pass

                paid = (
                    comment.get('paidCommentChipRenderer', {})
                    .get('pdgCommentChipRenderer', {})
                    .get('chipText', {})
                    .get('simpleText')
                )
                if paid:
                    result['paid'] = paid

                yield result
            time.sleep(sleep)

    def get_comments_detail(self, video_id):
        comment_with_commenter_name = list()
        t = ("commenter_name", "comment", "likes")
        comment_generator = self.get_comments(video_id, 1, 'en')
        for comment in comment_generator:
            comment['comment'] = comment.pop('text')
            comment['commenter_name'] = comment.pop('author')
            comment['likes'] = comment.pop('votes')
            comment = dict([(key, comment[key]) for key in t])
            comment_with_commenter_name.append(comment)

        comments = {"video_id": video_id, "comments": comment_with_commenter_name}
        no_of_comments = len(comment_with_commenter_name)
        result = Mongodb("comments").insert_comments(comments)
        if result: Postgresdb("youtube").update(no_of_comments, video_id)
        # print("Successfully Inserted!" if result == True else "Insert Failed!")

    def get_comments_details(self, videos):
        try:
            with ThreadPoolExecutor(max_workers=len(videos)) as executor:
                executor.map(self.get_comments_detail, [video["VideoId"] for video in videos])
        except Exception as e:
            print('The Exception message is: ', e)
            traceback.print_exc()

    @staticmethod
    def regex_search(text, pattern, group=1, default=None):
        match = re.search(pattern, text)
        return match.group(group) if match else default

    @staticmethod
    def search_dict(partial, search_key):
        stack = [partial]
        while stack:
            current_item = stack.pop()
            if isinstance(current_item, dict):
                for key, value in current_item.items():
                    if key == search_key:
                        yield value
                    else:
                        stack.append(value)
            elif isinstance(current_item, list):
                for value in current_item:
                    stack.append(value)
                    
