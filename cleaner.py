from bs4 import BeautifulSoup, Comment
from markdown import markdown
import validators
import argparse
import json

def clean_stackoverflow_post(html_text):
    """
    Cleans the HTML from a Stack Overflow post for sentiment analysis. This function was (partially) AI generated

    Args:
        html_text: A string containing the HTML of the post.

    Returns:
        A cleaned string.
    """
    soup = BeautifulSoup(html_text, 'html.parser')

    # 1. Remove script and style tags completely
    for script_or_style in soup(['script', 'style']):
        script_or_style.decompose()

    # 2. Remove HTML comments
    for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
        comment.extract()

    # 3. Replace code blocks
    for code_tag in soup.find_all('code'):
        code_tag.replace_with('')

    # 5. Handle links by keeping the text and adding a token for the href
    for a in soup.find_all('a'):
        #Replace if its not an url in first place
        a.replace_with(f"{a.get_text() if not validators.url(a.get_text()) else ''} http")

    # 6. Replace images with a token
    for img in soup.find_all('img'):
        img.replace_with('')

    # 7. Get the text, which strips other tags like <p>, <strong>, etc.
    # Use a space as a separator to avoid words merging
    text = soup.get_text(separator=' ', strip=True)

    #Also process the final text as required by the model
    new_text = []
    for t in text.split(' '):
        t = '@user' if t.startswith('@') and len(t) > 1 else t
        t = 'http' if t.startswith('http') else t
        new_text.append(t)
    return ' '.join(new_text).strip()

def clean_comment(md_text):
    try:
        html = markdown(md_text)
    except: #Malformatted markdown...
        return ''
    soup = BeautifulSoup(html, "html.parser")

    #Also replace code blocks
    for code_tag in soup.find_all('code'):
        code_tag.replace_with('')
        
    text = soup.get_text(separator=' ', strip=True)

    #Also process the final text as required by the model
    new_text = []
    for t in text.split(' '):
        t = '@user' if t.startswith('@') and len(t) > 1 else t
        t = 'http' if t.startswith('http') else t
        new_text.append(t)
    return ' '.join(new_text).strip()

def clean_post(post):
    #Clean the body
    post['body'] = clean_stackoverflow_post(post['body'])

    #Clean answers, if they exist
    if 'answers' in post:
        for a in post['answers']:
            clean_post(a)

    #Clean comments
    for c in post['comments']:
        c['text'] = clean_comment(c['text'])
    #Filter empty comments from cleaning
    post['comments'] = list(filter(lambda x : x['text'] != '', post['comments']))

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', type=str, help='Path to dump', required=True)
    args = parser.parse_args()

    with open(args.i, 'r') as inp:
        with open('./cleaned.jsonl', 'w') as outp:
            for line in inp:
                #Load the object
                obj = json.loads(line)

                #Clean posts recursively
                clean_post(obj)
                json.dump(obj, outp)
                outp.write('\n')
