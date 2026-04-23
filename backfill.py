import redis
import json

r = redis.Redis(host='localhost', port=6379, decode_responses=True)

with open("transactions.jsonl", "r") as f:
    for i, line in enumerate(f):
        tx = json.loads(line.strip())
        r.xadd("transactions", {"data": json.dumps(tx)})

        if i % 10000 == 0:
            print(f"{i} records loaded...")

print("Backfill completed")