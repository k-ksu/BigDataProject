#!/usr/bin/env python3
"""stage 3: distributed spark ml models for music preference prediction."""
# pylint: disable=too-many-lines

import json
import logging
import math

from pyspark import StorageLevel
from pyspark.ml import Pipeline
from pyspark.ml.classification import LogisticRegression, RandomForestClassifier
from pyspark.ml.evaluation import BinaryClassificationEvaluator
from pyspark.ml.feature import (
    HashingTF,
    Imputer,
    OneHotEncoder,
    RegexTokenizer,
    StringIndexer,
    VectorAssembler,
)
from pyspark.ml.functions import vector_to_array
from pyspark.ml.recommendation import ALS
from pyspark.ml.tuning import CrossValidator, ParamGridBuilder
from pyspark.sql import SparkSession
from pyspark.sql import functions as sql_fn
from pyspark.sql import Window

TEAM = "team11"
DATABASE = f"{TEAM}_projectdb"
WAREHOUSE = "project/hive/warehouse"
METASTORE_URI = "thrift://hadoop-02.uni.innopolis.ru:9883"
SEED = 42
TRAIN_ROW_FRACTION = 0.70
VALIDATION_ROW_FRACTION = 0.85
MIN_USER_ROWS = 4
HISTORY_LIMIT = 50
CV_FOLDS = 3
RANKING_KS = [10, 100]
SAMPLED_CANDIDATES_PER_USER = 100
SAMPLED_CANDIDATE_TRIES = 250
ALS_RANKS = [8, 16, 32]
ALS_REG_PARAMS = [0.05, 0.10]
HYBRID_ALPHAS = [0.25, 0.50, 0.75]
ALS_SCORE_FLOOR = 0.20

NUMERIC_COLS = [
    "track_number",
    "disc_number",
    "danceability",
    "energy",
    "loudness",
    "speechiness",
    "acousticness",
    "instrumentalness",
    "liveness",
    "valence",
    "tempo",
    "duration_ms",
    "year",
    "event_year",
    "month_sin",
    "month_cos",
    "dayofweek_sin",
    "dayofweek_cos",
    "hour_sin",
    "hour_cos",
    "prior_user_interactions",
    "prior_user_positives",
    "prior_user_positive_share",
    "prior_user_artist_interactions",
    "prior_user_artist_positives",
    "prior_user_artist_positive_share",
]
CATEGORICAL_COLS = [
    "explicit_str",
    "key_str",
    "mode_str",
    "time_signature_str",
]
THRESHOLDS = [value / 100.0 for value in range(5, 100, 5)]

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)


def create_spark():
    """create a spark session connected to the hive metastore."""
    return (
        SparkSession.builder.appName(f"{TEAM} - stage 3 spark ML")
        .master("yarn")
        .config("hive.metastore.uris", METASTORE_URI)
        .config("spark.sql.warehouse.dir", WAREHOUSE)
        .config("spark.sql.avro.compression.codec", "snappy")
        .config("spark.sql.session.timeZone", "UTC")
        .enableHiveSupport()
        .getOrCreate()
    )


def read_tracks(spark):
    """read track features from the stage 2 hive table."""
    return spark.table(f"{DATABASE}.tracks_part").select(
        sql_fn.col("id").alias("item_id"),
        "artists",
        "track_number",
        "disc_number",
        "explicit",
        "danceability",
        "energy",
        "key",
        "loudness",
        "mode",
        "speechiness",
        "acousticness",
        "instrumentalness",
        "liveness",
        "valence",
        "tempo",
        "duration_ms",
        "time_signature",
        "year",
    ).withColumn(
        "artists_clean",
        sql_fn.coalesce(sql_fn.col("artists"), sql_fn.lit("")),
    )


def prepare_dataset(spark):
    """read stage 2 hive tables and build ml rows."""
    interactions = spark.table(f"{DATABASE}.interactions_part").select(
        sql_fn.col("id").alias("interaction_id"),
        "user_id",
        "item_id",
        "ts",
        sql_fn.col("interaction_flag").cast("double").alias("label"),
    ).filter(sql_fn.col("label").isin(0.0, 1.0))
    tracks = read_tracks(spark)

    rows = interactions.join(tracks, on="item_id", how="inner")
    rows = assign_temporal_split(rows)
    rows = with_track_time_features(rows)
    rows = add_history_features(rows)
    rows = rows.filter(sql_fn.col("prior_item_count") == 0)
    rows = rows.withColumn(
        "cv_fold",
        sql_fn.expr(f"pmod(hash(user_id), {CV_FOLDS})").cast("int"),
    ).drop("rn", "n_user_rows", "train_cutoff", "validation_cutoff", "prior_item_count")
    return rows, tracks


