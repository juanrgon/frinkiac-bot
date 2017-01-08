import base64

from time import sleep

from fuzzywuzzy import fuzz, process
import yaml
import praw
import requests


def main():
    with open('already_commented_ids.yaml') as ids_file:
        already_commented_ids = yaml.load(ids_file.read())

    with open('top_phrases.yaml') as phrases_file:
        top_phrases = yaml.load(phrases_file.read())

    username = 'frinkiac-bot'
    password = '<password>'
    client_id = '<client_id>'
    client_secret = '<client_secret>'
    useragent = ("Frinkiac assistant for fans of The Simpsons. Contact me at "
                 "jrg2156@gmail.com (by /u/juanthedev)")

    reddit_client = praw.Reddit(user_agent=useragent,
                                username=username,
                                password=password,
                                client_id=client_id,
                                client_secret=client_secret)

    subreddit = reddit_client.subreddit('TheSimpsons')

    while True:
        old_id_list = already_commented_ids
        already_commented_ids = []
        with open('already_commented_ids.yaml', 'w+') as phrases_file:
            top_phrases_yaml = yaml.dump(phrases_file.read(),
                                         default_flow_style=False)
            phrases_file.write(top_phrases_yaml)
        for comment in subreddit.comments(limit=200):
            if comment.id not in old_id_list:
                query = frinkiac_query(comment.body)
                if query:
                    matched_top_phrase = top_phrase_match(query,
                                                          top_phrases.keys())
                    if matched_top_phrase is not None:
                        image_url = top_phrases[query]

                    else:
                        image_url = search_frinkiac(query)

                    if image_url is not None:
                        reply_message = '[Search Result]({})'.format(image_url)
                        comment.reply(reply_message)
                        already_commented_ids.append(comment.id)
                        sleep(600)  # Can't reply again for another 10 minutes.


def top_phrase_match(query, top_phrases):
    phrase, score = process.extractOne(
        query, top_phrases, scorer=fuzz.token_sort_ratio)
    if score >= 87:
        return phrase
    else:
        return None


def frinkiac_query(comment_text):
    """
    Return query text or False if this comment doesn't begin with one of the
    bots trigger phrases.
    """
    comment_text = normalize_text(comment_text)
    trigger_phrases = ['frinkiac', 'hey frinkiac', 'yo frinkiac', 'frinkiac:']
    for phrase in trigger_phrases:
        if comment_text.startswith(phrase):
            comment_text = comment_text[len(phrase):]
            query = comment_text.lstrip(' ,')
            return query
    else:
        return False


def normalize_text(comment_text):
    text = comment_text
    text = text.strip()
    text = text.lower()
    return text


def search_frinkiac(query):
    """
    Search 'query' in frinkiac.com and return the url for the top result image.

    Image url will include the meme text as a caption.
    """
    search_url = u'https://frinkiac.com/api/search?q={frinkiac_query}'
    captions_url = u'https://frinkiac.com/api/caption?e={episode}&t={timestamp}'
    image_url = u'https://frinkiac.com/meme/{episode}/{timestamp}.jpg?b64lines={b64_subtitles}'

    search_url = search_url.format(frinkiac_query=query)
    search_results = requests.get(search_url).json()

    # If there are results, build the meme image link for the top result...
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
    # ...else return False to indicate that there were no results for this query.
    else:
        return False


if __name__ == "__main__":
    main()
