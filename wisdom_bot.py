__author__ = 'Francis'

import json
import string
import random
import time

from slackclient import SlackClient

from quote import Quote


def load_quotes(path, stopwords):
    with open(path) as json_file:
        quotes = json.load(json_file)['quotes']
        json_file.close()

    result = []
    for quote in quotes:
        cleaned_quote = set(clean_input_sentence(str(quote['quote']), stopwords))
        result.append(Quote(cleaned_quote, str(quote['name']), str(quote['quote'])))
    return result


def load_stopwords():
    stopwords = []
    with open('stopwords.txt') as sw:
        for line in sw:
            stopwords.append(line)
    return stopwords


def load_config(path):
    config = {}
    with open(path) as config_file:
        for line in config_file:
            if len(line) > 3:
                params = line.split('=')
                config[params[0]] = params[1]
    return config


def find_quote(sentence, quotes, stopwords):
    words = set(clean_input_sentence(str(sentence), stopwords))
    words.remove('')
    result = None
    score = 0

    for quote in quotes:
        quote_set = quote.quote
        if len(set.intersection(quote_set, words)) > score:
            score = len(set.intersection(quote_set, words))
            result = quote

    if result is None:
        result = random.choice(quotes)
    return result


def clean_input_sentence(input, stopwords):
    for word in stopwords:
        input.replace(word, '')
    exclude = set(string.punctuation)
    input = ''.join(ch for ch in input if ch not in exclude)
    words = input.lower().split(' ')
    return words


def get_user_id(slack_client, name):
    users = json.loads(slack_client.api_call('users.list'))['members']
    for user in users:
        if name.lower() == user['name']:
            return user['id']


def get_user_name(slack_client, id):
    users = json.loads(slack_client.api_call('users.list'))['members']
    for user in users:
        if id == user['id']:
            return user['name']


def be_wise(config, quotes, stopwords):
    slack_client = SlackClient(config['token'])
    slack_client.rtm_connect()
    user_id = get_user_id(slack_client, config['name'])
    mention_string = '@%s' % user_id
    while True:
        messages = slack_client.rtm_read()
        messages = filter(lambda m: m['type'] == 'message', filter(lambda m: 'type' in m, messages))
        if len(messages) > 0:
            for message in messages:
                if mention_string in message['text']:
                    sentence = message['text'][len(user_id)+3:]
                    quote = find_quote(sentence, quotes, stopwords)
                    name = get_user_name(slack_client, message['user'])
                    response = '<@%s>: %s says: "%s"' % (name, quote.author, quote.sentence)
                    slack_client.rtm_send_message(message['channel'], response)

        time.sleep(1)


if __name__ == '__main__':
    config = load_config('wisdom.conf')
    stopwords = load_stopwords()
    quotes = load_quotes('quotes.json', stopwords)
    random.shuffle(quotes)
    be_wise(config, quotes, stopwords)