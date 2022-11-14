from collections import defaultdict
from typing import List
from pandas import DataFrame, Series
import numpy as np


def extract_clustering_from_sns(cmap):
    linkage = cmap.dendrogram_row.linkage
    leaves = cmap.dendrogram_row.reordered_ind
    return linkage, leaves


def extract_orders_from_sns(cmap):
    return cmap.dendrogram_col.reordered_ind, cmap.dendrogram_row.reordered_ind


def estimate_cooccurance_probabilities(tags: List[List[str]], symmetric:bool=False, normalize:bool=True) -> DataFrame:
    all_tags = sorted(np.unique(np.concatenate(tags)))
    cooccurance = defaultdict(lambda: defaultdict(int))
    for tag_list in tags:
        for t1 in tag_list:
            for t2 in tag_list:
                cooccurance[t1][t2] += 1
    cooccurance = DataFrame(cooccurance).loc[all_tags, all_tags].fillna(0).astype(int)
    if not symmetric and normalize:
        cooccurance /= cooccurance.sum(axis=1).values.reshape(-1, 1)
        return cooccurance

    cooccurance = (cooccurance + cooccurance.T) // 2
    if normalize:
        diag_vals = np.diag(cooccurance.values)
        diag_vals = np.repeat(diag_vals, len(diag_vals)).reshape(len(diag_vals), len(diag_vals))
        diag_vals = np.maximum(diag_vals, diag_vals.T)
        cooccurance /= diag_vals

    return cooccurance


def extract_tag_heatmap_json(tag_coocs: DataFrame, cmap_order: List[int]) -> dict:
    tag_ids = dict(Series(np.arange(tag_coocs.shape[0]), tag_coocs.index[cmap_order]))
    coocs = tag_coocs.iloc[cmap_order, cmap_order].stack().round(3)
    coocs = coocs[coocs > 1e-5].reset_index().rename(columns={'level_0': 'tag1', 'level_1': 'tag2', 0: 'cooc'})
    return {
        'freqs': {
            'ti1': [int(tag_ids[t]) for t in coocs['tag1']],
            'ti2': [int(tag_ids[t]) for t in coocs['tag2']],
            'cooc': list(map(float, coocs['cooc']))
        },
        'tags': list(tag_coocs.index[cmap_order])
    }
