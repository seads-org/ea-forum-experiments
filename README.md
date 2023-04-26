# EA Forum Experiments

To prepare the environment, run `mamba env create -f ./environment.yml`

## Workflow

1. The analysis starts with downloading data using `scripts/data/scrape_ea_forum.py`
2. Data needs to be pre-processed for SBERT training using `notebooks/data/prepare_sbert_train_data.ipynb`
3. To train SBERT on the processed texts, `scripts/train/train_sbert.py` must be used (`.gradient/workflows/train_sbert.yaml`)
4. The trained SBERT can be used to embed the texts with `scripts/data/sbert_embedding.py` must be used (`.gradient/workflows/sbert_embedding.yml`)

## Trends in emotions and sentiments

1. To download the data you need database access, use [`scripts/data/scrape_ea_forum_postgresql.py`](./scripts/data/scrape_ea_forum_postgresql.py).
2. To prepare the data and estimate emotions and sentiments, run [`notebooks/analysis/sentiment.ipynb`](./notebooks/analysis/sentiment.ipynb).
3. Finally, to visualize the trends run [`notebooks/analysis/sentiment_viz.ipynb`](./notebooks/analysis/sentiment_viz.ipynb).
