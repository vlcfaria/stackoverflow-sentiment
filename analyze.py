import json
import pandas as pd
import matplotlib.pyplot as plt

def plot_histogram(data, title, xlabel, ylabel='Frequency', bins=40, figsize=(10, 6)):
    plt.figure(figsize=figsize)
    data.hist(bins=bins)
    plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.tight_layout()
    plt.show()

def plot_horizontal_bar(data, title, xlabel, top_n=10, figsize=(12, 8), ascending=True):
    if ascending:
        plot_data = data.head(top_n)
    else:
        plot_data = data.tail(top_n)
    
    plt.figure(figsize=figsize)
    plt.barh(range(len(plot_data)), plot_data.values)
    plt.yticks(range(len(plot_data)), plot_data.index)
    plt.xlabel(xlabel)
    plt.title(title)
    plt.gca().invert_yaxis()
    plt.tight_layout()
    plt.show()

def analyze_sentiment(file_path, min_count=100):
    tag_dict = {}

    with open(file_path, 'r') as f:
        for line in f:
            try:
                post = json.loads(line)
                
                sentiments = []
                if 'body_sentiment' in post:
                    sentiments.append(post['body_sentiment'])
                
                if 'comments' in post:
                    for comment in post['comments']:
                        if 'text_sentiment' in comment:
                            sentiments.append(comment['text_sentiment'])
                
                if 'answers' in post:
                    for answer in post['answers']:
                        if 'body_sentiment' in answer:
                            sentiments.append(answer['body_sentiment'])
                        if 'comments' in answer:
                            for comment in answer['comments']:
                                if 'text_sentiment' in comment:
                                    sentiments.append(comment['text_sentiment'])
                
                if not sentiments:
                    continue
                    
                minimum_sentiment = min(sentiments)
                average_sentiment = sum(sentiments) / len(sentiments)
                
                if 'tags' in post:
                    for tag in post['tags']:
                        if tag not in tag_dict:
                            tag_dict[tag] = {'count': 1, 'minimum_sentiment': minimum_sentiment, 'average_sentiment': average_sentiment}
                        else:
                            tag_dict[tag]['minimum_sentiment'] += minimum_sentiment
                            tag_dict[tag]['average_sentiment'] += average_sentiment
                            tag_dict[tag]['count'] += 1

            except:
                continue

    tag_df = pd.DataFrame.from_dict(tag_dict, orient='index')
    tag_df['average_minimum_sentiment'] = tag_df['minimum_sentiment'] / tag_df['count']
    tag_df['average_average_sentiment'] = tag_df['average_sentiment'] / tag_df['count']
    tag_df = tag_df[tag_df['count'] >= min_count]
    tag_df = tag_df.sort_values(by='average_minimum_sentiment', ascending=True)

    plot_histogram(tag_df['average_minimum_sentiment'], 'Distribution of Average Minimum Sentiment by Tag', 'Average Minimum Sentiment')
    
    worst_tags = tag_df.head(10)
    plot_horizontal_bar(worst_tags['average_minimum_sentiment'], 'Top 10 Tags with Worst Average Minimum Sentiment', 'Average Minimum Sentiment')
    
    plot_histogram(tag_df['average_average_sentiment'], 'Distribution of Average Sentiment by Tag', 'Average Sentiment')
    
    worst_avg_tags = tag_df.nsmallest(10, 'average_average_sentiment')
    plot_horizontal_bar(worst_avg_tags['average_average_sentiment'], 'Top 10 Tags with Worst Average Sentiment', 'Average Sentiment')

    
if __name__ == "__main__":
    analyze_sentiment('analyzed.jsonl', min_count=100)
