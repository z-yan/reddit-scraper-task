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

import statistics

import nltk
from nltk.sentiment import SentimentIntensityAnalyzer


class ThreadAnalyzer:
    def __init__(self):
        try:
            nltk.data.find('corpora/stopwords.zip')
            nltk.data.find('tokenizers/punkt')
            nltk.data.find('sentiment/vader_lexicon.zip')
        except LookupError:
            print('Downloading missing NLTK resources...')
            nltk.download(['stopwords', 'punkt', 'vader_lexicon'], quiet=True)
        self.stopwords = nltk.corpus.stopwords.words('english')
        self.sentiment_analyzer = SentimentIntensityAnalyzer()

    @staticmethod
    def thread_to_texts(thread):
        """
        Process thread into list of comments
        :param thread:
        :return: List of comment strings
        """
        # Get original post text
        thread_op_text = thread['selftext']
        # Get all comments' texts
        comments_text = [comment['data']['body'] for comment in thread['comments']]
        # Combine them into one list
        all_texts = [thread_op_text] + comments_text

        return all_texts

    def text_to_words(self, text):
        """
        Process text into a list of tokenized, lowercase words
        :param text:
        :return: List of word strings
        """
        # Tokenize text
        words = nltk.word_tokenize(text)
        # Remove unimportant words (stopwords) and punctuation
        words = [w for w in words if w.lower() not in self.stopwords and w.isalnum()]

        return words

    def batch_preprocess_threads(self, threads):
        """
        Process all threads in list
        :param threads:
        :return: All words in all threads
        """
        threads_texts = [self.thread_to_texts(thread) for thread in threads]
        threads_words = [w for text in threads_texts for comment in text for w in self.text_to_words(comment)]

        return threads_words

    @staticmethod
    def get_freq_dist(word_list):
        """
        Prints the frequency distribution of tokens, bigrams and trigrams in word_list
        :param word_list:
        :return: tuple (token freq dist, bigram freq dist, trigram freq dist)
        """
        print('Analyzing frequency distribution.')

        thread_lowercase = [w.lower() for w in word_list]

        token_freq_dist = nltk.FreqDist(thread_lowercase)
        bigram_finder = nltk.collocations.BigramCollocationFinder.from_words(thread_lowercase)
        trigram_finder = nltk.collocations.TrigramCollocationFinder.from_words(thread_lowercase)

        return token_freq_dist, bigram_finder.ngram_fd, trigram_finder.ngram_fd

    @staticmethod
    def __sentiment_from_compound_score(compound):
        """
        Computes the sentiment from a compound score
        :param compound:
        :return: positive, neutral or negative
        """
        # scoring from https://github.com/cjhutto/vaderSentiment#about-the-scoring
        if compound >= 0.05:
            return 'positive'
        elif -0.05 < compound < 0.05:
            return 'neutral'
        else:
            return 'negative'

    def get_sentiment(self, text):
        """
        Computes the polarity scores for a text
        :param text:
        :return:
        """
        return self.sentiment_analyzer.polarity_scores(text)

    def classify_threads_sentiment(self, threads):
        """
        Returns the predominant sentiment for a list of threads
        :param threads:
        :return: positive, neutral or negative
        """
        print('Analyzing threads sentiment')

        all_comments = [comment for thread in threads for comment in self.thread_to_texts(thread)]

        all_sentiments = [self.get_sentiment(comment) for comment in all_comments]

        average_compound_score = statistics.mean([sentiment['compound'] for sentiment in all_sentiments])

        return average_compound_score, self.__sentiment_from_compound_score(average_compound_score)
