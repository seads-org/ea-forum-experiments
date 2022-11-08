# %%
from torch.utils.data import DataLoader
import math
from sentence_transformers import SentenceTransformer, losses, InputExample
from sentence_transformers.evaluation import EmbeddingSimilarityEvaluator
from datasets import DatasetDict
import logging

from datetime import datetime

from os import getenv
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(sys.path[0])))

from src.paths import get_project_root, abs_path
import wandb
from dotenv import load_dotenv
load_dotenv()

# %%
model_name = getenv("SBERT_MODEL", 'all-mpnet-base-v2')
train_batch_size = int(getenv("SBERT_BATCH_SIZE", 12))
num_epochs = int(getenv("SBERT_N_EPOCHS", 1))
evaluation_steps = int(getenv("SBERT_EVALUATION_STEPS", 1000))

model_save_path = abs_path("models", f'{model_name}-{datetime.now().strftime("%Y-%m-%d_%H-%M-%S")}')

# %%
wandb.login() # relies on WANDB_API_KEY env var
run = wandb.init(
    project="ea-forum-analysis", job_type="training", dir=get_project_root(),
    config={
        "model_name": model_name,
        "train_batch_size": train_batch_size,
        "num_epochs": num_epochs
    }
)

# %%
art = run.use_artifact("post_pairs:latest")
run.config.update({'data_version': art.version})

data = DatasetDict.load_from_disk(art.download())
data

# %%
model = SentenceTransformer(model_name).cuda()
wandb.watch(model, log="all", log_freq=1000)

# %%
train_samples = [InputExample(texts=ts, label=float(l)) for ts,l in zip(zip(data['train']['src_text'], data['train']['dst_text']), data['train']['sims'])]
train_loader = DataLoader(train_samples, batch_size=train_batch_size, shuffle=True)
train_loss = losses.CosineSimilarityLoss(model=model)

# %%
evaluator = EmbeddingSimilarityEvaluator(data['dev']['src_text'], data['dev']['dst_text'], data['dev']['sims'])

# %%
warmup_steps = math.ceil(len(train_loader) * num_epochs * 0.1) #10% of train data for warm-up
warmup_steps

# %%
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

# %%
score = evaluator(model)
wandb.log({'score': score, 'epoch': -1, 'steps': 0})
score

# %%
model.fit(
    train_objectives=[(train_loader, train_loss)],
    evaluator=evaluator,
    epochs=num_epochs,
    evaluation_steps=evaluation_steps,
    warmup_steps=warmup_steps,
    output_path=model_save_path,
    callback=lambda score, epoch, steps: wandb.log({'score': score, 'epoch': epoch, 'steps': steps})
)

# %%
art = wandb.Artifact("sbert", type="model", metadata={'model_name': model_name, 'data_version': art.version})
art.add_dir(model_save_path)
run.log_artifact(art, aliases=[model_name])

# %%
wandb.finish()