def assign_temporal_split(rows):
    """split each user's history into train, validation, and test periods."""
    user_time = Window.partitionBy("user_id").orderBy("ts", "interaction_id", "item_id")
    user_rows = Window.partitionBy("user_id")
    user_item_time = Window.partitionBy("user_id", "item_id").orderBy(
        "ts",
        "interaction_id",
        "item_id",
    )

    ranked = (
        rows.withColumn("rn", sql_fn.row_number().over(user_time))
        .withColumn("n_user_rows", sql_fn.count("*").over(user_rows).cast("int"))
        .filter(sql_fn.col("n_user_rows") >= MIN_USER_ROWS)
    )
    train_cutoff = sql_fn.least(
        sql_fn.greatest(
            sql_fn.floor(sql_fn.col("n_user_rows") * TRAIN_ROW_FRACTION).cast("int"),
            sql_fn.lit(1),
        ),
        sql_fn.col("n_user_rows") - sql_fn.lit(2),
    )
    validation_cutoff = sql_fn.least(
        sql_fn.greatest(
            sql_fn.floor(sql_fn.col("n_user_rows") * VALIDATION_ROW_FRACTION).cast("int"),
            train_cutoff + sql_fn.lit(1),
        ),
        sql_fn.col("n_user_rows") - sql_fn.lit(1),
    )
    marked = (
        ranked.withColumn("train_cutoff", train_cutoff)
        .withColumn("validation_cutoff", validation_cutoff)
        .withColumn(
            "split_group",
            sql_fn.when(sql_fn.col("rn") <= sql_fn.col("train_cutoff"), "train")
            .when(sql_fn.col("rn") <= sql_fn.col("validation_cutoff"), "validation")
            .otherwise("test"),
        )
        .withColumn(
            "prior_item_count",
            sql_fn.count("*").over(
                user_item_time.rowsBetween(Window.unboundedPreceding, -1)
            ),
        )
    )
    return marked


def add_history_features(rows):
    """add last-50 history features without using validation or test labels."""
    train = rows.filter(sql_fn.col("split_group") == "train")
    future = rows.filter(sql_fn.col("split_group") != "train")
    train_with_history = rolling_train_history(train)
    user_history, user_artist_history = latest_train_history(train)
    future_with_history = (
        future.join(user_history, on="user_id", how="left")
        .join(user_artist_history, on=["user_id", "artists_clean"], how="left")
        .select(train_with_history.columns)
    )
    return fill_history_defaults(train_with_history.unionByName(future_with_history))


def rolling_train_history(train):
    """build prior-only history features for train rows."""
    user_history = Window.partitionBy("user_id").orderBy("rn").rowsBetween(
        -HISTORY_LIMIT,
        -1,
    )
    user_artist_history = Window.partitionBy("user_id", "artists_clean").orderBy(
        "rn"
    ).rowsBetween(
        -HISTORY_LIMIT,
        -1,
    )
    rows = (
        train.withColumn(
            "prior_user_interactions",
            sql_fn.count("label").over(user_history).cast("double"),
        )
        .withColumn("prior_user_positives", sql_fn.sum("label").over(user_history))
        .withColumn(
            "prior_user_artist_interactions",
            sql_fn.count("label").over(user_artist_history).cast("double"),
        )
        .withColumn(
            "prior_user_artist_positives",
            sql_fn.sum("label").over(user_artist_history),
        )
    )
    return rows.withColumn(
        "prior_user_positive_share",
        sql_fn.when(
            sql_fn.col("prior_user_interactions") > 0,
            sql_fn.col("prior_user_positives") / sql_fn.col("prior_user_interactions"),
        ),
    ).withColumn(
        "prior_user_artist_positive_share",
        sql_fn.when(
            sql_fn.col("prior_user_artist_interactions") > 0,
            sql_fn.col("prior_user_artist_positives")
            / sql_fn.col("prior_user_artist_interactions"),
        ),
    )


def latest_train_history(train):
    """aggregate recent train rows for validation and test rows."""
    train_order = Window.partitionBy("user_id").orderBy(
        sql_fn.col("rn").desc(),
        sql_fn.col("interaction_id").desc(),
    )
    # last 50 keeps recent taste and avoids unbounded history features.
    latest_train = (
        train.withColumn("history_rank", sql_fn.row_number().over(train_order))
        .filter(sql_fn.col("history_rank") <= HISTORY_LIMIT)
        .select("user_id", "artists_clean", "label")
    )
    user_history = (
        latest_train.groupBy("user_id")
        .agg(
            sql_fn.count("*").cast("double").alias("prior_user_interactions"),
            sql_fn.sum("label").alias("prior_user_positives"),
        )
        .withColumn(
            "prior_user_positive_share",
            sql_fn.col("prior_user_positives") / sql_fn.col("prior_user_interactions"),
        )
    )
    user_artist_history = (
        latest_train.groupBy("user_id", "artists_clean")
        .agg(
            sql_fn.count("*").cast("double").alias("prior_user_artist_interactions"),
            sql_fn.sum("label").alias("prior_user_artist_positives"),
        )
        .withColumn(
            "prior_user_artist_positive_share",
            sql_fn.col("prior_user_artist_positives")
            / sql_fn.col("prior_user_artist_interactions"),
        )
    )
    return user_history, user_artist_history


def fill_history_defaults(rows):
    """fill missing history values with zeros."""
    for column in [
        "prior_user_interactions",
        "prior_user_positives",
        "prior_user_positive_share",
        "prior_user_artist_interactions",
        "prior_user_artist_positives",
        "prior_user_artist_positive_share",
    ]:
        rows = rows.withColumn(column, sql_fn.coalesce(sql_fn.col(column), sql_fn.lit(0.0)))
    return rows


