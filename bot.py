import base64

from time import sleep

import praw
import requests


def main(already_commented):
    username = 'frinkiac-bot'
    password = <password>
    useragent = ("Frinkiac assistant for fans of The Simpsons. Contact me at "
                 "jrg2156@gmail.com")

    reddit_client = praw.Reddit(useragent)
    reddit_client.login(username, password, disable_warning=True)

    subreddit = 'TheSimpsons'

    already_commented = set()

    subreddit = reddit_client.get_subreddit(subreddit)
    for comment in subreddit.get_comments():
        if comment.id not in already_commented:
            query = frinkiac_query(comment.body)
            if query:
                frinkiac_image_url = search_frinkiac(query)
                comment.reply(frinkiac_image_url)
                already_commented.add(comment.id)


def frinkiac_query(comment_text):
    comment_text = normalize_text(comment_text)
    print comment_text
    trigger_phrases = ['frinkiac', 'hey frinkiac', 'yo frinkiac', 'frinkiac:']
    for phrase in trigger_phrases:
        if comment_text.startswith(phrase):
            _, query = comment_text.split(phrase)
            return query
    else:
        return False


def normalize_text(comment_text):
    text = comment_text
    text = text.strip()
    text = text.lower()
    return text


def search_frinkiac(query):
    search_url = u'https://frinkiac.com/api/search?q={frinkiac_query}'
    captions_url = u'https://frinkiac.com/api/caption?e={episode}&t={timestamp}'
    image_url = u'https://frinkiac.com/meme/{episode}/{timestamp}.jpg?b64lines={b64_subtitles}'

    search_url = search_url.format(frinkiac_query=query)
    search_results = requests.get(search_url).json()
    if search_results:
        top_result = search_results[0]
        episode = top_result['Episode']
        timestamp = top_result['Timestamp']

        captions_url = captions_url.format(episode=episode,
                                           timestamp=timestamp)
        captions_info = requests.get(captions_url).json()
        subtitles = captions_info['Subtitles']
        subs_string = u'\n'.join([sub['Content'] for sub in subtitles])
        b64_subtitles = base64.b64encode(subs_string)

        return image_url.format(episode=episode,
                                timestamp=timestamp,
                                b64_subtitles=b64_subtitles)


if __name__ == "__main__":
    already_commented = set()
    while True:
        sleep(600)
        main(already_commented)
