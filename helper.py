import json
from datetime import datetime
from enum import Enum

class Sentiment(Enum):
    NEGATIVE = 0
    NEUTRAL = 1
    POSITIVE = 2

def load_post_data(path: str, keep_text: bool = False):
    'Loads user data from a .jsonl file, optionally keeping text, if RAM allows'
    data = {}
    with open(path, 'r') as inp:
        for line in inp:
            obj = json.loads(line)

            #Remove all text attributes
            if not keep_text:
                del obj['body'], obj['title']
                for a in obj['answers']:
                    del a['body']
                    for c in a['comments']:
                        del c['text']
                for c in obj['comments']:
                    del c['text']
            
            #Convert dates
            val = 'creation_date'
            obj[val] = datetime.fromisoformat(obj[val])
            for c in obj['comments']:
                c[val] = datetime.fromisoformat(c[val])
            for a in obj['answers']:
                a[val] = datetime.fromisoformat(a[val])
                for c in a['comments']:
                    c[val] = datetime.fromisoformat(c[val])

            #Convert user IDs to integers
            if 'owner_user_id' in obj and obj['owner_user_id'] is not None:
                obj['owner_user_id'] = int(obj['owner_user_id'])
            
            for c in obj['comments']:
                if 'user_id' in c and c['user_id'] is not None:
                    c['user_id'] = int(c['user_id'])
            
            for a in obj['answers']:
                if 'owner_user_id' in a and a['owner_user_id'] is not None:
                    a['owner_user_id'] = int(a['owner_user_id'])
                for c in a['comments']:
                    if 'user_id' in c and c['user_id'] is not None:
                        c['user_id'] = int(c['user_id'])

            obj['average_sentiment'] = get_post_average_sentiment(obj)
            obj['minimum_sentiment'] = get_post_minimum_sentiment(obj)

            data[obj['id']] = obj

    return data

def load_user_data(path: str):
    'Loads user data from a user .json file'
    with open(path, 'r') as inp:
        user_data = json.load(inp)
    
    #Convert dates
    for _, u in user_data.items():
        for val in ['creation_date', 'last_access_date', 'last_interaction']:
            u[val] = datetime.fromisoformat(u[val])
    
    #Convert indexes to integers
    og = list(user_data.keys())
    for u in og:
        user_data[int(u)] = user_data[u]
        del user_data[u]

    return user_data

def min_sentiment(post: dict, include_answers = True):
    '''
    Returns the minimum sentiment of a question post. The minimum sentiment is the lowest sentiment in the post/comment chain.
    You can also optionally only analyze the minimum sentiment between the question post and it's comments.
    '''

    val = post['body_sentiment']
    for c in post['comments']:
        val = min(val, c['text_sentiment'])

    if include_answers:
        for a in post['answers']:
            val = min(val, a['body_sentiment'])
            for c in a['comments']:
                val = min(val, c['text_sentiment'])
    
    return val

def get_users_average_sentiment(post_data: dict, minimum_posts: int = 10):
    '''
    Returns the average sentiment of all users based on their posts, comments, and answers.
    If a user has less than `minimum_posts` posts, comments, or answers, they are not included in the result.
    '''
    user_sentiments = {}
    for post in post_data.values():
        user_id = post['owner_user_id']
        if user_id not in user_sentiments:
            user_sentiments[user_id] = {'count': 0, 'total': 0}

        user_sentiments[user_id]['count'] += 1
        user_sentiments[user_id]['total'] += post["body_sentiment"]

        for c in post['comments']:
            if c['user_id'] not in user_sentiments:
                user_sentiments[c['user_id']] = {'count': 0, 'total': 0}
            user_sentiments[c['user_id']]['count'] += 1
            user_sentiments[c['user_id']]['total'] += c["text_sentiment"]

        for a in post['answers']:
            if a['owner_user_id'] not in user_sentiments:
                user_sentiments[a['owner_user_id']] = {'count': 0, 'total': 0}
            user_sentiments[a['owner_user_id']]['count'] += 1
            user_sentiments[a['owner_user_id']]['total'] += a["body_sentiment"]

            for c in a['comments']:
                if c['user_id'] not in user_sentiments:
                    user_sentiments[c['user_id']] = {'count': 0, 'total': 0}
                user_sentiments[c['user_id']]['count'] += 1
                user_sentiments[c['user_id']]['total'] += c["text_sentiment"]

    result = {}
    for user_id, sentiment in user_sentiments.items():
        if sentiment['count'] >= minimum_posts:
            result[user_id] = sentiment['total'] / sentiment['count']

    return result

def get_post_average_sentiment(post: dict):
    '''
    Returns the average sentiment of a post, including its comments and answers.
    '''
    total_sentiment = post['body_sentiment']
    count = 1

    for c in post['comments']:
        total_sentiment += c['text_sentiment']
        count += 1

    for a in post['answers']:
        total_sentiment += a['body_sentiment']
        count += 1
        for c in a['comments']:
            total_sentiment += c['text_sentiment']
            count += 1

    return total_sentiment / count if count > 0 else None

def get_post_minimum_sentiment(post: dict):
    '''
    Returns the minimum sentiment of a post, including its comments and answers.
    '''
    min_sentiment = post['body_sentiment']

    for c in post['comments']:
        min_sentiment = min(min_sentiment, c['text_sentiment'])

    for a in post['answers']:
        min_sentiment = min(min_sentiment, a['body_sentiment'])
        for c in a['comments']:
            min_sentiment = min(min_sentiment, c['text_sentiment'])

    return min_sentiment

def get_user_to_post_dict(post_data):
    '''
    Returns a dictionary mapping user IDs to the posts they have interacted with, sorted by the date
    of the most recent interaction.
    '''
    result = {}
    for post_id, post in post_data.items():
        if post['owner_user_id'] not in result:
            result[post['owner_user_id']] = []
        result[post['owner_user_id']].append((post_id, post['creation_date']))

        for comment in post['comments']:
            if comment['user_id'] not in result:
                result[comment['user_id']] = []
            result[comment['user_id']].append((post_id, comment['creation_date']))

        for answer in post['answers']:
            if answer['owner_user_id'] not in result:
                result[answer['owner_user_id']] = []
            result[answer['owner_user_id']].append((post_id, answer['creation_date']))

            for comment in answer['comments']:
                if comment['user_id'] not in result:
                    result[comment['user_id']] = []
                result[comment['user_id']].append((post_id, comment['creation_date']))

    # Sort each user's posts by the date of the most recent interaction
    for user_id, posts in result.items():
        posts.sort(key=lambda x: x[1], reverse=True)
        result[user_id] = posts

    return result