def with_track_time_features(data):
    """add track, category, and timestamp features."""
    # normalize possible millisecond timestamps before deriving time features.
    ts_seconds = sql_fn.when(
        sql_fn.col("ts") > sql_fn.lit(10_000_000_000),
        (sql_fn.col("ts") / sql_fn.lit(1000)).cast("long"),
    ).otherwise(sql_fn.col("ts").cast("long"))
    event_time = sql_fn.to_timestamp(sql_fn.from_unixtime(ts_seconds))

    return (
        data.withColumn("event_time", event_time)
        .withColumn("event_year", sql_fn.year("event_time").cast("double"))
        .withColumn("event_month", sql_fn.month("event_time").cast("double"))
        .withColumn("event_dayofweek", sql_fn.dayofweek("event_time").cast("double"))
        .withColumn("event_hour", sql_fn.hour("event_time").cast("double"))
        .withColumn("month_sin", sql_fn.sin(2 * math.pi * sql_fn.col("event_month") / 12))
        .withColumn("month_cos", sql_fn.cos(2 * math.pi * sql_fn.col("event_month") / 12))
        .withColumn(
            "dayofweek_sin",
            sql_fn.sin(2 * math.pi * sql_fn.col("event_dayofweek") / 7),
        )
        .withColumn(
            "dayofweek_cos",
            sql_fn.cos(2 * math.pi * sql_fn.col("event_dayofweek") / 7),
        )
        .withColumn("hour_sin", sql_fn.sin(2 * math.pi * sql_fn.col("event_hour") / 24))
        .withColumn("hour_cos", sql_fn.cos(2 * math.pi * sql_fn.col("event_hour") / 24))
        .withColumn("explicit_str", sql_fn.col("explicit").cast("string"))
        .withColumn("key_str", sql_fn.col("key").cast("string"))
        .withColumn("mode_str", sql_fn.col("mode").cast("string"))
        .withColumn("time_signature_str", sql_fn.col("time_signature").cast("string"))
    )


def split_dataset(data):
    """return temporal train, validation, and test rows."""
    train = data.filter(sql_fn.col("split_group") == "train").drop("split_group")
    validation = data.filter(sql_fn.col("split_group") == "validation").drop("split_group")
    test = data.filter(sql_fn.col("split_group") == "test").drop("split_group")
    return train, validation, test


def build_ranking_candidates(train, validation, test, tracks):
    """add sampled unobserved tracks to the test ranking set."""
    interaction_type = test.schema["interaction_id"].dataType
    track_index = indexed_tracks(tracks).persist(StorageLevel.MEMORY_AND_DISK)
    users = test.select("user_id").distinct()
    sampled = sample_unseen_tracks(users, track_index, train, validation, test)
    sampled = sampled.join(candidate_user_context(test), on="user_id", how="inner")
    sampled = sampled.join(
        candidate_artist_context(train),
        on=["user_id", "artists_clean"],
        how="left",
    )
    sampled = fill_history_defaults(with_track_time_features(sampled))
    sampled = (
        sampled.withColumn("interaction_id", sql_fn.lit(None).cast(interaction_type))
        .withColumn("label", sql_fn.lit(0.0))
        .withColumn("is_sampled_candidate", sql_fn.lit(1))
    )
    labeled = test.drop("weight").withColumn("is_sampled_candidate", sql_fn.lit(0))
    sampled = sampled.withColumn(
        "cv_fold",
        sql_fn.expr(f"pmod(hash(user_id), {CV_FOLDS})").cast("int"),
    )
    return labeled.unionByName(sampled.select(labeled.columns))


def indexed_tracks(tracks):
    """add a stable numeric position for deterministic track sampling."""
    order = Window.orderBy("item_id")
    return tracks.withColumn(
        "track_pos",
        (sql_fn.row_number().over(order) - 1).cast("long"),
    )


def sample_unseen_tracks(users, track_index, train, validation, test):
    """sample tracks without known user interaction."""
    track_count = track_index.count()
    offsets = users.withColumn(
        "candidate_offset",
        sql_fn.explode(
            sql_fn.sequence(
                sql_fn.lit(0),
                sql_fn.lit(SAMPLED_CANDIDATE_TRIES - 1),
            )
        ),
    )
    candidates = offsets.withColumn(
        "track_pos",
        sql_fn.expr(
            f"pmod(xxhash64(user_id, candidate_offset, {SEED}), {track_count})"
        ).cast("long"),
    ).join(track_index, on="track_pos", how="inner")
    observed = (
        train.select("user_id", "item_id")
        .unionByName(validation.select("user_id", "item_id"))
        .unionByName(test.select("user_id", "item_id"))
        .distinct()
    )
    sample_order = Window.partitionBy("user_id").orderBy("candidate_offset", "item_id")
    return (
        candidates.join(observed, on=["user_id", "item_id"], how="left_anti")
        .dropDuplicates(["user_id", "item_id"])
        .withColumn("sample_rank", sql_fn.row_number().over(sample_order))
        .filter(sql_fn.col("sample_rank") <= SAMPLED_CANDIDATES_PER_USER)
        .drop("track_pos", "candidate_offset", "sample_rank")
    )


