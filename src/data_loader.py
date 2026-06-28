"""
Data Loader Module for CLTV Prediction System.
Handles data loading, schema validation, and summary reporting.
"""

import logging
from pathlib import Path
from typing import Dict, Any, Union
import pandas as pd

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("DataLoader")

class DataLoader:
    """
    Handles ingestion of transactional retail data from CSV or Excel formats,
    validates the schema, provides diagnostics summaries, and handles saving/loading
    processed files.
    """

    def __init__(self, raw_dir: Union[str, Path]):
        """
        Initializes DataLoader with path to raw data folder.
        
        Args:
            raw_dir: Path to directory containing raw data files.
        """
        self.raw_dir = Path(raw_dir)

    def load_online_retail_data(self, filename: str) -> pd.DataFrame:
        """
        Loads the online retail dataset. If filename ends with .xlsx, tries to read
        and combine 'Year 2009-2010' and 'Year 2010-2011' sheets.
        
        Args:
            filename: Name of file in raw_dir to load.
            
        Returns:
            pd.DataFrame: Combined transactions dataset.
            
        Raises:
            FileNotFoundError: If the file is not found.
            ValueError: If file type is unsupported.
        """
        filepath = self.raw_dir / filename
        if not filepath.exists():
            logger.error(f"Data file not found at {filepath}")
            raise FileNotFoundError(f"Data file not found at {filepath}")

        logger.info(f"Loading dataset from {filepath}...")
        
        if filepath.suffix == '.xlsx':
            # UCI Online Retail II has sheets for two periods
            try:
                logger.info("Reading Sheet 'Year 2009-2010'...")
                df1 = pd.read_excel(filepath, sheet_name='Year 2009-2010', dtype={'Customer ID': str})
                logger.info("Reading Sheet 'Year 2010-2011'...")
                df2 = pd.read_excel(filepath, sheet_name='Year 2010-2011', dtype={'Customer ID': str})
                df = pd.concat([df1, df2], ignore_index=True)
                logger.info(f"Successfully combined sheets. Total records: {len(df):,}")
            except Exception as e:
                logger.warning(f"Failed to read sheets separately: {e}. Reading first sheet instead.")
                df = pd.read_excel(filepath, dtype={'Customer ID': str})
        elif filepath.suffix == '.csv':
            try:
                df = pd.read_csv(filepath, encoding='unicode_escape', dtype={'Customer ID': str})
            except UnicodeDecodeError:
                df = pd.read_csv(filepath, encoding='latin1', dtype={'Customer ID': str})
            logger.info(f"Successfully loaded CSV. Total records: {len(df):,}")
        else:
            raise ValueError(f"Unsupported file format: {filepath.suffix}. Must be .xlsx or .csv")

        return df

    def validate_schema(self, df: pd.DataFrame) -> bool:
        """
        Validates that the loaded DataFrame contains all required columns.
        
        Args:
            df: Loaded DataFrame.
            
        Returns:
            bool: True if schema is valid, False otherwise.
        """
        required_cols = [
            "Invoice", "StockCode", "Description", 
            "Quantity", "InvoiceDate", "Price", 
            "Customer ID", "Country"
        ]
        missing_cols = [col for col in required_cols if col not in df.columns]
        
        # Check standard variation without spaces (like CustomerID)
        if "CustomerID" in df.columns and "Customer ID" in missing_cols:
            df.rename(columns={"CustomerID": "Customer ID"}, inplace=True)
            missing_cols.remove("Customer ID")

        if missing_cols:
            logger.error(f"Schema validation failed. Missing columns: {missing_cols}")
            return False
            
        logger.info("Schema validation successful. All required columns are present.")
        return True

    def get_data_summary(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Generates a summary dictionary of the dataset's basic statistics.
        
        Args:
            df: DataFrame to summarize.
            
        Returns:
            Dict: Summary statistics.
        """
        summary = {
            "total_rows": len(df),
            "total_columns": len(df.columns),
            "memory_usage_mb": round(df.memory_usage(deep=True).sum() / 1024**2, 2),
            "columns_info": {},
            "duplicate_rows": int(df.duplicated().sum())
        }

        for col in df.columns:
            null_count = int(df[col].isnull().sum())
            summary["columns_info"][col] = {
                "dtype": str(df[col].dtype),
                "unique_values": int(df[col].nunique()),
                "null_count": null_count,
                "null_percentage": round((null_count / len(df)) * 100, 2)
            }
            
        return summary

    def save_processed(self, df: pd.DataFrame, filepath: Union[str, Path]) -> None:
        """
        Saves a processed DataFrame to the specified CSV filepath.
        
        Args:
            df: DataFrame to save.
            filepath: Destination path.
        """
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(filepath, index=False)
        logger.info(f"Successfully saved processed data to {filepath}")

    def load_processed(self, filepath: Union[str, Path]) -> pd.DataFrame:
        """
        Loads a processed CSV file.
        
        Args:
            filepath: Path to processed file.
            
        Returns:
            pd.DataFrame: Loaded processed DataFrame.
        """
        filepath = Path(filepath)
        logger.info(f"Loading processed data from {filepath}...")
        df = pd.read_csv(filepath, dtype={'Customer ID': str})
        return df
