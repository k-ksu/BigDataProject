# Data

This directory contains the dataset files used by the project. The dataset is downloaded automatically by `scripts/data_collection.sh` and is excluded from Git via `.gitignore`.

## Source

- **Kaggle dataset**: [Music Interaction](https://www.kaggle.com/datasets/huynguyen1902/music-interaction/data) (~1.3 GB)
- **Alternative download**: [Google Drive](https://drive.google.com/drive/folders/1DRIoKe-eViuAamsxpYnrJuPoLyf0qTln?usp=sharing)

## Files

| File | Size | Rows | Description |
|---|---|---|---|
| `tracks_features.csv` | 330 MB | 1,204,025 | 24 audio features, metadata, and identifiers for each track |
| `interaction.csv` | 574 MB | 11,808,554 | User-track interaction log (user_id, item_id, interaction_flag, ts) |
| `train.csv` | 257 MB | 626,141 | Provided train split (not used in current pipeline) |
| `test.csv` | 91 MB | 200,575 | Provided test split (not used in current pipeline) |
| `train.json` | – | – | Stage 3 exported training features (Spark JSON) |
| `test.json` | – | – | Stage 3 exported test features (Spark JSON) |

## Usage

```bash
bash scripts/data_collection.sh
```

The script checks whether the files already exist before downloading, so repeated runs are safe.