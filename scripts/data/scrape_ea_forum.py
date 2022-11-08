import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(sys.path[0])))
print(sys.path)

from dotenv import load_dotenv
import wandb

import pandas as pd
from pandas import DataFrame
from datasets import Dataset

from src.forum_gql_utils import *
from src.parsing import get_html_parser
from src.paths import *

from tqdm.auto import tqdm
tqdm.pandas()

load_dotenv()

wandb.login() # relies on WANDB_API_KEY env var
run = wandb.init(project="ea-forum-analysis", job_type="scrape", dir=get_project_root())

# See https://forum.effectivealtruism.org/graphiql for interactive version and https://www.lesswrong.com/posts/LJiGhpq8w4Badr5KJ/graphql-tutorial-for-lesswrong-and-effective-altruism-forum for a manual.

## Posts

# %%
posts = scrape_forum(content='posts', url=EA_GQL_URL, limit=15000, step=5000)
print(f"Scraped {len(posts)} posts")

# %%
post_df = DataFrame(posts).set_index('_id')
post_df['tags'] = post_df.tags.map(lambda x: [v['name'] for v in x])
post_df['postedAt'] = pd.to_datetime(post_df['postedAt'])
post_df['userId'] = post_df.user.map(lambda x: x['_id'] if x is not None else '-')
post_df['user'] = post_df.user.map(lambda x: x['username'] if x is not None else '-')

h2t = get_html_parser()
post_df['body'] = post_df['htmlBody'].progress_map(h2t.handle)
post_df.shape

# %%
post_data = Dataset.from_pandas(post_df)
post_data.save_to_disk(datap('posts'))
# post_df.to_csv(datap('posts.csv'))

art = wandb.Artifact("posts_raw", type="dataset")
art.add_dir(datap('posts'))
run.log_artifact(art)

## Users

# %%
users = scrape_forum(content='users', url=EA_GQL_URL, limit=30000)
print(f"Scraped {len(users)} users")

# %%
user_df = DataFrame(users).set_index('_id')
user_df['posts'] = user_df['posts'].map(lambda x: [v['_id'] for v in x])

Dataset.from_pandas(post_df).save_to_disk(datap('users'))
# user_df.to_csv('./data/users.csv')

art = wandb.Artifact("users_raw", type="dataset")
art.add_dir(datap('users'))
run.log_artifact(art)

## Comments

# %%
comments = scrape_forum(content='comments', url=EA_GQL_URL, limit=200000)
print(f"Scraped {len(comments)} users")

# %%
comments_df = DataFrame(comments).set_index('_id')
comments_df = comments_df[(~comments_df.user.isna()) & (~comments_df.htmlBody.isna())]

comments_df['username'] = comments_df.user.map(lambda x: x['username'])
comments_df['userId'] = comments_df.user.map(lambda x: x['_id'])
del comments_df['user']

comments_df['allVotes'] = comments_df['allVotes'].map(lambda x: ','.join([v['voteType'] for v in x]))

# comments_df['score'] = comments['score'].map(get_number)
# comments_df['baseScore'] = comments['baseScore'].map(get_number)
comments_df['body'] = comments_df.htmlBody.progress_map(h2t.handle)

# %%
Dataset.from_pandas(comments_df).save_to_disk(datap('comments'))
# comments_df.to_csv('./data/comments.csv')

art = wandb.Artifact("comments_raw", type="dataset")
art.add_dir(datap('comments'))
run.log_artifact(art)

run.finish()