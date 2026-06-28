"""
Data Cleaning Module for CLTV Prediction System.
Implements industrial-grade data cleaning pipelines for retail transactional data.
"""

import logging
from typing import Dict, Any, List, Tuple
import pandas as pd
import numpy as np

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("DataCleaner")

class DataCleaner:
    """
    Cleans raw retail transaction datasets using strict business rules
    and keeps a detailed audit log of rows removed at each stage.
    """

    def __init__(self, df: pd.DataFrame):
        """
        Initializes DataCleaner with a copy of the input DataFrame.
        
        Args:
            df: Raw DataFrame to clean.
        """
        self.df = df.copy()
        self.original_shape = df.shape
        self.cleaning_log: List[Dict[str, Any]] = []

    def _log_step(self, step_name: str, df_before: pd.DataFrame, df_after: pd.DataFrame) -> None:
        """
        Logs the results of a data cleaning step.
        """
        rows_before = len(df_before)
        rows_after = len(df_after)
        rows_removed = rows_before - rows_after
        pct_removed = round((rows_removed / rows_before) * 100, 4) if rows_before > 0 else 0.0
        
        self.cleaning_log.append({
            "step_name": step_name,
            "rows_before": rows_before,
            "rows_after": rows_after,
            "rows_removed": rows_removed,
            "pct_removed": pct_removed
        })
        logger.info(f"[{step_name}] Rows before: {rows_before:,} | Rows after: {rows_after:,} | Removed: {rows_removed:,} ({pct_removed}%)")

    def remove_missing_customer_ids(self) -> "DataCleaner":
        """
        Drops records that lack a Customer ID.
        Justification: Unregistered/guest purchases cannot be modeled for CLTV.
        """
        df_before = self.df.copy()
        self.df = self.df.dropna(subset=["Customer ID"])
        self._log_step("Remove Missing Customer ID", df_before, self.df)
        return self

    def remove_cancelled_transactions(self) -> "DataCleaner":
        """
        Drops cancellations (invoices starting with 'C').
        Justification: Invoices starting with C represent refunds. These should be tracked
        separately but removed from main modeling flow to prevent revenue inflation.
        """
        df_before = self.df.copy()
        # Invoices can be floats/ints in some sheets, ensure cast to string
        self.df["Invoice"] = self.df["Invoice"].astype(str).str.strip()
        self.df = self.df[~self.df["Invoice"].str.startswith("C", na=False)]
        self._log_step("Remove Cancelled Transactions", df_before, self.df)
        return self

    def remove_negative_quantities(self) -> "DataCleaner":
        """
        Drops records with negative or zero quantities.
        Justification: Non-positive quantities are anomalous and likely errors or returns.
        """
        df_before = self.df.copy()
        self.df = self.df[self.df["Quantity"] > 0]
        self._log_step("Remove Non-Positive Quantities", df_before, self.df)
        return self

    def remove_negative_prices(self) -> "DataCleaner":
        """
        Drops records with negative or zero unit prices.
        Justification: Free items or adjustments (negative prices) pollute spend metrics.
        """
        df_before = self.df.copy()
        self.df = self.df[self.df["Price"] > 0]
        self._log_step("Remove Non-Positive Prices", df_before, self.df)
        return self

    def fix_data_types(self) -> "DataCleaner":
        """
        Ensures proper types: Datetime for InvoiceDate, string for Customer ID, float for Price, int for Quantity.
        """
        self.df["InvoiceDate"] = pd.to_datetime(self.df["InvoiceDate"])
        self.df["Customer ID"] = self.df["Customer ID"].astype(str).str.split('.').str[0].str.strip()
        self.df["Quantity"] = self.df["Quantity"].astype(int)
        self.df["Price"] = self.df["Price"].astype(float)
        logger.info("Fixed data types: InvoiceDate->datetime, Customer ID->string, Quantity->int, Price->float")
        return self

    def remove_duplicates(self) -> "DataCleaner":
        """
        Drops duplicate transaction lines.
        Justification: Duplicates inflate transaction frequency and monetary volume.
        """
        df_before = self.df.copy()
        self.df = self.df.drop_duplicates()
        self._log_step("Remove Duplicates", df_before, self.df)
        return self

    def remove_test_customers(self) -> "DataCleaner":
        """
        Drops Customer IDs representing testing entries or internal corporate accounts.
        Justification: Accounts like "AMAZONFBA" or IDs that contain alphabetical letters
        usually represent operational anomalies.
        """
        df_before = self.df.copy()
        
        # Keep only numeric customer IDs (5-digit integers)
        # Check if ID consists only of digits
        self.df = self.df[self.df["Customer ID"].str.match(r"^\d+$", na=False)]
        
        # Also drop known test stockcodes
        test_codes = ["POST", "D", "DOT", "M", "BANK CHARGES", "TEST", "PADS", "ADJUST", "CRUK"]
        self.df = self.df[~self.df["StockCode"].astype(str).str.upper().isin(test_codes)]
        
        self._log_step("Remove Test Accounts & Codes", df_before, self.df)
        return self

    def cap_outliers(self, lower_pct: float = 0.01, upper_pct: float = 0.99) -> "DataCleaner":
        """
        Winsorizes Quantity and Price columns to remove extreme outlier distortions.
        Justification: Extreme transaction counts or prices skew modeling and metrics.
        """
        for col in ["Quantity", "Price"]:
            lower_bound = self.df[col].quantile(lower_pct)
            upper_bound = self.df[col].quantile(upper_pct)
            
            logger.info(f"Capping {col}: values below {lower_bound} and above {upper_bound} will be capped.")
            self.df[col] = np.clip(self.df[col], lower_bound, upper_bound)
            
        return self

    def add_revenue_column(self) -> "DataCleaner":
        """
        Calculates transaction line revenue (Quantity * Price).
        """
        self.df["Revenue"] = self.df["Quantity"] * self.df["Price"]
        logger.info("Added 'Revenue' column (Quantity * Price)")
        return self

    def clean_description(self) -> "DataCleaner":
        """
        Cleans the description text for consistency.
        """
        if "Description" in self.df.columns:
            self.df["Description"] = self.df["Description"].astype(str).str.strip().str.upper()
            logger.info("Normalized 'Description' column to uppercase and stripped spaces.")
        return self

    def get_cleaning_report(self) -> pd.DataFrame:
        """
        Returns a DataFrame summarizing all cleaning steps taken.
        """
        report_df = pd.DataFrame(self.cleaning_log)
        if not report_df.empty:
            report_df["total_removed"] = self.original_shape[0] - report_df["rows_after"]
            report_df["total_removed_pct"] = round((report_df["total_removed"] / self.original_shape[0]) * 100, 2)
        return report_df

    def run_full_pipeline(self) -> pd.DataFrame:
        """
        Runs the full cleaning pipeline in the recommended order.
        """
        logger.info("Starting raw data cleaning pipeline...")
        (
            self.remove_missing_customer_ids()
                .remove_cancelled_transactions()
                .remove_negative_quantities()
                .remove_negative_prices()
                .fix_data_types()
                .remove_duplicates()
                .remove_test_customers()
                .cap_outliers()
                .clean_description()
                .add_revenue_column()
        )
        logger.info(f"Data cleaning pipeline complete. Cleaned data contains {len(self.df):,} rows.")
        return self.df
