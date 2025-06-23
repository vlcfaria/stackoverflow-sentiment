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