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
