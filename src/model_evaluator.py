"""
Model Evaluation and Metrics Module for CLTV Prediction System.
Handles validation metrics, residual plotting, error distributions, and SHAP explainability.
"""

import logging
from pathlib import Path
from typing import Dict, List, Any, Tuple, Union
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import shap

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("ModelEvaluator")

class ModelEvaluator:
    """
    Computes performance metrics and generates explainability visualizations
    for Customer Lifetime Value regression models.
    """

    def __init__(self, y_test: Union[np.ndarray, pd.Series], feature_names: List[str]):
        """
        Initializes ModelEvaluator.
        
        Args:
            y_test: True future revenue values.
            feature_names: List of feature names.
        """
        self.y_test = np.asarray(y_test)
        self.feature_names = feature_names

    def calculate_metrics(self, y_pred: np.ndarray) -> Dict[str, float]:
        """
        Calculates MAE, RMSE, MAPE, and R2 scores.
        
        Args:
            y_pred: Predicted values.
            
        Returns:
            Dict: Dictionary containing standard regression metrics.
        """
        mae = mean_absolute_error(self.y_test, y_pred)
        rmse = np.sqrt(mean_squared_error(self.y_test, y_pred))
        r2 = r2_score(self.y_test, y_pred)
        
        # Mean Absolute Percentage Error (avoiding zero division)
        non_zeros = self.y_test > 0
        if non_zeros.sum() > 0:
            mape = np.mean(np.abs((self.y_test[non_zeros] - y_pred[non_zeros]) / self.y_test[non_zeros])) * 100
        else:
            mape = 0.0

        return {
            "MAE": float(mae),
            "RMSE": float(rmse),
            "R2": float(r2),
            "MAPE": float(mape)
        }

    def generate_evaluation_summary(self, models_dict: Dict[str, Any], X_test: Union[pd.DataFrame, np.ndarray]) -> pd.DataFrame:
        """
        Evaluates a dictionary of models on the test set and returns a comparison DataFrame.
        """
        summary_rows = []
        for name, model in models_dict.items():
            y_pred = model.predict(X_test)
            metrics = self.calculate_metrics(y_pred)
            metrics["Model"] = name
            summary_rows.append(metrics)
            
        summary_df = pd.DataFrame(summary_rows)
        # Reorder columns
        summary_df = summary_df[["Model", "MAE", "RMSE", "R2", "MAPE"]]
        return summary_df.sort_values(by="R2", ascending=False)

    def plot_residuals(self, y_pred: np.ndarray, model_name: str, save_path: Path) -> None:
        """
        Generates and saves a residual plot.
        """
        residuals = self.y_test - y_pred
        
        plt.figure(figsize=(10, 6))
        sns.scatterplot(x=y_pred, y=residuals, alpha=0.5, color="#58a6ff")
        plt.axhline(y=0, color="#f85149", linestyle="--", linewidth=2)
        plt.xlabel("Predicted CLTV (£)")
        plt.ylabel("Residual (Actual - Predicted) (£)")
        plt.title(f"Residual Plot - {model_name}")
        plt.grid(True, linestyle=":", alpha=0.6)
        
        plt.tight_layout()
        plt.savefig(save_path, dpi=150, facecolor="#0d1117")
        plt.close()
        logger.info(f"Saved residual plot for {model_name} to {save_path}")

    def plot_prediction_error(self, y_pred: np.ndarray, model_name: str, save_path: Path) -> None:
        """
        Generates and saves an actual vs predicted scatter plot.
        """
        plt.figure(figsize=(10, 6))
        sns.scatterplot(x=self.y_test, y=y_pred, alpha=0.5, color="#3fb950")
        
        # Perfect fit line
        max_val = max(self.y_test.max(), y_pred.max())
        min_val = min(self.y_test.min(), y_pred.min())
        plt.plot([min_val, max_val], [min_val, max_val], color="#f0883e", linestyle="--", linewidth=2, label="Perfect Forecast")
        
        plt.xlabel("Actual CLTV (£)")
        plt.ylabel("Predicted CLTV (£)")
        plt.title(f"Prediction Error Plot (Actual vs Predicted) - {model_name}")
        plt.legend()
        plt.grid(True, linestyle=":", alpha=0.6)
        
        plt.tight_layout()
        plt.savefig(save_path, dpi=150, facecolor="#0d1117")
        plt.close()
        logger.info(f"Saved prediction error plot for {model_name} to {save_path}")

    def explain_with_shap(self, model: Any, X_train: Union[pd.DataFrame, np.ndarray], X_test: Union[pd.DataFrame, np.ndarray], save_dir: Path) -> None:
        """
        Generates and saves SHAP summary and bar plots.
        """
        save_dir = Path(save_dir)
        save_dir.mkdir(parents=True, exist_ok=True)
        
        # Check model type to choose SHAP explainer
        model_type = type(model).__name__
        logger.info(f"Generating SHAP explanations for {model_type}...")
        
        try:
            # Tree based explainers for XGBoost, LightGBM, RandomForest
            if any(name in model_type for name in ["XGB", "LGBM", "RandomForest", "Forest", "Boosting"]):
                explainer = shap.TreeExplainer(model)
            else:
                # Kernel / Linear fallback
                explainer = shap.Explainer(model, X_train)
                
            shap_values = explainer(X_test)
            
            # 1. SHAP Summary Plot
            plt.figure(figsize=(12, 8))
            shap.summary_plot(shap_values, X_test, feature_names=self.feature_names, show=False)
            plt.title(f"SHAP Feature Impact Summary - {model_type}", fontsize=14, color="#c9d1d9")
            plt.gcf().patch.set_facecolor("#0d1117")
            plt.tight_layout()
            plt.savefig(save_dir / "shap_summary.png", dpi=150, facecolor="#0d1117")
            plt.close()
            
            # 2. SHAP Bar Plot (Global Importance)
            plt.figure(figsize=(12, 8))
            shap.plots.bar(shap_values, show=False)
            plt.title(f"SHAP Global Feature Importance - {model_type}", fontsize=14, color="#c9d1d9")
            plt.gcf().patch.set_facecolor("#0d1117")
            plt.tight_layout()
            plt.savefig(save_dir / "shap_bar.png", dpi=150, facecolor="#0d1117")
            plt.close()
            
            logger.info(f"Successfully generated SHAP summary and bar plots in {save_dir}")
        except Exception as e:
            logger.error(f"Failed to generate SHAP plots: {e}")
