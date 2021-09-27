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

from reddit_scraper import RedditScraper
from thread_analyzer import ThreadAnalyzer

CLIENT_ID = ''
CLIENT_SECRET = ''
SUBREDDIT_NAME = 'CryptoCurrency'
KEYWORDS = ['BTC', 'ETH', 'TRX']
MOST_FREQ_COUNT = 10

if __name__ == '__main__':
    analyzer = ThreadAnalyzer()
    scraper = RedditScraper(CLIENT_ID, CLIENT_SECRET)

    all_threads = scraper.get_threads_with_comments_for_today(SUBREDDIT_NAME, keywords=KEYWORDS)
    preprocessed_threads = analyzer.batch_preprocess_threads(all_threads)

    frequency_distributions = analyzer.get_freq_dist(preprocessed_threads)
    print(f'{MOST_FREQ_COUNT} most frequent terms:')
    frequency_distributions[0].tabulate(MOST_FREQ_COUNT)
    print(f'{MOST_FREQ_COUNT} most frequent bigrams:')
    frequency_distributions[1].tabulate(MOST_FREQ_COUNT)
    print(f'{MOST_FREQ_COUNT} most frequent trigrams:')
    frequency_distributions[2].tabulate(MOST_FREQ_COUNT)

    sentiment = analyzer.classify_threads_sentiment(all_threads)
    print(f'Sentiment from all comments for today: {sentiment[1]} (score: {sentiment[0]})')
