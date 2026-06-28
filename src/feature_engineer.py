"""
Feature Engineering Module for CLTV Prediction System.
Extracts customer behavioral features for predictive modeling and segmentation.
"""

import logging
from typing import Tuple, Optional, Any, Union
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler, MinMaxScaler

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("FeatureEngineer")

class FeatureEngineer:
    """
    Transforms transactional retail data into customer-level features.
    Provides methods for time-based splitting to prevent data leakage.
    """

    def __init__(self, df: pd.DataFrame):
        """
        Initializes FeatureEngineer.
        
        Args:
            df: Cleaned retail transactions DataFrame.
        """
        self.df = df.copy()
        self.df['InvoiceDate'] = pd.to_datetime(self.df['InvoiceDate'])

    def split_data_on_date(self, split_date: Union[str, pd.Timestamp], prediction_days: int = 90) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Splits transactions into an observation window and a prediction window.
        
        Args:
            split_date: Date to split the transactions.
            prediction_days: Number of days in the prediction window.
            
        Returns:
            Tuple of DataFrames: (df_observation, df_prediction)
        """
        split_dt = pd.to_datetime(split_date) if isinstance(split_date, str) else split_date
        end_prediction_dt = split_dt + pd.Timedelta(days=prediction_days)
        
        logger.info(f"Splitting data. Split Date (Observation End): {split_dt.date()} | Prediction End: {end_prediction_dt.date()}")
        
        df_obs = self.df[self.df["InvoiceDate"] < split_dt]
        df_pred = self.df[(self.df["InvoiceDate"] >= split_dt) & (self.df["InvoiceDate"] < end_prediction_dt)]
        
        logger.info(f"Observation records: {len(df_obs):,} | Prediction records: {len(df_pred):,}")
        return df_obs, df_pred

    def calculate_rfm_base(self, df_obs: pd.DataFrame, ref_date: pd.Timestamp) -> pd.DataFrame:
        """
        Calculates basic Recency, Frequency, and Monetary metrics.
        
        Args:
            df_obs: DataFrame containing observation window transactions.
            ref_date: Reference date for Recency calculation (usually observation end date).
            
        Returns:
            pd.DataFrame: Customer-level RFM metrics.
        """
        logger.info("Calculating base RFM metrics...")
        
        # Group by customer
        rfm = df_obs.groupby("Customer ID").agg(
            last_purchase=("InvoiceDate", "max"),
            first_purchase=("InvoiceDate", "min"),
            Frequency=("Invoice", "nunique"),
            Monetary=("Revenue", "sum")
        ).reset_index()
        
        # Recency: days between last purchase and reference date
        rfm["Recency"] = (ref_date - rfm["last_purchase"]).dt.days
        # Customer Tenure: days since first purchase
        rfm["Tenure"] = (ref_date - rfm["first_purchase"]).dt.days
        
        return rfm.drop(columns=["last_purchase", "first_purchase"])

    def calculate_behavioral_features(self, df_obs: pd.DataFrame) -> pd.DataFrame:
        """
        Computes advanced behavioral features from observation window.
        
        Args:
            df_obs: DataFrame containing observation window transactions.
            
        Returns:
            pd.DataFrame: Customer-level behavioral features.
        """
        logger.info("Calculating behavioral customer features...")
        
        # 1. Product diversity (unique stock codes bought)
        prod_diversity = df_obs.groupby("Customer ID")["StockCode"].nunique().reset_index(name="Product_Diversity")
        
        # 2. Average basket size (units per invoice) and Average line price
        basket = df_obs.groupby(["Customer ID", "Invoice"]).agg(
            items_count=("Quantity", "sum"),
            invoice_revenue=("Revenue", "sum")
        ).reset_index()
        
        avg_basket = basket.groupby("Customer ID").agg(
            Avg_Basket_Size=("items_count", "mean"),
            Avg_Order_Value=("invoice_revenue", "mean")
        ).reset_index()
        
        # 3. Monthly spending patterns (Average monthly spend)
        df_obs_copy = df_obs.copy()
        df_obs_copy["YearMonth"] = df_obs_copy["InvoiceDate"].dt.to_period("M")
        monthly_spend = df_obs_copy.groupby(["Customer ID", "YearMonth"])["Revenue"].sum().reset_index()
        avg_monthly_spend = monthly_spend.groupby("Customer ID")["Revenue"].mean().reset_index(name="Avg_Monthly_Spend")
        
        # 4. Seasonal buying score (proportion of purchases in Q4 - peak retail season)
        df_obs_copy["Quarter"] = df_obs_copy["InvoiceDate"].dt.quarter
        q4_spend = df_obs_copy[df_obs_copy["Quarter"] == 4].groupby("Customer ID")["Revenue"].sum().reset_index(name="q4_rev")
        total_spend = df_obs_copy.groupby("Customer ID")["Revenue"].sum().reset_index(name="total_rev")
        
        seasonality = pd.merge(total_spend, q4_spend, on="Customer ID", how="left").fillna(0)
        seasonality["Seasonal_Score_Q4"] = seasonality["q4_rev"] / seasonality["total_rev"]
        seasonality = seasonality[["Customer ID", "Seasonal_Score_Q4"]]
        
        # 5. Purchase intervals (average days between purchases)
        cust_invoices = df_obs.groupby(["Customer ID", "Invoice"])["InvoiceDate"].min().reset_index()
        cust_invoices = cust_invoices.sort_values(["Customer ID", "InvoiceDate"])
        cust_invoices["prev_date"] = cust_invoices.groupby("Customer ID")["InvoiceDate"].shift(1)
        cust_invoices["days_between"] = (cust_invoices["InvoiceDate"] - cust_invoices["prev_date"]).dt.days
        
        intervals = cust_invoices.groupby("Customer ID")["days_between"].mean().reset_index(name="Avg_Purchase_Interval")
        intervals["Avg_Purchase_Interval"] = intervals["Avg_Purchase_Interval"].fillna(999.0) # Fill for single-purchase customers
        
        # 6. Revenue growth trend (First half vs Second half of tenure spending)
        cust_dates = df_obs.groupby("Customer ID").agg(
            min_d=("InvoiceDate", "min"),
            max_d=("InvoiceDate", "max")
        ).reset_index()
        cust_dates["midpoint"] = cust_dates["min_d"] + (cust_dates["max_d"] - cust_dates["min_d"]) / 2
        
        df_trends = pd.merge(df_obs, cust_dates, on="Customer ID", how="left")
        rev_first_half = df_trends[df_trends["InvoiceDate"] <= df_trends["midpoint"]].groupby("Customer ID")["Revenue"].sum().reset_index(name="rev_fh")
        rev_second_half = df_trends[df_trends["InvoiceDate"] > df_trends["midpoint"]].groupby("Customer ID")["Revenue"].sum().reset_index(name="rev_sh")
        
        trends = pd.merge(rev_first_half, rev_second_half, on="Customer ID", how="outer").fillna(0)
        trends["Revenue_Growth"] = (trends["rev_sh"] - trends["rev_fh"]) / (trends["rev_fh"] + 1e-5)
        trends = trends[["Customer ID", "Revenue_Growth"]]
        
        # 7. Customer Country (One-hot encoding candidate)
        countries = df_obs.groupby("Customer ID")["Country"].first().reset_index()
        countries["Is_UK"] = (countries["Country"] == "United Kingdom").astype(int)
        countries = countries[["Customer ID", "Is_UK"]]

        # Combine all features
        features = prod_diversity
        for right_df in [avg_basket, avg_monthly_spend, seasonality, intervals, trends, countries]:
            features = pd.merge(features, right_df, on="Customer ID", how="left")
            
        return features

    def build_master_feature_table(self, split_date: Union[str, pd.Timestamp], prediction_days: int = 90) -> pd.DataFrame:
        """
        Creates observation features and prediction target.
        Target is total customer revenue in the prediction window (CLTV target).
        
        Args:
            split_date: Split date.
            prediction_days: Prediction horizon in days.
            
        Returns:
            Tuple of DataFrames: (X, y) merged as a master table and X_raw.
        """
        df_obs, df_pred = self.split_data_on_date(split_date, prediction_days)
        split_dt = pd.Timestamp(split_date)
        
        # 1. Base RFM features on observation window
        rfm_base = self.calculate_rfm_base(df_obs, split_dt)
        
        # 2. Behavioral features on observation window
        behavioral = self.calculate_behavioral_features(df_obs)
        
        # Combine X features
        X_features = pd.merge(rfm_base, behavioral, on="Customer ID", how="left").fillna(0)
        
        # 3. Create target on prediction window (monetary value in prediction window)
        target = df_pred.groupby("Customer ID")["Revenue"].sum().reset_index(name="target_revenue")
        
        # Merge features and target
        master_table = pd.merge(X_features, target, on="Customer ID", how="left").fillna(0)
        
        logger.info(f"Master feature table shape: {master_table.shape}")
        logger.info(f"Active customers in prediction window: {master_table['target_revenue'].gt(0).sum():,} ({master_table['target_revenue'].gt(0).mean()*100:.2f}%)")
        
        return master_table

    def normalize_features(self, df: pd.DataFrame, columns_to_scale: list, method: str = "standard") -> Tuple[pd.DataFrame, Any]:
        """
        Applies scaling to numerical columns.
        
        Args:
            df: Feature DataFrame.
            columns_to_scale: List of column names to scale.
            method: 'standard' for StandardScaler, 'minmax' for MinMaxScaler.
            
        Returns:
            Tuple of (scaled_df, scaler_object)
        """
        df_scaled = df.copy()
        if method == "standard":
            scaler = StandardScaler()
        elif method == "minmax":
            scaler = MinMaxScaler()
        else:
            raise ValueError(f"Unknown scaling method: {method}")
            
        df_scaled[columns_to_scale] = scaler.fit_transform(df_scaled[columns_to_scale])
        logger.info(f"Scaled {len(columns_to_scale)} features using {method} scaling.")
        return df_scaled, scaler
