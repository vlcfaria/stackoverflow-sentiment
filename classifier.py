from scipy.special import softmax
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import argparse
import json
import numpy

def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument('-i', type=str, help='Input JSONL file', required=True)

    return parser.parse_args()

def classify_sentiment(tokenizer, model, text):
    encoded_input = tokenizer(text, return_tensors='pt')
    output = model(**encoded_input)
    scores = output[0][0].detach().numpy()
    scores = softmax(scores)
    
    return np.argmin(scores)

def classify_post(post):
    if 'answers' in post: #Question
        augmented = post['title'] + post['body']
        #del post['title'], post['body']
        post['body_sentiment'] = classify_sentiment(tokenizer, model, augmented)
    else: #Answer
        post['body_sentiment'] = classify_sentiment(tokenizer, model, post['body'])
        #del post['body']

    #Classify comments
    for c in post['comments']:
        c['text_sentiment'] = classify_sentiment(tokenizer, model, c['text'])
        #del c['text']

if __name__ == '__main__':
    MODEL = 'Cloudy1225/stackoverflow-roberta-base-sentiment'
    tokenizer = AutoTokenizer.from_pretrained(MODEL)
    model = AutoModelForSequenceClassification.from_pretrained(MODEL)

    args = parse_args()
    with open(args.i, 'r') as inp:
        with open('./analyzed.jsonl', 'w') as outp:
            for line in inp:
                obj = json.loads(line)
                classify_post(obj)
                json.dump(obj, outp)
                outp.write('\n')
