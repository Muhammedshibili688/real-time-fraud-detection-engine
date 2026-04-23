# import redis
# import json

# r = redis.Redis(host='localhost', port=6379, decode_responses=True)

# with open("transactions.jsonl", "r") as f:
#     for i, line in enumerate(f):
#         tx = json.loads(line.strip())
#         r.xadd("transactions", {"data": json.dumps(tx)})

#         if i % 10000 == 0:
#             print(f"{i} records loaded...")

# print("Backfill completed")


"""
backfill.py
────────────────────────────────────────────────────────────────
Retroactive Feature Enrichment Utility

Three use cases this solves:
  1. Logic update   — new feature added, re-enrich all historical records
  2. Gap recovery   — consumer crashed, fill missing hours from raw file
  3. Cold start     — generate training data from a large historical snapshot

Usage:
  python backfill.py --source transactions.jsonl
  python backfill.py --source transactions.jsonl --batch-size 500 --delay 0.05
  python backfill.py --source transactions.jsonl --start-line 45000  (resume)
"""

import redis
import json
import time
import argparse
import logging
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%H:%M:%S"
)

# ----------------------------------------------------------------
# CONFIG
# ----------------------------------------------------------------
STREAM_NAME  = "transactions"
CHECKPOINT   = ".backfill_checkpoint"   # tracks last processed line


# ----------------------------------------------------------------
# REDIS
# ----------------------------------------------------------------
def get_redis():
    try:
        r = redis.Redis(host='localhost', port=6379, decode_responses=True)
        r.ping()
        return r
    except redis.ConnectionError:
        logging.error("Redis is not running. Start Redis first.")
        raise


# ----------------------------------------------------------------
# CHECKPOINT (resume support)
# ----------------------------------------------------------------
def save_checkpoint(line_number: int):
    Path(CHECKPOINT).write_text(str(line_number))

def load_checkpoint() -> int:
    if Path(CHECKPOINT).exists():
        val = Path(CHECKPOINT).read_text().strip()
        logging.info(f"Resuming from checkpoint: line {val}")
        return int(val)
    return 0

def clear_checkpoint():
    if Path(CHECKPOINT).exists():
        Path(CHECKPOINT).unlink()


# ----------------------------------------------------------------
# MAIN BACKFILL
# ----------------------------------------------------------------
def run_backfill(source: str, batch_size: int, delay: float, start_line: int):
    r = get_redis()
    source_path = Path(source)

    if not source_path.exists():
        logging.error(f"File not found: {source}")
        return

    total_lines = sum(1 for _ in open(source_path, encoding="utf-8"))
    logging.info(f"Source     : {source}")
    logging.info(f"Total rows : {total_lines:,}")
    logging.info(f"Start line : {start_line:,}")
    logging.info(f"Batch size : {batch_size}")
    logging.info(f"Delay      : {delay}s per batch")
    logging.info("─" * 50)

    processed = 0
    skipped   = 0
    errors    = 0
    batch     = []

    with open(source_path, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f):

            # Resume: skip already-processed lines
            if line_num < start_line:
                skipped += 1
                continue

            line = line.strip()
            if not line:
                continue

            # Parse with error isolation — one bad line doesn't crash all
            try:
                tx = json.loads(line)
            except json.JSONDecodeError as e:
                logging.warning(f"Line {line_num} — bad JSON, skipping: {e}")
                errors += 1
                continue

            batch.append(tx)

            # Flush batch to Redis
            if len(batch) >= batch_size:
                _flush_batch(r, batch, line_num)
                processed += len(batch)
                batch = []

                # Checkpoint every batch so we can resume
                save_checkpoint(line_num)

                # Progress
                pct = ((line_num - start_line) / max(total_lines - start_line, 1)) * 100
                logging.info(f"  {processed:>8,} records pushed | line {line_num:,} | {pct:.1f}%")

                # Rate limiting — don't overwhelm Redis
                if delay > 0:
                    time.sleep(delay)

    # Flush remaining records
    if batch:
        _flush_batch(r, batch, total_lines)
        processed += len(batch)

    clear_checkpoint()
    logging.info("─" * 50)
    logging.info(f"✓ Backfill complete")
    logging.info(f"  Processed : {processed:,}")
    logging.info(f"  Skipped   : {skipped:,}  (lines before start_line)")
    logging.info(f"  Errors    : {errors:,}   (malformed JSON lines)")


def _flush_batch(r, batch: list, last_line: int):
    pipe = r.pipeline()
    for tx in batch:
        pipe.xadd(STREAM_NAME, {"data": json.dumps(tx)})
    pipe.execute()


# ----------------------------------------------------------------
# ENTRYPOINT
# ----------------------------------------------------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Backfill raw transactions into Redis stream")
    parser.add_argument("--source",     default="transactions.jsonl", help="Path to raw JSONL file")
    parser.add_argument("--batch-size", type=int,   default=1000,  help="Records per Redis pipeline flush")
    parser.add_argument("--delay",      type=float, default=0.01,  help="Seconds to sleep between batches")
    parser.add_argument("--start-line", type=int,   default=None,  help="Override checkpoint, start from this line")
    parser.add_argument("--resume",     action="store_true",       help="Resume from last checkpoint")
    args = parser.parse_args()

    start = 0
    if args.start_line is not None:
        start = args.start_line
    elif args.resume:
        start = load_checkpoint()

    run_backfill(
        source     = args.source,
        batch_size = args.batch_size,
        delay      = args.delay,
        start_line = start,
    )