"""
RFM Analysis and Customer Segmentation Module.
Computes RFM Scores and assigns customer cohorts/segments for target marketing.
"""

import logging
from typing import Tuple, Dict, Any
import pandas as pd
import numpy as np

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("RFMAnalyzer")

class RFMAnalyzer:
    """
    Performs quintile-based RFM (Recency, Frequency, Monetary) analysis
    and maps customers to descriptive marketing segments.
    """

    def __init__(self, df: pd.DataFrame):
        """
        Initializes RFMAnalyzer.
        
        Args:
            df: DataFrame containing Customer ID, Recency, Frequency, Monetary columns.
        """
        self.df = df.copy()
        # Ensure correct naming
        if "Customer ID" in self.df.columns and "CustomerID" not in self.df.columns:
            self.df.rename(columns={"Customer ID": "CustomerID"}, inplace=True)
            
        required_cols = {"CustomerID", "Recency", "Frequency", "Monetary"}
        missing = required_cols - set(self.df.columns)
        if missing:
            raise ValueError(f"Input DataFrame is missing required columns: {missing}")

    def calculate_rfm_scores(self, n_quantiles: int = 5) -> pd.DataFrame:
        """
        Applies quintile splits to assign scores from 1 to 5.
        Recency is inverted (lower days since last purchase -> higher score).
        """
        logger.info("Calculating RFM scores using quintiles...")
        
        # Handle Recency (invert: lower values -> higher score)
        # We rank values to resolve duplicates, then bin
        self.df["R_Score"] = pd.qcut(self.df["Recency"].rank(method="first"), n_quantiles, labels=range(n_quantiles, 0, -1)).astype(int)
        
        # Handle Frequency (higher values -> higher score)
        self.df["F_Score"] = pd.qcut(self.df["Frequency"].rank(method="first"), n_quantiles, labels=range(1, n_quantiles + 1)).astype(int)
        
        # Handle Monetary (higher values -> higher score)
        self.df["M_Score"] = pd.qcut(self.df["Monetary"].rank(method="first"), n_quantiles, labels=range(1, n_quantiles + 1)).astype(int)
        
        # Concatenated RFM Score
        self.df["RFM_Score"] = self.df["R_Score"].astype(str) + self.df["F_Score"].astype(str) + self.df["M_Score"].astype(str)
        
        return self.df

    def assign_segments(self) -> pd.DataFrame:
        """
        Assigns standard marketing segments based on R and F score boundaries.
        """
        logger.info("Assigning customer segments based on RFM scores...")
        
        conditions = [
            (self.df["R_Score"] >= 4) & (self.df["F_Score"] >= 4), # Champions
            (self.df["R_Score"] >= 3) & (self.df["F_Score"] >= 3), # Loyal Customers
            (self.df["R_Score"] >= 3) & (self.df["F_Score"] == 2), # Potential Loyalists
            (self.df["R_Score"] >= 4) & (self.df["F_Score"] == 1), # New Customers
            (self.df["R_Score"] == 2) & (self.df["F_Score"] >= 3), # At Risk
            (self.df["R_Score"] == 1) & (self.df["F_Score"] >= 4), # Can't Lose Them
            (self.df["R_Score"] == 2) & (self.df["F_Score"] == 2), # Need Attention
            (self.df["R_Score"] == 3) & (self.df["F_Score"] == 1), # About to Sleep
            (self.df["R_Score"] == 1) & (self.df["F_Score"] <= 3) & (self.df["F_Score"] > 1), # Hibernating
            (self.df["R_Score"] == 1) & (self.df["F_Score"] == 1)  # Lost
        ]
        
        segments = [
            "Champions",
            "Loyal Customers",
            "Potential Loyalists",
            "New Customers",
            "At Risk",
            "Can't Lose Them",
            "Need Attention",
            "About to Sleep",
            "Hibernating",
            "Lost"
        ]
        
        self.df["Segment"] = np.select(conditions, segments, default="Need Attention")
        return self.df

    def get_segment_summary(self) -> pd.DataFrame:
        """
        Generates a summary stats DataFrame for each customer segment.
        """
        summary = self.df.groupby("Segment").agg(
            Customer_Count=("CustomerID", "count"),
            Avg_Recency=("Recency", "mean"),
            Avg_Frequency=("Frequency", "mean"),
            Avg_Monetary=("Monetary", "mean"),
            Total_Monetary=("Monetary", "sum")
        ).reset_index()
        
        total_customers = summary["Customer_Count"].sum()
        total_revenue = summary["Total_Monetary"].sum()
        
        summary["Customer_Percentage"] = round((summary["Customer_Count"] / total_customers) * 100, 2)
        summary["Revenue_Percentage"] = round((summary["Total_Monetary"] / total_revenue) * 100, 2)
        
        # Sort by total monetary contribution
        summary = summary.sort_values(by="Total_Monetary", ascending=False)
        return summary

    def get_business_strategy(self) -> Dict[str, Dict[str, str]]:
        """
        Returns actionable business strategies for each segment.
        """
        return {
            "Champions": {
                "Description": "Best customers, buy recently and buy often with high spend.",
                "Marketing_Goal": "Upsell premium products, reward loyalty, seek advocacy.",
                "Tactical_Action": "Invite to VIP program, early access to new collections, ask for reviews.",
                "Primary_Channel": "Personalized Email / Dedicated Account Manager"
            },
            "Loyal Customers": {
                "Description": "Buy regularly. Responsive to promotions.",
                "Marketing_Goal": "Maintain engagement, cross-sell related categories.",
                "Tactical_Action": "Loyalty program points acceleration, recommend companion items.",
                "Primary_Channel": "Email / Push Notifications"
            },
            "Potential Loyalists": {
                "Description": "Recent shoppers with moderate frequency and spend.",
                "Marketing_Goal": "Increase purchase frequency.",
                "Tactical_Action": "Offer multi-buy discounts, discount code for next purchase within 30 days.",
                "Primary_Channel": "SMS / Push Notifications"
            },
            "New Customers": {
                "Description": "Bought very recently but only once.",
                "Marketing_Goal": "Onboard and secure the second purchase.",
                "Tactical_Action": "Welcome sequence with discount, usage/styling guides, customer support follow-up.",
                "Primary_Channel": "Email / In-app greetings"
            },
            "At Risk": {
                "Description": "Frequent/big spenders in the past, but haven't purchased in a while.",
                "Marketing_Goal": "Win them back before they churn.",
                "Tactical_Action": "Send renewal/re-activation discount code, ask feedback, 'We miss you' campaign.",
                "Primary_Channel": "Personalized Email / Re-targeting Ads"
            },
            "Can't Lose Them": {
                "Description": "Used to make massive purchases often, but inactive for a long time.",
                "Marketing_Goal": "Emergency reactivation.",
                "Tactical_Action": "High-value direct discount, phone outreach, exclusive renewal offers.",
                "Primary_Channel": "Personalized Email / Direct Call"
            },
            "Need Attention": {
                "Description": "Above-average recency and frequency, but not quite loyal.",
                "Marketing_Goal": "Nudge into loyal status.",
                "Tactical_Action": "Limited-time offers, bundle deals based on browse history.",
                "Primary_Channel": "Email / Web Popups"
            },
            "About to Sleep": {
                "Description": "Below-average recency, frequency and spend. Will lose them if not reactivated.",
                "Marketing_Goal": "Low-cost re-engagement.",
                "Tactical_Action": "Share popular products list, low value coupon.",
                "Primary_Channel": "Email / Push"
            },
            "Hibernating": {
                "Description": "Low frequency, low spend, and inactive for a long time.",
                "Marketing_Goal": "Cost-effective recovery attempt.",
                "Tactical_Action": "Reconstruct value proposition, send massive seasonal clearance campaign.",
                "Primary_Channel": "Email"
            },
            "Lost": {
                "Description": "Lowest R, F, and M scores. Churned.",
                "Marketing_Goal": "Minimal spend. Abandon unless high acquisition cost justifies it.",
                "Tactical_Action": "Standard automated newsletter, survey on why they left.",
                "Primary_Channel": "Email"
            }
        }

    def run_full_analysis(self) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Runs the complete segmentation analysis pipeline.
        """
        self.calculate_rfm_scores()
        self.assign_segments()
        summary = self.get_segment_summary()
        return self.df, summary