def candidate_user_context(test):
    """get the user state at the test horizon."""
    return test.groupBy("user_id").agg(
        sql_fn.min("ts").alias("ts"),
        sql_fn.max("prior_user_interactions").alias("prior_user_interactions"),
        sql_fn.max("prior_user_positives").alias("prior_user_positives"),
        sql_fn.max("prior_user_positive_share").alias("prior_user_positive_share"),
    )


def candidate_artist_context(train):
    """aggregate train-period user-artist history for candidate tracks."""
    history = (
        train.groupBy("user_id", "artists_clean")
        .agg(
            sql_fn.count("*").cast("double").alias("prior_user_artist_interactions"),
            sql_fn.sum("label").alias("prior_user_artist_positives"),
        )
        .withColumn(
            "prior_user_artist_positive_share",
            sql_fn.col("prior_user_artist_positives")
            / sql_fn.col("prior_user_artist_interactions"),
        )
    )
    return history


def add_class_weights(train, validation, test):
    """add class weights from the train split."""
    # use only train labels so validation and test stay unseen.
    counts = {
        int(row["label"]): row["count"]
        for row in train.groupBy("label").count().collect()
    }
    if 0 not in counts or 1 not in counts:
        raise ValueError("training split must contain both label classes")
    total = counts[0] + counts[1]
    negative_weight = total / (2.0 * counts[0])
    positive_weight = total / (2.0 * counts[1])

    def with_weight(dataframe):
        return dataframe.withColumn(
            "weight",
            sql_fn.when(sql_fn.col("label") == 1.0, positive_weight).otherwise(
                negative_weight
            ),
        )

    log.info("Class weights: negative=%.4f positive=%.4f", negative_weight, positive_weight)
    return with_weight(train), with_weight(validation), with_weight(test)


def feature_stages():
    """return shared preprocessing stages."""
    imputed_cols = [f"{col}_imputed" for col in NUMERIC_COLS]
    indexed_cols = [f"{col}_indexed" for col in CATEGORICAL_COLS]
    encoded_cols = [f"{col}_encoded" for col in CATEGORICAL_COLS]

    return [
        Imputer(inputCols=NUMERIC_COLS, outputCols=imputed_cols),
        # artists are high-cardinality text, so hash tokens instead of indexing them.
        RegexTokenizer(
            inputCol="artists_clean",
            outputCol="artist_tokens",
            pattern="\\W+",
            gaps=True,
        ),
        HashingTF(inputCol="artist_tokens", outputCol="artist_features", numFeatures=512),
        *[
            StringIndexer(inputCol=col, outputCol=indexed, handleInvalid="keep")
            for col, indexed in zip(CATEGORICAL_COLS, indexed_cols)
        ],
        OneHotEncoder(
            inputCols=indexed_cols,
            outputCols=encoded_cols,
            handleInvalid="keep",
        ),
        VectorAssembler(
            inputCols=imputed_cols + encoded_cols + ["artist_features"],
            outputCol="features",
        ),
    ]


def train_model(name, classifier, grid, train, validation):
    """train with cross validation and choose a threshold."""
    evaluator = BinaryClassificationEvaluator(
        labelCol="label",
        rawPredictionCol="rawPrediction",
        metricName="areaUnderPR",
    )
    pipeline = Pipeline(stages=feature_stages() + [classifier])
    validator = CrossValidator(
        estimator=pipeline,
        estimatorParamMaps=grid,
        evaluator=evaluator,
        numFolds=CV_FOLDS,
        foldCol="cv_fold",
        parallelism=2,
        seed=SEED,
    )

    # the assignment requires cross validation; each user stays in one fold.
    log.info("Training %s", name)
    model = validator.fit(train)
    validation_scores = with_rel_score(model.transform(validation))
    # choose the operating threshold on later validation rows, not test rows.
    threshold = select_threshold(validation_scores)
    apply_model_threshold(model, threshold)
    log.info("%s selected threshold: %.2f", name, threshold)
    return model, threshold


def apply_model_threshold(model, threshold):
    """store the selected threshold in the fitted classifier."""
    classifier = model.bestModel.stages[-1]
    if hasattr(classifier, "setThreshold"):
        classifier.setThreshold(threshold)
    else:
        classifier.setThresholds([1.0 - threshold, threshold])


def with_rel_score(predictions):
    """add rel_score as the positive-class probability."""
    # rel_score is the soft score used for ranking available target rows.
    return predictions.withColumn(
        "rel_score",
        vector_to_array(sql_fn.col("probability")).getItem(1),
    )


def with_threshold_prediction(scored, threshold):
    """apply a threshold to rel_score."""
    return scored.withColumn(
        "prediction",
        sql_fn.when(sql_fn.col("rel_score") >= threshold, 1.0).otherwise(0.0),
    )


