import argparse
import json
import psycopg as psy
from psycopg.rows import dict_row

def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument('-i', type=str, help='Path to dump', required=True)
    parser.add_argument('-o', type=str, help='Output file', required=True)

    return parser.parse_args()

def get_ids(post, ids):
    ids.add(post['owner_user_id'])

    if 'answers' in post:
        for a in post['answers']:
            get_ids(a, ids)

    for c in post['comments']:
        ids.add(c['user_id'])

if __name__ == '__main__':
    args = parse_args()
    ids = set()
    with open(args.i, 'r') as inp:
        for line in inp:
            obj = json.loads(line)
            get_ids(obj, ids)

    ids.remove(None)
    print(f"Parsed {len(ids)} unique user ids")

    #Pull the user data
    conn = psy.connect("dbname=stackoverflow user=postgres", row_factory=dict_row)
    cur = conn.cursor(name='cur')

    cols = ['id', 'reputation', 'location', 'views', 'up_votes', 'down_votes', 'creation_date', 'last_access_date']
    query = cur.execute(f"""SELECT {', '.join(cols)} FROM users
                            WHERE id = ANY(%s);
                        """, (list(ids),))
    
    with open(args.o, 'w') as outp:
        users = query.fetchall()

        for u in users:
            #Convert time
            u['creation_date'] = u['creation_date'].isoformat()
            u['last_access_date'] = u['last_access_date'].isoformat()
        #Index by id
        users = {u['id']: u for u in users}
        json.dump(users, outp, indent=1)

    cur.close()
    conn.close()