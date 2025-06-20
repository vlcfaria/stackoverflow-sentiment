from scipy.special import softmax
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import argparse
import json
import numpy as np
import torch
import time
from datetime import datetime, timedelta

def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument('-i', type=str, help='Input JSONL file', required=True)

    return parser.parse_args()

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

def classify_sentiment(tokenizer, model, text):
    encoded_input = tokenizer(text, return_tensors='pt', truncation=True, max_length=512)
    encoded_input = {k: v.to(device) for k, v in encoded_input.items()}
    output = model(**encoded_input)
    scores = output[0][0].detach().cpu().numpy()
    scores = softmax(scores)
    return int(np.argmax(scores))

def classify_post(post):
    if 'answers' in post:
        augmented = post['title'] + '\n' + post['body']
        post['body_sentiment'] = classify_sentiment(tokenizer, model, augmented)
        for a in post['answers']:
            classify_post(a)
    else:
        post['body_sentiment'] = classify_sentiment(tokenizer, model, post['body'])

    for c in post['comments']:
        c['text_sentiment'] = classify_sentiment(tokenizer, model, c['text'])

if __name__ == '__main__':
    MODEL = 'Cloudy1225/stackoverflow-roberta-base-sentiment'
    tokenizer = AutoTokenizer.from_pretrained(MODEL)
    model = AutoModelForSequenceClassification.from_pretrained(MODEL)
    model.to(device)

    args = parse_args()
    
    with open(args.i, 'r') as f:
        total_lines = sum(1 for _ in f)
    
    start_time = time.time()
    processed_lines = 0
    
    with open(args.i, 'r') as inp:
        with open('./analyzed.jsonl', 'w') as outp:
            for line in inp:
                obj = json.loads(line)
                classify_post(obj)
                json.dump(obj, outp)
                outp.write('\n')
                
                processed_lines += 1
                
                if processed_lines % 10000 == 0:
                    current_time = time.time()
                    elapsed_time = current_time - start_time
                    
                    progress_percent = (processed_lines / total_lines) * 100
                    
                    if processed_lines > 0:
                        avg_time_per_line = elapsed_time / processed_lines
                        remaining_lines = total_lines - processed_lines
                        eta_seconds = remaining_lines * avg_time_per_line
                        eta = datetime.now() + timedelta(seconds=eta_seconds)
                        
                        print(f"Progress: {processed_lines}/{total_lines} ({progress_percent:.1f}%) | "
                              f"Elapsed: {timedelta(seconds=int(elapsed_time))} | "
                              f"ETA: {eta.strftime('%Y-%m-%d %H:%M:%S')} | "
                              f"Rate: {processed_lines/elapsed_time:.1f} lines/sec")
    
    total_time = time.time() - start_time
    print(f"\nProcessed {processed_lines} lines in {timedelta(seconds=int(total_time))}")
    print(f"Average rate: {processed_lines/total_time:.1f} lines/sec")
