import json
import re
import pandas as pd
import html2text


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