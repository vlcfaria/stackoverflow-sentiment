import argparse
import json
import psycopg as psy
from psycopg.rows import dict_row

def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument('-n', type=int, help='Number of posts to be parsed', required = True)
    parser.add_argument('-o', type=str, help='Output file', required=True)

    return parser.parse_args()

def treat_post(post):
    """Treats the post object"""
    #Convert datetime
    post['creation_date'] = post['creation_date'].isoformat()
    post['comments'] = []

    return post

def treat_comment(comment):
    """Treats comments"""
    #Convert datetime
    comment['creation_date'] = comment['creation_date'].isoformat()
    
    return comment

if __name__ == '__main__':
    args = parse_args()

    conn = psy.connect("dbname=stackoverflow user=postgres", row_factory=dict_row)
    question_cur = conn.cursor(name='question_cur')
    bulk_cur = conn.cursor(name='bulk_cur')

    with open(args.o, 'w') as output:
        BATCH_SIZE = 10000

        q_fields = ['id', 'owner_user_id', 'score', 'tags', 'title', 'body', 'comment_count', 'creation_date']
        ans_fields = ['id', 'parent_id', 'owner_user_id', 'score', 'body', 'comment_count', 'creation_date']
        comm_fields = ['id', 'post_id', 'user_id', 'score', 'text', 'creation_date']
        num_posts = 0
        num_comments = 0

        #Define our years -> 2014-2024
        lower, upper = 2014, 2024
        years = range(2014,2024)
        posts_per_year = args.n // (upper-lower)

        for y in years:
            query = question_cur.execute(f"""SELECT {', '.join(q_fields)} FROM posts 
                                            WHERE post_type_id = 1 AND (comment_count > 0 OR answer_count > 0) AND extract(year from creation_date) = %s
                                            LIMIT %s;
                                        """, (y, posts_per_year,))
            #Process all
            while True:
                data = query.fetchmany(BATCH_SIZE)
                if not data: break #No data

                qids = {q['id'] for q in data}

                #Get all answers
                raw_answers = bulk_cur.execute(f"""SELECT {', '.join(ans_fields)} FROM posts
                                    WHERE parent_id = ANY(%s) AND post_type_id = 2""", (list(qids),)).fetchall()
                ans_ids = {a['id'] for a in raw_answers}
                
                #Get all comments from questions + answers
                raw_comments = bulk_cur.execute(f"""SELECT {', '.join(comm_fields)} FROM comments
                                                WHERE post_id = ANY(%s)
                                                """, (list(qids.union(ans_ids)),)).fetchall()
                
                #Index everything, so we can append the comments easily
                all_posts = {q['id']: treat_post(q) for q in data + raw_answers}

                for c in raw_comments: #Add comments
                    all_posts[c['post_id']]['comments'].append(treat_comment(c))
                
                #Now add answer to questions
                for q in data:
                    q['answers'] = []
                
                for ans in raw_answers:
                    all_posts[ans['parent_id']]['answers'].append(ans)

                #Write out final obj
                for q in data:
                    json.dump(q, output)
                    output.write('\n')
                
                num_posts += len(data) + len(raw_answers)
                num_comments += len(raw_comments)

    question_cur.close()
    conn.close()

    print(f"Fetched {num_posts} posts and {num_comments} comments")