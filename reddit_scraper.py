#  reddit-scraper-task
#  Copyright (C) 2021 Zdravko Yanakiev
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU Affero General Public License as
#  published by the Free Software Foundation, either version 3 of the
#  License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU Affero General Public License for more details.
#
#  You should have received a copy of the GNU Affero General Public License
#  along with this program.  If not, see <https://www.gnu.org/licenses/>.

import json
from datetime import date

from oauthlib.oauth2 import BackendApplicationClient
from requests_oauthlib import OAuth2Session


class RedditScraper:
    __USER_AGENT = 'python3:reddit-scraper-task:0.0.1'
    __ACCESS_TOKEN_ENDPOINT = 'https://www.reddit.com/api/v1/access_token'

    def __init__(self, client_id, client_secret):
        client = BackendApplicationClient(client_id=client_id)
        oauth = OAuth2Session(client=client)
        oauth.headers.update({'User-Agent': RedditScraper.__USER_AGENT, 'Accept': 'application/json'})

        self.session = oauth
        self.__token = oauth.fetch_token(token_url=RedditScraper.__ACCESS_TOKEN_ENDPOINT, client_id=client_id,
                                         client_secret=client_secret)

    @staticmethod
    def __unix_timestamp_to_date(unix_timestamp):
        """
        Gets the date part for a unix timestamp
        :param unix_timestamp:
        :return: python date
        """
        return date.fromtimestamp(unix_timestamp)

    @staticmethod
    def __filter_threads(threads, keywords):
        """
        Filter threads by keywords
        :param threads:
        :param keywords:
        :return:
        """
        filtered_threads = list()

        for thread in threads:
            for keyword in keywords:
                if keyword in thread['title'] or keyword in thread['selftext']:
                    filtered_threads.append(thread)
                    break

        return filtered_threads

    def get_threads_for_today(self, subreddit_name):
        """
        Get all today's threads from a specific subreddit
        :param subreddit_name:
        :return:
        """
        all_threads = list()
        today = date.today()

        threads_left = True
        after = ''

        while threads_left:
            response = self.session.get(f'https://oauth.reddit.com/r/{subreddit_name}/new',
                                        params={'after': after}).json()

            data = response['data']
            after = data['after']
            threads = data['children']

            if len(threads) == 0:
                threads_left = False

            for thread in threads:
                if RedditScraper.__unix_timestamp_to_date(thread['data']['created_utc']) == today:
                    all_threads.append(thread['data'])
                else:
                    threads_left = False
                    break

        return all_threads

    def write_threads_with_comments_for_today(self, subreddit_name, keywords=None):
        threads = self.get_threads_with_comments_for_today(subreddit_name, keywords=keywords)

        with open(f'{str(date.today())}_{subreddit_name}.json', 'w', encoding='utf-8') as f:
            json.dump(threads, f, ensure_ascii=False, indent=4)

    def get_threads_with_comments_for_today(self, subreddit_name, keywords=None):
        """
        Get all comments for all of today's threads in a subreddit, filtered by keywords
        :param subreddit_name:
        :param keywords: optional keywords to filter by
        :return:
        """
        print(f'Fetching all of today\'s threads for /r/{subreddit_name}')
        threads = self.get_threads_for_today(subreddit_name)

        if keywords:
            threads = RedditScraper.__filter_threads(threads, keywords)

        for thread in threads:
            thread_id = thread['id']
            thread['comments'] = self.get_comments_for_thread(thread_id)

        print('Done fetching threads.')
        return threads

    def get_comments_for_thread(self, thread_id):
        """
        Get all comments for a specific thread
        :param thread_id: internal thread ID
        :return:
        """
        response = self.session.get(f'https://oauth.reddit.com/comments/{thread_id}').json()

        thread_id = response[0]['data']['children'][0]['data']['id']
        children = response[1]['data']['children']

        more_children_ids = [child_id for child in children if child['kind'] == 'more' for child_id in
                             child['data']['children']]
        initial_comments = [child for child in children if child['kind'] == 't1']

        return initial_comments + self.__get_more_comments(thread_id, more_children_ids)

    def __get_more_comments(self, thread_id, children_ids):
        """
        Recursively fetch more comments for a thread
        :param thread_id: internal thread ID
        :param children_ids: childrent comment IDs
        :return:
        """
        comments = list()

        for i in range(0, len(children_ids), 100):
            request_params = {'link_id': f't3_{thread_id}', 'api_type': 'json',
                              'children': ','.join(children_ids[i:i + 100])}
            thread_children = \
                self.session.get(f'https://oauth.reddit.com/api/morechildren', params=request_params).json()['json'][
                    'data']['things']

            for child in thread_children:
                if child['kind'] == 't1':
                    comments.append(child)
                elif child['kind'] == 'more':
                    new_children_ids = child['data']['children']
                    comments += self.__get_more_comments(thread_id, new_children_ids)

        return comments
