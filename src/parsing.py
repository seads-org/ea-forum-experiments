import json
import re
import pandas as pd


def replace_single_quotes(x:str):
    return re.sub(string=x, pattern=r"(([ {\[])')|('([:},\]]))", repl=r'\2"\4')


def read_post_data(path: str):
    data = pd.read_csv(path).set_index('_id')
    data['postedAt'] = pd.to_datetime(data['postedAt'])
    data['user'] = data.user.map(lambda x: json.loads(replace_single_quotes(x))['username'] if not pd.isna(x) else '-')
    data['tags'] = data['tags'].map(lambda x: json.loads(replace_single_quotes(x)))
    return data