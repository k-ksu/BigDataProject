# Models

This directory stores the best models selected by hyperparameter tuning in Stage 3. Each subdirectory contains a trained Spark ML pipeline.

## Subdirectories

| Model | Subdirectory | Algorithm | Hyperparameters |
|---|---|---|---|
| Model 1 | `model1/` | Logistic Regression | `elasticNetParam=0.0; regParam=0.001` (threshold = 0.15)[reference:11] |
| Model 2 | `model2/` | Random Forest | `maxDepth=8; numTrees=150` (threshold = 0.30)[reference:12] |

## Contents

Each model directory contains:

- `metadata/` – Spark ML pipeline metadata
- `stages/` – Serialised pipeline stages (vector assembler, indexers, etc.)

## Loading a Model

```python
from pyspark.ml import PipelineModel
model = PipelineModel.load("models/model1")
predictions = model.transform(test_data)
```

## Notes
Models are trained on YARN and saved to HDFS first, then fetched locally by scripts/stage3.sh.

These are the best models from 3‑fold cross‑validation with 6‑combination grid search.