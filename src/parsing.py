import json
import re
import pandas as pd
from pandas import DataFrame, Series
import html2text
from collections import defaultdict


def replace_single_quotes(x:str):
    return re.sub(string=x, pattern=r"(([ {\[])')|('([:},\]]))", repl=r'\2"\4')


def read_post_data(path: str):
    data = pd.read_csv(path).set_index('_id')
    data['postedAt'] = pd.to_datetime(data['postedAt'])
    data['user'] = data.user.map(lambda x: json.loads(replace_single_quotes(x)) if not pd.isna(x) else None)
    data['userId'] = data.user.map(lambda x: x['_id'] if x is not None else '-')
    data['user'] = data.user.map(lambda x: x['username'] if x is not None else '-')
    data['tags'] = data['tags'].map(lambda x: json.loads(replace_single_quotes(x)))
    data['coauthors'] = data['coauthors'].map(lambda x: json.loads(replace_single_quotes(x)))
    return data


def get_html_parser(ignore_emphasis: bool = True, ignore_links: bool = True, ignore_images: bool = True, ignore_tables: bool = True, body_width: int = None):
    h2t = html2text.HTML2Text()
    h2t.ignore_emphasis = ignore_emphasis
    h2t.ignore_images = ignore_links
    h2t.ignore_links = ignore_images
    h2t.ignore_tables = ignore_tables
    h2t.body_width = body_width
    return h2t


def estimate_posts_per_user(posts: DataFrame, user_list: list = None):
    posts_per_user = defaultdict(lambda: [])
    for pid,uid,coaths in zip(posts.index, posts.userId, posts.coauthors):
        for u in [uid] + [v['_id'] for v in coaths]:
            posts_per_user[u].append(pid)

    posts_per_user = Series(posts_per_user)
    if user_list is not None:
        posts_per_user = posts_per_user.reindex(user_list).map(lambda x: x if not isinstance(x, float) else [])

    return posts_per_user


def estimate_comments_per_user(comments: DataFrame, user_list: list):
    return Series(comments.index.groupby(comments.userId)).reindex(user_list).\
        map(lambda x: list(x) if not isinstance(x, float) else [])


def estimate_relevant_posts_per_user(comments: DataFrame, posts: DataFrame):
    relevant_post_scores_per_user = pd.concat([
        comments[['postId', 'baseScore', 'userId']],
        posts[['baseScore', 'userId']].reset_index(names=['postId'])
    ], ignore_index=True).groupby(['userId', 'postId']).sum().reset_index('postId')

    return relevant_post_scores_per_user


def estimate_tag_scores_per_user(relevant_posts_per_user: Series, tags_per_post: Series, use_base_score:bool = True,
                                 min_tags_per_user: int = 0, min_content_per_user: int = 0, min_users_per_tag: int = 0,
                                 tag_filter: list = None):
    relevant_posts_per_user = relevant_posts_per_user.copy()
    relevant_posts_per_user['tag'] = tags_per_post[relevant_posts_per_user.postId].values

    if not use_base_score:
        relevant_posts_per_user['baseScore'] = 1

    tags_per_user = relevant_posts_per_user.explode('tag')[['tag', 'baseScore']].\
        groupby(['userId', 'tag']).sum().unstack().fillna(0).droplevel(axis=1, level=0)

    if tag_filter is not None:
        tags_per_user = tags_per_user[tag_filter]

    has_tag = (tags_per_user > 0)
    tags_per_user = tags_per_user.iloc[
        (has_tag.sum(axis=1).values >= min_tags_per_user) & (tags_per_user.sum(axis=1).values >= min_content_per_user),
        has_tag.sum().values >= min_users_per_tag
    ]

    return tags_per_user