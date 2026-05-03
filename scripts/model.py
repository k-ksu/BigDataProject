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
from pyspark.ml.tuning import CrossValidator, ParamGridBuilder
from pyspark.sql import SparkSession
from pyspark.sql import functions as sql_fn
from pyspark.sql import Window

TEAM = "team11"
DATABASE = f"{TEAM}_projectdb"
WAREHOUSE = "project/hive/warehouse"
METASTORE_URI = "thrift://hadoop-02.uni.innopolis.ru:9883"
SEED = 42
TRAIN_USER_PERCENT = 70
VALIDATION_USER_PERCENT = 85
CONTEXT_FRACTION = 0.7
HISTORY_LIMIT = 50
CV_FOLDS = 3
RANKING_K = 100

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
    # stage 3 starts from hive, not from local csv files.
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

    split_interactions = assign_user_split(interactions)
    context, targets = split_context_targets(split_interactions)
    return build_target_rows(targets, context, tracks)


def assign_user_split(interactions):
    """assign each user to one deterministic split."""
    users = interactions.select("user_id").distinct().withColumn(
        "user_bucket",
        sql_fn.expr("pmod(hash(user_id), 100)"),
    )
    users = users.withColumn(
        "split_group",
        sql_fn.when(sql_fn.col("user_bucket") < TRAIN_USER_PERCENT, "train")
        .when(sql_fn.col("user_bucket") < VALIDATION_USER_PERCENT, "validation")
        .otherwise("test"),
    )
    return interactions.join(users.select("user_id", "split_group"), on="user_id")


def split_context_targets(interactions):
    """mark early rows as context and later rows as targets."""
    user_time = Window.partitionBy("user_id").orderBy("ts", "interaction_id", "item_id")
    user_rows = Window.partitionBy("user_id")

    ranked = (
        interactions.withColumn("rn", sql_fn.row_number().over(user_time))
        .withColumn("n_user_rows", sql_fn.count("*").over(user_rows).cast("int"))
        .filter(sql_fn.col("n_user_rows") >= 2)
    )
    cutoff = sql_fn.least(
        sql_fn.greatest(
            sql_fn.floor(sql_fn.col("n_user_rows") * CONTEXT_FRACTION).cast("int"),
            sql_fn.lit(1),
        ),
        sql_fn.col("n_user_rows") - sql_fn.lit(1),
    )
    marked = ranked.withColumn("context_cutoff", cutoff)
    context = marked.filter(sql_fn.col("rn") <= sql_fn.col("context_cutoff"))
    targets = marked.filter(sql_fn.col("rn") > sql_fn.col("context_cutoff"))
    return context, targets


def build_target_rows(targets, context, tracks):
    """build target rows with context-only history features."""
    target_candidates = remove_seen_context_items(targets, context)
    latest_context = latest_context_rows(context, tracks)
    user_history, user_artist_history = context_history_features(latest_context)

    target_rows = target_candidates.join(tracks, on="item_id", how="inner")
    target_rows = with_track_time_features(target_rows)
    target_rows = (
        target_rows.join(user_history, on="user_id", how="left")
        .join(user_artist_history, on=["user_id", "artists_clean"], how="left")
        .withColumn(
            "cv_fold",
            sql_fn.expr(f"pmod(hash(user_id), {CV_FOLDS})").cast("int"),
        )
    )

    # validation and test targets see only their early context rows.
    for column in [
        "prior_user_interactions",
        "prior_user_positives",
        "prior_user_positive_share",
        "prior_user_artist_interactions",
        "prior_user_artist_positives",
        "prior_user_artist_positive_share",
    ]:
        target_rows = target_rows.withColumn(
            column,
            sql_fn.coalesce(sql_fn.col(column), sql_fn.lit(0.0)),
        )

    return target_rows.drop("rn", "n_user_rows", "context_cutoff")


def remove_seen_context_items(targets, context):
    """drop target items already present in user context."""
    seen_items = context.select("user_id", "item_id").distinct()
    # held-out ranking should not recommend tracks already seen in context.
    return targets.join(seen_items, on=["user_id", "item_id"], how="left_anti")


def latest_context_rows(context, tracks):
    """keep the latest context rows for history aggregates."""
    context_tracks = context.join(
        tracks.select("item_id", "artists_clean"),
        on="item_id",
        how="inner",
    )
    context_order = Window.partitionBy("user_id").orderBy(
        sql_fn.col("rn").desc(),
        sql_fn.col("interaction_id").desc(),
    )
    # last 50 keeps recent taste and avoids unbounded history features.
    return (
        context_tracks.withColumn("context_rank", sql_fn.row_number().over(context_order))
        .filter(sql_fn.col("context_rank") <= HISTORY_LIMIT)
        .select("user_id", "artists_clean", "label")
    )


def context_history_features(latest_context):
    """aggregate recent context rows into history features."""
    user_history = (
        latest_context.groupBy("user_id")
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
        latest_context.groupBy("user_id", "artists_clean")
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
    """return rows from disjoint train, validation, and test users."""
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

    # the assignment requires cross validation; folds are user-disjoint.
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


def evaluate_model(name, model, threshold, test, param_names):
    """evaluate the tuned model on test rows."""
    scored = with_rel_score(model.transform(test)).persist(StorageLevel.MEMORY_AND_DISK)
    classified = with_threshold_prediction(scored, threshold).persist(
        StorageLevel.MEMORY_AND_DISK
    )
    evaluator_pr = BinaryClassificationEvaluator(
        labelCol="label",
        rawPredictionCol="rawPrediction",
        metricName="areaUnderPR",
    )
    evaluator_roc = BinaryClassificationEvaluator(
        labelCol="label",
        rawPredictionCol="rawPrediction",
        metricName="areaUnderROC",
    )
    metrics = threshold_metrics(scored, threshold)
    metrics["areaUnderPR"] = evaluator_pr.evaluate(scored)
    metrics["areaUnderROC"] = evaluator_roc.evaluate(scored)
    metrics.update(target_set_metrics(scored))
    metrics.update(ranking_metrics(scored))
    metrics["threshold"] = threshold
    metrics["best_params"] = best_params(model, param_names)
    log.info("%s metrics: %s", name, json.dumps(metrics, sort_keys=True))
    return classified, metrics


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
        .addGrid(logistic_regression.regParam, [0.01, 0.1])
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
        .addGrid(random_forest.numTrees, [50, 100])
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
    first_model = model_results[0]["model"]
    # the assignment wants train/test after feature extraction, not raw rows.
    train_features = first_model.bestModel.transform(train).select("features", "label")
    test_features = first_model.bestModel.transform(test).select("features", "label")
    write_json(train_features, "project/data/train")
    write_json(test_features, "project/data/test")

    evaluation_rows = []
    for result in model_results:
        name = result["name"]
        model = result["model"]
        predictions = result["predictions"]
        metrics = result["metrics"]

        # save the full fitted pipeline so preprocessing is kept with the model.
        model.bestModel.write().overwrite().save(f"project/models/{name}")
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

    results = []
    for name, classifier, grid, param_names in model_specs():
        model, threshold = train_model(name, classifier, grid, train, validation)
        predictions, metrics = evaluate_model(name, model, threshold, test, param_names)
        results.append(
            {
                "name": name,
                "model": model,
                "predictions": predictions,
                "metrics": metrics,
            }
        )

    save_outputs(spark, results, train, test)
    spark.stop()


if __name__ == "__main__":
    main()
