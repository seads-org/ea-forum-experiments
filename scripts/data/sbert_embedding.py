# %%
import pandas as pd
from pandas import DataFrame
from tqdm.auto import tqdm

from datasets import Dataset
from sentence_transformers import SentenceTransformer

from os import getenv
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(sys.path[0])))

from src.text_split import extract_paragraphs, split_long_paragraphs, collapse_paragraphs_iteratively
from src.paths import get_project_root, datap

import wandb
from dotenv import load_dotenv
load_dotenv()

tqdm.pandas()

# %%
model_name = getenv("SBERT_EMB_MODEL", "n8-all-mpnet-base-v2")
batch_size = int(getenv("SBERT_EMB_BATCH_SIZE", 384))
# model_name = "n8-all-mpnet-base-v2"
# model_name = 'all-MiniLM-L12-v2:baseline'

# %%
wandb.login() # relies on WANDB_API_KEY env var
run = wandb.init(
    project="ea-forum-analysis", job_type="processing", dir=get_project_root(),
    config={"model_name": model_name, "batch_size": batch_size}
)

# %%
if model_name.endswith(":baseline"):
    run.config.update({'model_version': 'baseline'})
    model = SentenceTransformer.load(model_name.split(":")[0])
else:
    art = run.use_artifact(f"sbert:{model_name}")
    run.config.update({'model_version': art.version})
    model = SentenceTransformer.load(art.download())

art = run.use_artifact("posts_raw:latest")
run.config.update({'data_version': art.version})
data = Dataset.load_from_disk(art.download()).to_pandas()
data = data[data['body'].map(len) > 50].copy()
data.shape

# %% [markdown]
# ## Split data

# %%
max_n_words = 400
data['paragraphs'] = data.body.progress_map(extract_paragraphs)
data['paragraphs'] = data.paragraphs.progress_map(lambda p: split_long_paragraphs(p, max_n_words=max_n_words))
data['paragraphs_split'] = data.paragraphs.progress_map(lambda x: collapse_paragraphs_iteratively(x, max_n_words=max_n_words))

# %%
par_split_df = pd.concat([
    DataFrame({'postId': pid, 'text': r.paragraphs_split.text.values})
    for pid,r in data.iterrows()
], ignore_index=True)
par_split_df.shape

# %% [markdown]
# ## Embed

# %% [markdown]
# ### By paragraphs

# %%
pars_encoded = model.encode(par_split_df.text, batch_size=batch_size, show_progress_bar=True)

# %%
DataFrame(pars_encoded).groupby(par_split_df.postId.values).mean().to_csv(datap("posts_encoded.csv"))

art = wandb.Artifact("posts_encoded", type="dataset", metadata={'model_name': model_name})
art.add_file(datap("posts_encoded.csv"))
run.log_artifact(art, aliases=[model_name.replace(":", "-")])

# %%
wandb.finish()