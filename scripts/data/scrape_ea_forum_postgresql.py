"""
This scrapes the EA forum via direct PostgreSQL connection.

At time of writing, the DB replica we used was janky when querying JSONB fields. There are two ways to work around this:
1. Manually chunk the query with LIMIT and OFFSET
2. Only query recent posts (e.g. since 2020-01-01)
"""

# %%
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(sys.path[0])))
print(sys.path)

import pandas as pd
import psycopg2
import pyarrow as pa
from datasets import Dataset
from dotenv import load_dotenv
from IPython.display import display
from pandas import DataFrame
from tqdm.auto import tqdm

import wandb
from src.parsing import get_html_parser
from src.paths import *

tqdm.pandas()

load_dotenv()

wandb.login()  # relies on WANDB_API_KEY env var
run = wandb.init(
    project="ea-forum-analysis", job_type="scrape_postgresql", dir=get_project_root()
)

# %%

conn = psycopg2.connect(os.environ["POSTGRESQL_CONNECTION_STRING"])
conn.set_session(
    psycopg2.extensions.ISOLATION_LEVEL_REPEATABLE_READ, readonly=True, deferrable=True
)

# %%

h2t = get_html_parser()

# %%


def retry_query(*query):
    """Execute query with retry up to 10 times on serialization failure"""
    retry_count = 0
    while retry_count < 10:
        try:
            cur = conn.cursor()
            cur.arraysize = 1000  # chunk size
            cur.execute(*query)
            return cur
        except psycopg2.errors.SerializationFailure as e:
            retry_count += 1
            conn.rollback()


def chunked_query():
    chunk_size = 1000
    offset = 0

    while True:
        cur = retry_query(
            """
            SELECT p._id AS "postId", p.title, p."postedAt", p."userId", contents->>'html' as "htmlBody", array_remove(array_agg(t.name), NULL) AS tags, p."voteCount", p."baseScore"
            FROM "Posts" p
            LEFT JOIN "TagRels" tr ON p._id = tr."postId"
            LEFT JOIN "Tags" t ON tr."tagId" = t._id
            WHERE status = 2 /* approved */
            AND NOT (draft OR unlisted OR contents->>'html' IS NULL)
            GROUP BY p._id
            LIMIT %s OFFSET %s;
        """,
            (chunk_size, offset),
        )

        # fetch the results
        results = cur.fetchall()

        yield (cur, results)

        # if the number of rows returned is less than the chunk size,
        # we have reached the end of the results, so we can break the loop
        if len(results) < chunk_size:
            break

        # update the offset for the next iteration
        offset += chunk_size


# %%

# chunked query with retries for querying historic data with write contention (approach 1)
# stream posts from postgresql and save in an arrow file

if not os.path.exists(datap("posts_raw")):
    os.mkdir(datap("posts_raw"))
dest = f"{datap('posts_raw')}/dataset.arrow"

from itertools import *

a, b = tee(chunked_query())

# infer schema
cur, data = next(a)
df = pd.DataFrame(data, columns=[desc[0] for desc in cur.description])
schema = pa.Schema.from_pandas(df)
cur.scroll(-5)

with pa.ipc.new_file(dest, schema) as writer:
    for _, data in tqdm(b):
        print(type(data))
        batch = pa.record_batch(
            [pa.array([x[i] for x in data]) for i in range(len(data[0]))], schema=schema
        )
        writer.write_batch(batch)

# %%

# only select recent posts (approach 2)
# stream posts from postgresql and save in an arrow file

if not os.path.exists(datap("posts_raw")):
    os.mkdir(datap("posts_raw"))
dest = f"{datap('posts_raw')}/dataset.arrow"

with conn:
    with conn.cursor() as cur:
        cur.arraysize = 1000  # chunk size
        cur.execute(
            """
        SELECT p._id AS "postId", p.title, p."postedAt", p."userId", u.username, contents->>'html' as "htmlBody", array_remove(array_agg(t.name), NULL) AS tags, p."voteCount", p."baseScore"
        FROM "Posts" p
        JOIN "filtered_readonly_Users" u ON p."userId" = u._id
        LEFT JOIN "TagRels" tr ON p._id = tr."postId"
        LEFT JOIN "Tags" t ON tr."tagId" = t._id
        WHERE status = 2 /* approved */
        AND NOT (draft OR unlisted OR contents->>'html' IS NULL)
        /* AND p."postedAt" < (now() - interval '1 day') */
        AND p."postedAt" > '2022-01-01'
        GROUP BY p._id, u.username;
        """
        )

        # infer schema
        data = cur.fetchmany(5)  # sample a few rows
        df = pd.DataFrame(data, columns=[desc[0] for desc in cur.description])
        schema = pa.Schema.from_pandas(df)
        cur.scroll(-5)

        with pa.ipc.new_file(dest, schema) as writer:
            for i in tqdm(range(cur.rowcount // cur.arraysize + 1)):
                data = cur.fetchmany()
                if not data:
                    break
                batch = pa.record_batch(
                    [pa.array([x[i] for x in data]) for i in range(len(data[0]))],
                    schema=schema,
                )
                writer.write_batch(batch)

# %%

with pa.ipc.open_file(dest) as reader:
    df = reader.read_pandas()
    print(f"Scraped {df.size} posts")
    display(reader.read_pandas().head())

# %%

post_df = df.set_index("postId")
post_df["body"] = post_df["htmlBody"].progress_map(h2t.handle)

# %%
post_data = Dataset.from_pandas(post_df)
post_data.save_to_disk(datap("posts"))
# post_df.to_csv(datap('posts.csv'))

art = wandb.Artifact("posts_raw", type="dataset")
art.add_dir(datap("posts"))
run.log_artifact(art)

## Comments

# %%

# stream comments from postgresql and save in an arrow file

if not os.path.exists(datap("comments_raw")):
    os.mkdir(datap("comments_raw"))
dest = f"{datap('comments_raw')}/dataset.arrow"

with conn:
    with conn.cursor() as cur:
        cur.arraysize = 1000  # chunk size
        cur.execute(
            """
            SELECT _id as "commentId", "postedAt", "userId", "postId", contents->>'html' as "htmlBody"
            FROM "Comments"
            WHERE NOT (deleted OR rejected OR spam OR contents->>'html' IS NULL OR "userId" IS NULL)
        """
        )

        # infer schema
        data = cur.fetchmany(5)  # sample a few rows
        df = pd.DataFrame(data, columns=[desc[0] for desc in cur.description])
        schema = pa.Schema.from_pandas(df)
        cur.scroll(-5)

        with pa.ipc.new_file(dest, schema) as writer:
            for i in tqdm(range(cur.rowcount // cur.arraysize + 1)):
                data = cur.fetchmany()
                if not data:
                    break
                batch = pa.record_batch(
                    [pa.array([x[i] for x in data]) for i in range(len(data[0]))],
                    schema=schema,
                )
                writer.write_batch(batch)

# %%

with pa.ipc.open_file(dest) as reader:
    df = reader.read_pandas()
    print(f"Scraped {df.size} comments")
    display(reader.read_pandas().head())

# %%

comments_df = df.set_index("commentId")
comments_df["body"] = comments_df.htmlBody.progress_map(h2t.handle)

# %%
Dataset.from_pandas(comments_df).save_to_disk(datap("comments"))
# comments_df.to_csv('./data/comments.csv')

art = wandb.Artifact("comments_raw", type="dataset")
art.add_dir(datap("comments"))
run.log_artifact(art)

# %%
run.finish()
# %%
