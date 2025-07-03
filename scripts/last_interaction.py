import argparse
import json
import psycopg as psy
from psycopg.rows import dict_row

def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument('-i', type=str, help='Path to user_dump', required=True)
    parser.add_argument('-o', type=str, help='Output file', required=True)

    return parser.parse_args()

i = 0
if __name__ == '__main__':
    args = parse_args()
    ids = set()
    with open(args.i, 'r') as inp:
        data = json.load(inp)

    conn = psy.connect("dbname=stackoverflow user=postgres", row_factory=dict_row)
    cur = conn.cursor(name='cur')

    ids = list(data.keys())

    comments = cur.execute(f"""SELECT user_id, MAX(creation_date) FROM comments
                    WHERE user_id = ANY(%s)
                    GROUP BY user_id;
                """, (ids,)).fetchall()
    
    print("Finished comments")
    
    posts = cur.execute(f"""SELECT owner_user_id, MAX(creation_date) FROM posts
                    WHERE owner_user_id = ANY(%s)
                    GROUP BY owner_user_id;
                """, (ids,)).fetchall()

    print("Finished posts")

    #Transform post and comments to dictionaries
    c_indexed = {}
    for c in comments:
        c_indexed[str(c['user_id'])] = c['max']
    p_indexed = {}
    for p in posts:
        p_indexed[str(p['owner_user_id'])] = p['max']

    #Add the interactions
    for id, user in data.items():
        #print(id)
        if id in p_indexed and id in c_indexed:
            user['last_interaction'] = max(p_indexed[id], c_indexed[id]).isoformat()
        elif id in p_indexed:
            user['last_interaction'] = p_indexed[id].isoformat()
        elif id in c_indexed:
            user['last_interaction'] = c_indexed[id].isoformat()
        else:
            user['last_interaction'] = None
    
    with open(args.o, 'w') as outp:
        json.dump(data, outp, indent=1)

    cur.close()
    conn.close()