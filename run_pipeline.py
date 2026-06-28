import sys
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

base_dir = Path(r"c:\Users\Nisarga N\OneDrive\Documents\My Projects\coderbeach\customer-lifetime-value-prediction")
sys.path.append(str(base_dir))

from src.data_loader import DataLoader
from src.data_cleaner import DataCleaner
from src.feature_engineer import FeatureEngineer
from src.rfm_analyzer import RFMAnalyzer
from src.model_trainer import ModelTrainer
from src.model_evaluator import ModelEvaluator

# Configure plotting styles
plt.rcParams.update({
    'figure.facecolor': '#0d1117', 'axes.facecolor': '#161b22',
    'axes.edgecolor': '#30363d', 'axes.labelcolor': '#c9d1d9',
    'text.color': '#c9d1d9', 'xtick.color': '#8b949e',
    'ytick.color': '#8b949e', 'grid.color': '#21262d',
    'font.size': 11, 'axes.titlesize': 14,
})

def main():
    print("======================================================================")
    print("RUNNING END-TO-END CLTV SYSTEM PIPELINE")
    print("======================================================================")

    # 1. Ingest Raw & Clean
    DATA_RAW = base_dir / "data" / "raw"
    DATA_PROCESSED = base_dir / "data" / "processed"
    DATA_FEATURES = base_dir / "data" / "features"
    MODELS_DIR = base_dir / "models" / "saved_models"
    VIZ_EDA = base_dir / "visualizations" / "eda"
    VIZ_RFM = base_dir / "visualizations" / "rfm"
    VIZ_MODEL = base_dir / "visualizations" / "model"
    
    # Ensure all dirs exist
    for d in [DATA_PROCESSED, DATA_FEATURES, MODELS_DIR, VIZ_EDA, VIZ_RFM, VIZ_MODEL]:
        d.mkdir(parents=True, exist_ok=True)

    loader = DataLoader(DATA_RAW)
    df = loader.load_processed(DATA_PROCESSED / "cleaned_retail.csv")
    print(f"Loaded processed data: {len(df):,} transactions")

    # 2. RFM Segmentation
    print("\n--- Running RFM Segmentation ---")
    ref_date = pd.to_datetime(df["InvoiceDate"]).max() + pd.Timedelta(days=1)
    rfm_base = df.groupby("Customer ID").agg(
        Recency=("InvoiceDate", lambda x: (ref_date - pd.to_datetime(x).max()).days),
        Frequency=("Invoice", "nunique"),
        Monetary=("Revenue", "sum")
    ).reset_index()
    
    rfm_analyzer = RFMAnalyzer(rfm_base)
    df_rfm, summary = rfm_analyzer.run_full_analysis()
    df_rfm.to_csv(DATA_PROCESSED / "rfm_segments.csv", index=False)
    print("Saved RFM segments to data/processed/rfm_segments.csv")
    
    # Plot segment counts
    plt.figure(figsize=(12, 6))
    sns.barplot(data=summary, x="Customer_Count", y="Segment", palette="viridis")
    plt.title("Customer Segment Sizes")
    plt.xlabel("Number of Customers")
    plt.ylabel("Segment")
    plt.tight_layout()
    plt.savefig(VIZ_RFM / "01_segment_sizes.png", dpi=150, facecolor='#0d1117')
    plt.close()
    print("Saved segment size plot to visualizations/rfm/01_segment_sizes.png")

    # 3. Feature Engineering (Out-of-time Split)
    print("\n--- Running Feature Engineering ---")
    fe = FeatureEngineer(df)
    # Split at 2011-09-01 (approx last 90 days of dataset as prediction target)
    split_date = pd.Timestamp("2011-09-01")
    master_table = fe.build_master_feature_table(split_date, prediction_days=90)
    master_table.to_csv(DATA_FEATURES / "customer_features.csv", index=False)
    print("Saved customer features to data/features/customer_features.csv")

    # 4. ML Model Training
    print("\n--- Training ML Models ---")
    trainer = ModelTrainer(master_table, target_col="target_revenue")
    X_train, X_test, y_train, y_test, feature_names = trainer.prepare_data(test_size=0.2, random_state=42)
    
    # Train all 6 algorithms
    results = trainer.train_all_models(X_train, y_train, tune_hyperparams=True)

    # 5. Evaluation and Registry Logs
    print("\n--- Evaluating Models and Serialization ---")
    evaluator = ModelEvaluator(y_test, feature_names)
    summary_df = evaluator.generate_evaluation_summary(trainer.models, X_test)
    print("\nMODEL PERFORMANCE COMPARISON:")
    print(summary_df.to_string(index=False))
    
    # Save comparison table
    summary_df.to_csv(base_dir / "models" / "model_comparison.csv", index=False)

    # Save models and update registry
    for name, model in trainer.models.items():
        row = summary_df[summary_df["Model"] == name].iloc[0]
        metrics = {"MAE": float(row["MAE"]), "RMSE": float(row["RMSE"]), "R2": float(row["R2"])}
        trainer.save_model(model, name, MODELS_DIR, metrics)
        
    # Generate charts for the best model
    best_model_name = summary_df.iloc[0]["Model"]
    print(f"\nBest Model: {best_model_name}. Generating residual and explainability plots...")
    best_model = trainer.models[best_model_name]
    
    y_pred = best_model.predict(X_test)
    evaluator.plot_residuals(y_pred, best_model_name, VIZ_MODEL / "residuals.png")
    evaluator.plot_prediction_error(y_pred, best_model_name, VIZ_MODEL / "pred_error.png")
    
    # Explainability via SHAP
    evaluator.explain_with_shap(best_model, X_train, X_test, VIZ_MODEL)
    
    print("\n======================================================================")
    print("PIPELINE EXECUTED SUCCESSFULLY - ALL ARTIFACTS GENERATED")
    print("======================================================================")

if __name__ == "__main__":
    main()