def threshold_metrics(scored, threshold):
    """compute threshold-dependent binary metrics."""
    classified = with_threshold_prediction(scored, threshold)
    row = classified.agg(
        sql_fn.sum(
            sql_fn.when(
                (sql_fn.col("label") == 1.0) & (sql_fn.col("prediction") == 1.0), 1
            ).otherwise(0)
        ).alias("tp"),
        sql_fn.sum(
            sql_fn.when(
                (sql_fn.col("label") == 0.0) & (sql_fn.col("prediction") == 1.0), 1
            ).otherwise(0)
        ).alias("fp"),
        sql_fn.sum(
            sql_fn.when(
                (sql_fn.col("label") == 1.0) & (sql_fn.col("prediction") == 0.0), 1
            ).otherwise(0)
        ).alias("fn"),
        sql_fn.sum(
            sql_fn.when(sql_fn.col("label") == sql_fn.col("prediction"), 1).otherwise(0)
        ).alias("correct"),
        sql_fn.count("*").alias("total"),
    ).first()

    true_positive = row["tp"]
    false_positive = row["fp"]
    false_negative = row["fn"]
    predicted_positive = true_positive + false_positive
    actual_positive = true_positive + false_negative
    precision = true_positive / predicted_positive if predicted_positive else 0.0
    recall = true_positive / actual_positive if actual_positive else 0.0
    f1_score = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    accuracy = row["correct"] / row["total"] if row["total"] else 0.0
    return {
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "f1": f1_score,
    }


def ranking_metrics(scored):
    """compute user-level ranking metrics over candidate rows."""
    metrics = ranking_set_metrics(scored)
    for ranking_k in RANKING_KS:
        metrics.update(ranking_metrics_at(scored, ranking_k))
    return metrics


def ranking_set_metrics(scored):
    """count rows used in ranking evaluation."""
    sampled_column = (
        sql_fn.col("is_sampled_candidate")
        if "is_sampled_candidate" in scored.columns
        else sql_fn.lit(0)
    )
    row = scored.agg(
        sql_fn.countDistinct("user_id").alias("rankingUsers"),
        sql_fn.count("*").alias("rankingRows"),
        sql_fn.sum(sampled_column).alias("sampledCandidates"),
    ).first()
    return {
        "rankingUsers": row["rankingUsers"],
        "rankingRows": row["rankingRows"],
        "sampledCandidates": row["sampledCandidates"] or 0,
    }


def ranking_metrics_at(scored, ranking_k):
    """compute ranking metrics for one cutoff."""
    user_order = Window.partitionBy("user_id").orderBy(
        sql_fn.col("rel_score").desc(),
        "item_id",
    )
    ranked = scored.select("user_id", "item_id", "label", "rel_score").withColumn(
        "rank",
        sql_fn.row_number().over(user_order),
    )
    users = ranked.groupBy("user_id").agg(
        sql_fn.count("*").cast("double").alias("n_candidates"),
        sql_fn.sum("label").alias("n_positives"),
    )
    top_ranked = (
        ranked.filter(sql_fn.col("rank") <= ranking_k)
        .withColumn(
            "discounted_gain",
            sql_fn.col("label")
            / (sql_fn.log(sql_fn.col("rank") + sql_fn.lit(1.0)) / math.log(2.0)),
        )
        .withColumn(
            "reciprocal_rank",
            sql_fn.when(
                sql_fn.col("label") == 1.0,
                sql_fn.lit(1.0) / sql_fn.col("rank"),
            ).otherwise(0.0),
        )
    )
    top_by_user = top_ranked.groupBy("user_id").agg(
        sql_fn.sum("label").alias("hits"),
        sql_fn.sum("discounted_gain").alias("dcg"),
        sql_fn.max("reciprocal_rank").alias("rr"),
    )

    idcg = None
    for rank in range(1, ranking_k + 1):
        gain = sql_fn.when(
            sql_fn.col("n_positives") >= rank,
            1.0 / math.log2(rank + 1),
        ).otherwise(0.0)
        idcg = gain if idcg is None else idcg + gain

    per_user = (
        users.filter(sql_fn.col("n_positives") > 0)
        .join(top_by_user, on="user_id", how="left")
        .fillna({"hits": 0.0, "dcg": 0.0, "rr": 0.0})
        .withColumn(
            "effective_k",
            sql_fn.least(sql_fn.lit(float(ranking_k)), sql_fn.col("n_candidates")),
        )
        .withColumn("idcg", idcg)
        .withColumn("precision_at_k", sql_fn.col("hits") / sql_fn.col("effective_k"))
        .withColumn("recall_at_k", sql_fn.col("hits") / sql_fn.col("n_positives"))
        .withColumn("ndcg_at_k", sql_fn.col("dcg") / sql_fn.col("idcg"))
        .withColumn("mrr_at_k", sql_fn.col("rr"))
    )
    row = per_user.agg(
        sql_fn.avg("precision_at_k").alias("precisionAtK"),
        sql_fn.avg("recall_at_k").alias("recallAtK"),
        sql_fn.avg("ndcg_at_k").alias("ndcgAtK"),
        sql_fn.avg("mrr_at_k").alias("mrrAtK"),
    ).first()
    return {
        f"precisionAt{ranking_k}": row["precisionAtK"] or 0.0,
        f"recallAt{ranking_k}": row["recallAtK"] or 0.0,
        f"ndcgAt{ranking_k}": row["ndcgAtK"] or 0.0,
        f"mrrAt{ranking_k}": row["mrrAtK"] or 0.0,
    }


