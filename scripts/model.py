#!/usr/bin/env python3
"""stage 3: distributed spark ml models for music preference prediction."""

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
RANKING_K = 100
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


def prepare_dataset(spark):
    """read stage 2 hive tables and build ml rows."""
    interactions = spark.table(f"{DATABASE}.interactions_part").select(
        sql_fn.col("id").alias("interaction_id"),
        "user_id",
        "item_id",
        "ts",
        sql_fn.col("interaction_flag").cast("double").alias("label"),
    ).filter(sql_fn.col("label").isin(0.0, 1.0))
    tracks = spark.table(f"{DATABASE}.tracks_part").select(
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

    rows = interactions.join(tracks, on="item_id", how="inner")
    rows = assign_temporal_split(rows)
    rows = with_track_time_features(rows)
    rows = add_history_features(rows)
    rows = rows.filter(sql_fn.col("prior_item_count") == 0)
    return rows.withColumn(
        "cv_fold",
        sql_fn.expr(f"pmod(hash(user_id), {CV_FOLDS})").cast("int"),
    ).drop("rn", "n_user_rows", "train_cutoff", "validation_cutoff", "prior_item_count")


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
    """compute user-level ranking metrics over target rows."""
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
        ranked.filter(sql_fn.col("rank") <= RANKING_K)
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
    for rank in range(1, RANKING_K + 1):
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
            sql_fn.least(sql_fn.lit(float(RANKING_K)), sql_fn.col("n_candidates")),
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
        f"precisionAt{RANKING_K}": row["precisionAtK"] or 0.0,
        f"recallAt{RANKING_K}": row["recallAtK"] or 0.0,
        f"ndcgAt{RANKING_K}": row["ndcgAtK"] or 0.0,
        f"mrrAt{RANKING_K}": row["mrrAtK"] or 0.0,
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


def evaluate_scored(name, scored, threshold, raw_prediction_col, params_text):
    """evaluate scored rows on the test split."""
    scored = scored.persist(StorageLevel.MEMORY_AND_DISK)
    classified = with_threshold_prediction(scored, threshold).persist(
        StorageLevel.MEMORY_AND_DISK
    )
    evaluator_pr = BinaryClassificationEvaluator(
        labelCol="label",
        rawPredictionCol=raw_prediction_col,
        metricName="areaUnderPR",
    )
    evaluator_roc = BinaryClassificationEvaluator(
        labelCol="label",
        rawPredictionCol=raw_prediction_col,
        metricName="areaUnderROC",
    )
    metrics = threshold_metrics(scored, threshold)
    metrics["areaUnderPR"] = evaluator_pr.evaluate(scored)
    metrics["areaUnderROC"] = evaluator_roc.evaluate(scored)
    metrics.update(target_set_metrics(scored))
    metrics.update(ranking_metrics(scored))
    metrics["threshold"] = threshold
    metrics["best_params"] = params_text
    log.info("%s metrics: %s", name, json.dumps(metrics, sort_keys=True))
    return classified, metrics


def evaluate_model(name, model, threshold, test, param_names):
    """evaluate the tuned spark ml classifier on test rows."""
    scored = with_rel_score(model.transform(test))
    return evaluate_scored(
        name,
        scored,
        threshold,
        "rawPrediction",
        best_params(model, param_names),
    )


def index_als_data(train, validation, test):
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

    return transform(train), transform(validation), transform(test)


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
    base = base_scores.select(
        "user_id", "item_id", "label", sql_fn.col("rel_score").alias("base_rel_score")
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
        .select("user_id", "item_id", "label", "rel_score")
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
                metrics[f"precisionAt{RANKING_K}"],
                metrics[f"recallAt{RANKING_K}"],
                metrics[f"ndcgAt{RANKING_K}"],
                metrics[f"mrrAt{RANKING_K}"],
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
            f"precisionAt{RANKING_K}",
            f"recallAt{RANKING_K}",
            f"ndcgAt{RANKING_K}",
            f"mrrAt{RANKING_K}",
            "best_params",
        ],
    )
    write_single_csv(evaluation, "project/output/evaluation")


def train_assignment_models(train, validation, test):
    """train model1 and model2 required by the assignment."""
    results = []
    model1_validation_scores = None
    model1_test_scores = None
    for name, classifier, grid, param_names in model_specs():
        model, threshold = train_model(name, classifier, grid, train, validation)
        predictions, metrics = evaluate_model(name, model, threshold, test, param_names)
        if name == "model1":
            model1_validation_scores = (
                with_rel_score(model.transform(validation))
                .select("user_id", "item_id", "label", "rel_score")
                .persist(StorageLevel.MEMORY_AND_DISK)
            )
            model1_test_scores = predictions.select("user_id", "item_id", "label", "rel_score")
        results.append(
            {
                "name": name,
                "model_to_save": model.bestModel,
                "predictions": predictions,
                "metrics": metrics,
            }
        )
    return results, model1_validation_scores, model1_test_scores


def train_recommender_extensions(
    train, validation, test, model1_validation_scores, model1_test_scores
):
    """train als and the hybrid extension."""
    als_data = index_als_data(train, validation, test)
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
        als_training[1],
        "rel_score",
        als_training[2],
    )
    alpha = select_hybrid_alpha(model1_validation_scores, als_validation_scores)
    hybrid_threshold = select_threshold(
        hybrid_scores(model1_validation_scores, als_validation_scores, alpha)
    )
    hybrid_evaluation = evaluate_scored(
        "hybrid",
        hybrid_scores(model1_test_scores, als_evaluation[0], alpha),
        hybrid_threshold,
        "rel_score",
        f"alpha={alpha}; base=model1; als=model3",
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
    data = prepare_dataset(spark)
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

    results, model1_validation_scores, model1_test_scores = train_assignment_models(
        train, validation, test
    )
    results.extend(
        train_recommender_extensions(
            train, validation, test, model1_validation_scores, model1_test_scores
        )
    )

    save_outputs(spark, results, train, test)
    spark.stop()


if __name__ == "__main__":
    main()
