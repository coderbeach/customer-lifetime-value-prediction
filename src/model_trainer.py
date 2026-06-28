"""
Model Training Module for CLTV Prediction System.
Handles data preparation, model selection, hyperparameter tuning, and saving.
"""

import logging
import json
from pathlib import Path
from typing import Tuple, Dict, Any, List, Optional, Union
import pandas as pd
import numpy as np
import joblib

from sklearn.model_selection import train_test_split, RandomizedSearchCV, KFold
from sklearn.linear_model import LinearRegression
from sklearn.tree import DecisionTreeRegressor
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from xgboost import XGBRegressor
from lightgbm import LGBMRegressor

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("ModelTrainer")

class ModelTrainer:
    """
    Manages data splitting, model training, hyperparameter search, and serialization.
    """

    def __init__(self, feature_df: pd.DataFrame, target_col: str = "target_revenue"):
        """
        Initializes ModelTrainer.
        
        Args:
            feature_df: Master feature table containing features and target.
            target_col: Target column name.
        """
        self.df = feature_df.copy()
        self.target_col = target_col
        self.models: Dict[str, Any] = {}

    def prepare_data(self, test_size: float = 0.2, random_state: int = 42) -> Tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series, List[str]]:
        """
        Prepares training and testing datasets. Drops CustomerID and the target.
        
        Args:
            test_size: Proportion of dataset to include in test split.
            random_state: Seed for reproducibility.
            
        Returns:
            Tuple: (X_train, X_test, y_train, y_test, feature_names)
        """
        logger.info("Splitting dataset into train and test sets...")
        
        # Identify columns to drop (identifiers and targets)
        drop_cols = [self.target_col]
        for col in ["Customer ID", "CustomerID", "Country"]:
            if col in self.df.columns:
                drop_cols.append(col)
                
        X = self.df.drop(columns=drop_cols)
        y = self.df[self.target_col]
        
        feature_names = list(X.columns)
        
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=random_state
        )
        
        logger.info(f"Features: {feature_names}")
        logger.info(f"Train set shape: {X_train.shape} | Test set shape: {X_test.shape}")
        
        return X_train, X_test, y_train, y_test, feature_names

    def get_model_configs(self) -> Dict[str, Dict[str, Any]]:
        """
        Returns models and their hyperparameter grids for RandomizedSearchCV.
        """
        return {
            "LinearRegression": {
                "model": LinearRegression(),
                "param_grid": {}
            },
            "DecisionTree": {
                "model": DecisionTreeRegressor(random_state=42),
                "param_grid": {
                    "max_depth": [3, 5, 7, 10, 15],
                    "min_samples_split": [2, 5, 10, 20],
                    "min_samples_leaf": [1, 2, 4, 8]
                }
            },
            "RandomForest": {
                "model": RandomForestRegressor(random_state=42),
                "param_grid": {
                    "n_estimators": [50, 100, 200],
                    "max_depth": [5, 10, 15, None],
                    "min_samples_split": [2, 5, 10],
                    "min_samples_leaf": [1, 2, 4]
                }
            },
            "GradientBoosting": {
                "model": GradientBoostingRegressor(random_state=42),
                "param_grid": {
                    "n_estimators": [50, 100, 200],
                    "learning_rate": [0.01, 0.05, 0.1, 0.2],
                    "max_depth": [3, 4, 5, 6],
                    "subsample": [0.8, 0.9, 1.0]
                }
            },
            "XGBoost": {
                "model": XGBRegressor(random_state=42, objective="reg:squarederror"),
                "param_grid": {
                    "n_estimators": [50, 100, 200],
                    "learning_rate": [0.01, 0.05, 0.1, 0.2],
                    "max_depth": [3, 5, 7],
                    "subsample": [0.8, 1.0],
                    "colsample_bytree": [0.8, 1.0]
                }
            },
            "LightGBM": {
                "model": LGBMRegressor(random_state=42, verbose=-1),
                "param_grid": {
                    "n_estimators": [50, 100, 200],
                    "learning_rate": [0.01, 0.05, 0.1, 0.2],
                    "num_leaves": [15, 31, 63],
                    "subsample": [0.8, 1.0]
                }
            }
        }

    def train_single_model(self, model_name: str, X_train: Union[pd.DataFrame, np.ndarray], y_train: Union[pd.Series, np.ndarray], tune_hyperparams: bool = True) -> Dict[str, Any]:
        """
        Trains a single model, optionally with randomized search hyperparameter tuning.
        """
        logger.info(f"Training {model_name}...")
        configs = self.get_model_configs()
        
        if model_name not in configs:
            raise ValueError(f"Model {model_name} not found in configurations.")
            
        config = configs[model_name]
        model = config["model"]
        param_grid = config["param_grid"]
        
        # If tuning is enabled and hyperparams exist
        if tune_hyperparams and param_grid:
            logger.info(f"Running RandomizedSearchCV for {model_name}...")
            cv = KFold(n_splits=5, shuffle=True, random_state=42)
            search = RandomizedSearchCV(
                estimator=model,
                param_distributions=param_grid,
                n_iter=10,
                cv=cv,
                scoring="neg_root_mean_squared_error",
                random_state=42,
                n_jobs=-1
            )
            search.fit(X_train, y_train)
            best_model = search.best_estimator_
            best_params = search.best_params_
            cv_score = float(-search.best_score_)
            logger.info(f"Best params for {model_name}: {best_params} | Best CV RMSE: {cv_score:.4f}")
        else:
            logger.info(f"Fitting baseline {model_name} (no tuning)...")
            best_model = model.fit(X_train, y_train)
            best_params = {}
            cv_score = 0.0
            
        self.models[model_name] = best_model
        return {
            "model": best_model,
            "best_params": best_params,
            "cv_rmse": cv_score
        }

    def train_all_models(self, X_train: Union[pd.DataFrame, np.ndarray], y_train: Union[pd.Series, np.ndarray], tune_hyperparams: bool = True) -> Dict[str, Dict[str, Any]]:
        """
        Iterates over and trains all configured models.
        """
        results = {}
        for name in self.get_model_configs().keys():
            results[name] = self.train_single_model(name, X_train, y_train, tune_hyperparams)
        return results

    def save_model(self, model: Any, model_name: str, save_dir: Union[str, Path], metrics: Dict[str, float]) -> None:
        """
        Serializes and saves a model to disk, updating the registry.
        """
        save_dir = Path(save_dir)
        save_dir.mkdir(parents=True, exist_ok=True)
        
        model_path = save_dir / f"{model_name}.joblib"
        joblib.dump(model, model_path)
        logger.info(f"Saved {model_name} model to {model_path}")
        
        # Update registry json
        registry_path = save_dir.parent / "model_registry.json"
        
        registry = {"models": [], "best_model": None, "last_updated": None}
        if registry_path.exists():
            try:
                with open(registry_path, "r") as f:
                    registry = json.load(f)
            except Exception:
                pass
                
        # Update details
        model_entry = {
            "name": model_name,
            "path": str(model_path.relative_to(save_dir.parent.parent)),
            "metrics": metrics
        }
        
        # Remove old entry if same name
        registry["models"] = [m for m in registry["models"] if m["name"] != model_name]
        registry["models"].append(model_entry)
        
        # Determine best model based on R2 (highest is best)
        best_r2 = -float("inf")
        best_name = None
        for m in registry["models"]:
            r2 = m["metrics"].get("R2", -999.0)
            if r2 > best_r2:
                best_r2 = r2
                best_name = m["name"]
                
        registry["best_model"] = best_name
        
        # Write back to file
        with open(registry_path, "w") as f:
            json.dump(registry, f, indent=4)
        logger.info("Updated model_registry.json")

    def get_feature_importance(self, model: Any, feature_names: List[str]) -> pd.DataFrame:
        """
        Retrieves feature importance/coefficients from a trained model.
        """
        # Linear Regression has coef_
        if hasattr(model, "coef_"):
            importances = model.coef_
        elif hasattr(model, "feature_importances_"):
            importances = model.feature_importances_
        else:
            logger.warning(f"Model {type(model)} does not support feature importance/coefficients.")
            importances = np.zeros(len(feature_names))
            
        df_imp = pd.DataFrame({
            "Feature": feature_names,
            "Importance": importances
        }).sort_values(by="Importance", ascending=False)
        
        return df_imp