def target_set_metrics(scored):
    """count target rows used for final evaluation."""
    row = scored.agg(
        sql_fn.countDistinct("user_id").alias("testUsers"),
        sql_fn.count("*").alias("testRows"),
        sql_fn.sum("label").alias("trueInteractions"),
    ).first()
    return {
        "testUsers": row["testUsers"],
        "testRows": row["testRows"],
        "trueInteractions": row["trueInteractions"] or 0.0,
    }


def select_threshold(scored):
    """pick the threshold with the highest validation f1."""
    # cache because every threshold scans the same validation predictions.
    # coarse 0.05 steps are enough for the assignment and cheap to run.
    scored.persist(StorageLevel.MEMORY_AND_DISK)
    best_threshold = 0.5
    best_f1 = -1.0
    for threshold in THRESHOLDS:
        metrics = threshold_metrics(scored, threshold)
        if metrics["f1"] > best_f1:
            best_threshold = threshold
            best_f1 = metrics["f1"]
    scored.unpersist()
    return best_threshold


def best_params(model, names):
    """format selected hyperparameters."""
    classifier = model.bestModel.stages[-1]
    params = []
    for param, value in classifier.extractParamMap().items():
        if param.name in names:
            params.append(f"{param.name}={value}")
    return "; ".join(sorted(params))


def evaluate_scored(
    name,
    scored,
    eval_options,
    ranking_scored=None,
):
    """evaluate scored rows on the test split."""
    threshold = eval_options["threshold"]
    scored = scored.persist(StorageLevel.MEMORY_AND_DISK)
    classified = with_threshold_prediction(scored, threshold).persist(
        StorageLevel.MEMORY_AND_DISK
    )
    if ranking_scored is None:
        ranking_scored = scored
    ranking_scored = ranking_scored.persist(StorageLevel.MEMORY_AND_DISK)
    evaluator_pr = BinaryClassificationEvaluator(
        labelCol="label",
        rawPredictionCol=eval_options["raw_prediction_col"],
        metricName="areaUnderPR",
    )
    evaluator_roc = BinaryClassificationEvaluator(
        labelCol="label",
        rawPredictionCol=eval_options["raw_prediction_col"],
        metricName="areaUnderROC",
    )
    metrics = threshold_metrics(scored, threshold)
    metrics["areaUnderPR"] = evaluator_pr.evaluate(scored)
    metrics["areaUnderROC"] = evaluator_roc.evaluate(scored)
    metrics.update(target_set_metrics(scored))
    metrics.update(ranking_metrics(ranking_scored))
    metrics["threshold"] = threshold
    metrics["best_params"] = eval_options["params_text"]
    log.info("%s metrics: %s", name, json.dumps(metrics, sort_keys=True))
    return classified, metrics, ranking_scored


def evaluate_model(name, model, threshold, test_sets, param_names):
    """evaluate the tuned spark ml classifier on test rows."""
    test = test_sets["labeled"]
    ranking_test = test_sets["ranking"]
    scored = with_rel_score(model.transform(test))
    ranking_scored = with_rel_score(model.transform(ranking_test))
    return evaluate_scored(
        name,
        scored,
        {
            "threshold": threshold,
            "raw_prediction_col": "rawPrediction",
            "params_text": best_params(model, param_names),
        },
        ranking_scored,
    )


def index_als_data(train, validation, test, ranking_test):
    """create integer ids for als from train ids only."""
    indexer = Pipeline(
        stages=[
            StringIndexer(inputCol="user_id", outputCol="user_index", handleInvalid="keep"),
            StringIndexer(inputCol="item_id", outputCol="item_index", handleInvalid="keep"),
        ]
    )
    index_model = indexer.fit(train)

    def transform(dataframe):
        return (
            index_model.transform(dataframe)
            .withColumn("user_index", sql_fn.col("user_index").cast("int"))
            .withColumn("item_index", sql_fn.col("item_index").cast("int"))
        )

    return transform(train), transform(validation), transform(test), transform(ranking_test)


def score_als(model, data):
    """turn als predictions into rel_score."""
    scored = model.transform(data)
    has_prediction = ~(sql_fn.col("als_prediction").isNull() | sql_fn.isnan("als_prediction"))
    raw_score = sql_fn.when(has_prediction, sql_fn.col("als_prediction")).otherwise(
        sql_fn.lit(0.0)
    )
    raw_rel_score = sql_fn.lit(1.0) / (
        sql_fn.lit(1.0) + sql_fn.exp(-sql_fn.col("als_raw_score"))
    )
    als_rel_score = sql_fn.greatest(raw_rel_score, sql_fn.lit(ALS_SCORE_FLOOR))
    return (
        scored.withColumn("als_raw_score", raw_score)
        .withColumn("rel_score", sql_fn.when(has_prediction, als_rel_score).otherwise(
            sql_fn.lit(ALS_SCORE_FLOOR)
        ))
        .drop("als_prediction")
    )


def validation_auc(scored):
    """measure validation ranking quality."""
    evaluator = BinaryClassificationEvaluator(
        labelCol="label",
        rawPredictionCol="rel_score",
        metricName="areaUnderPR",
    )
    return evaluator.evaluate(scored)


def train_als_model(train, validation):
    """fit als grid and select the best validation model."""
    ratings = train.select(
        "user_index",
        "item_index",
        sql_fn.col("label").alias("rating"),
    )
    best_model = None
    best_params_text = ""
    best_metric = -1.0

    for rank in ALS_RANKS:
        for reg_param in ALS_REG_PARAMS:
            als = ALS(
                userCol="user_index",
                itemCol="item_index",
                ratingCol="rating",
                predictionCol="als_prediction",
                rank=rank,
                regParam=reg_param,
                maxIter=10,
                nonnegative=True,
                coldStartStrategy="nan",
                seed=SEED,
            )
            model = als.fit(ratings)
            validation_scores = score_als(model, validation)
            metric = validation_auc(validation_scores)
            log.info(
                "model3 candidate rank=%s regParam=%s areaUnderPR=%.6f",
                rank,
                reg_param,
                metric,
            )
            if metric > best_metric:
                best_model = model
                best_metric = metric
                best_params_text = f"rank={rank}; regParam={reg_param}"

    validation_scores = score_als(best_model, validation)
    threshold = select_threshold(validation_scores)
    log.info("model3 selected threshold: %.2f", threshold)
    return best_model, threshold, best_params_text


def hybrid_scores(base_scores, als_scores, alpha):
    """combine model1 probability with als relevance."""
    base_cols = ["user_id", "item_id", "label"]
    if "is_sampled_candidate" in base_scores.columns:
        base_cols.append("is_sampled_candidate")
    base = base_scores.select(
        *base_cols,
        sql_fn.col("rel_score").alias("base_rel_score"),
    )
    als = als_scores.select(
        "user_id", "item_id", sql_fn.col("rel_score").alias("als_rel_score")
    )
    return (
        base.join(als, on=["user_id", "item_id"], how="left")
        .withColumn(
            "als_rel_score",
            sql_fn.coalesce(sql_fn.col("als_rel_score"), sql_fn.lit(ALS_SCORE_FLOOR)),
        )
        .withColumn(
            "rel_score",
            sql_fn.lit(alpha) * sql_fn.col("als_rel_score")
            + sql_fn.lit(1.0 - alpha) * sql_fn.col("base_rel_score"),
        )
        .select(*base_cols, "rel_score")
    )


def select_hybrid_alpha(base_scores, als_scores):
    """select hybrid alpha on validation rows."""
    best_alpha = HYBRID_ALPHAS[0]
    best_metric = -1.0
    for alpha in HYBRID_ALPHAS:
        scored = hybrid_scores(base_scores, als_scores, alpha)
        metric = validation_auc(scored)
        log.info("hybrid candidate alpha=%.2f areaUnderPR=%.6f", alpha, metric)
        if metric > best_metric:
            best_alpha = alpha
            best_metric = metric
    return best_alpha


def model_specs():
    """return the two assignment-required model configs."""
    logistic_regression = LogisticRegression(
        labelCol="label",
        featuresCol="features",
        weightCol="weight",
        maxIter=50,
    )
    logistic_grid = (
        ParamGridBuilder()
        .addGrid(logistic_regression.regParam, [0.001, 0.01, 0.1])
        .addGrid(logistic_regression.elasticNetParam, [0.0, 0.5])
        .build()
    )

    random_forest = RandomForestClassifier(
        labelCol="label",
        featuresCol="features",
        weightCol="weight",
        seed=SEED,
    )
    forest_grid = (
        ParamGridBuilder()
        .addGrid(random_forest.numTrees, [50, 100, 150])
        .addGrid(random_forest.maxDepth, [5, 8])
        .build()
    )

    return [
        ("model1", logistic_regression, logistic_grid, ["elasticNetParam", "regParam"]),
        ("model2", random_forest, forest_grid, ["maxDepth", "numTrees"]),
    ]


def write_single_csv(dataframe, path):
    """write one csv part directory with a header."""
    dataframe.coalesce(1).write.mode("overwrite").option("header", "true").csv(path)


def write_json(dataframe, path):
    """write a json directory."""
    dataframe.write.mode("overwrite").json(path)


def save_outputs(spark, model_results, train, test):
    """persist assignment artifacts and soft-score outputs."""
    first_model = model_results[0]["model_to_save"]
    train_features = first_model.transform(train).select("features", "label")
    test_features = first_model.transform(test).select("features", "label")
    write_json(train_features, "project/data/train")
    write_json(test_features, "project/data/test")

    evaluation_rows = []
    for result in model_results:
        name = result["name"]
        model_to_save = result["model_to_save"]
        predictions = result["predictions"]
        metrics = result["metrics"]

        # save the full fitted pipeline so preprocessing is kept with the model.
        if model_to_save is not None:
            model_to_save.write().overwrite().save(f"project/models/{name}")
        write_single_csv(
            predictions.select("label", "prediction"),
            f"project/output/{name}_predictions",
        )
        write_single_csv(
            predictions.select("user_id", "item_id", "label", "prediction", "rel_score"),
            f"project/output/{name}_scores",
        )
        evaluation_rows.append(
            (
                name,
                metrics["areaUnderPR"],
                metrics["areaUnderROC"],
                metrics["testUsers"],
                metrics["testRows"],
                metrics["trueInteractions"],
                metrics["threshold"],
                metrics["accuracy"],
                metrics["precision"],
                metrics["recall"],
                metrics["f1"],
                metrics["rankingUsers"],
                metrics["rankingRows"],
                metrics["sampledCandidates"],
                metrics["precisionAt10"],
                metrics["recallAt10"],
                metrics["ndcgAt10"],
                metrics["mrrAt10"],
                metrics["precisionAt100"],
                metrics["recallAt100"],
                metrics["ndcgAt100"],
                metrics["mrrAt100"],
                metrics["best_params"],
            )
        )

    evaluation = spark.createDataFrame(
        evaluation_rows,
        [
            "model",
            "areaUnderPR",
            "areaUnderROC",
            "testUsers",
            "testRows",
            "trueInteractions",
            "threshold",
            "accuracy",
            "precision",
            "recall",
            "f1",
            "rankingUsers",
            "rankingRows",
            "sampledCandidates",
            "precisionAt10",
            "recallAt10",
            "ndcgAt10",
            "mrrAt10",
            "precisionAt100",
            "recallAt100",
            "ndcgAt100",
            "mrrAt100",
            "best_params",
        ],
    )
    write_single_csv(evaluation, "project/output/evaluation")


def train_assignment_models(train, validation, test_sets):
    """train model1 and model2 required by the assignment."""
    results = []
    model1_scores = {}
    for name, classifier, grid, param_names in model_specs():
        model, threshold = train_model(name, classifier, grid, train, validation)
        predictions, metrics, ranking_scores = evaluate_model(
            name,
            model,
            threshold,
            test_sets,
            param_names,
        )
        if name == "model1":
            model1_scores["validation"] = (
                with_rel_score(model.transform(validation))
                .select("user_id", "item_id", "label", "rel_score")
                .persist(StorageLevel.MEMORY_AND_DISK)
            )
            model1_scores["test"] = predictions.select(
                "user_id",
                "item_id",
                "label",
                "rel_score",
            )
            model1_scores["ranking"] = ranking_scores.select(
                "user_id",
                "item_id",
                "label",
                "rel_score",
                "is_sampled_candidate",
            )
        results.append(
            {
                "name": name,
                "model_to_save": model.bestModel,
                "predictions": predictions,
                "metrics": metrics,
            }
        )
    return results, model1_scores


def train_recommender_extensions(train, validation, test_sets, model1_scores):
    """train als and the hybrid extension."""
    test = test_sets["labeled"]
    ranking_test = test_sets["ranking"]
    als_data = index_als_data(train, validation, test, ranking_test)
    for dataframe in als_data:
        dataframe.persist(StorageLevel.MEMORY_AND_DISK)

    als_training = train_als_model(als_data[0], als_data[1])
    als_validation_scores = (
        score_als(als_training[0], als_data[1])
        .select("user_id", "item_id", "label", "rel_score")
        .persist(StorageLevel.MEMORY_AND_DISK)
    )
    als_evaluation = evaluate_scored(
        "model3",
        score_als(als_training[0], als_data[2]),
        {
            "threshold": als_training[1],
            "raw_prediction_col": "rel_score",
            "params_text": als_training[2],
        },
        score_als(als_training[0], als_data[3]),
    )
    alpha = select_hybrid_alpha(model1_scores["validation"], als_validation_scores)
    hybrid_threshold = select_threshold(
        hybrid_scores(model1_scores["validation"], als_validation_scores, alpha)
    )
    hybrid_evaluation = evaluate_scored(
        "hybrid",
        hybrid_scores(model1_scores["test"], als_evaluation[0], alpha),
        {
            "threshold": hybrid_threshold,
            "raw_prediction_col": "rel_score",
            "params_text": f"alpha={alpha}; base=model1; als=model3",
        },
        hybrid_scores(model1_scores["ranking"], als_evaluation[2], alpha),
    )
    return [
        {
            "name": "model3",
            "model_to_save": als_training[0],
            "predictions": als_evaluation[0],
            "metrics": als_evaluation[1],
        },
        {
            "name": "hybrid",
            "model_to_save": None,
            "predictions": hybrid_evaluation[0],
            "metrics": hybrid_evaluation[1],
        },
    ]


def main():
    """run the stage 3 training and evaluation pipeline."""
    spark = create_spark()
    data, tracks = prepare_dataset(spark)
    train, validation, test = split_dataset(data)
    train, validation, test = add_class_weights(train, validation, test)
    train.persist(StorageLevel.MEMORY_AND_DISK)
    validation.persist(StorageLevel.MEMORY_AND_DISK)
    test.persist(StorageLevel.MEMORY_AND_DISK)
    log.info(
        "Split sizes: train=%d validation=%d test=%d",
        train.count(),
        validation.count(),
        test.count(),
    )
    ranking_test = build_ranking_candidates(train, validation, test, tracks).persist(
        StorageLevel.MEMORY_AND_DISK
    )
    log.info("Ranking candidate rows: %d", ranking_test.count())

    test_sets = {"labeled": test, "ranking": ranking_test}
    results, model1_scores = train_assignment_models(train, validation, test_sets)
    results.extend(
        train_recommender_extensions(train, validation, test_sets, model1_scores)
    )

    save_outputs(spark, results, train, test)
    spark.stop()


if __name__ == "__main__":
    main()
