"""
Streamlit Web Application for CLTV Prediction System.
Provides interactive customer value lookup, batch predictions, and marketing guidelines.
"""

import sys
import json
from pathlib import Path
import streamlit as st
import pandas as pd
import numpy as np
import joblib
import plotly.express as px
import plotly.graph_objects as go

# Configure page settings
st.set_page_config(
    page_title="CLTV Prediction Portal",
    page_icon="🏆",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom styles for dark theme matching GitHub/Antigravity aesthetics
st.markdown("""
<style>
    .main { background-color: #0d1117; color: #c9d1d9; }
    .stSidebar { background-color: #161b22; border-right: 1px solid #30363d; }
    h1, h2, h3 { color: #58a6ff; font-family: 'Segoe UI', sans-serif; }
    .stButton>button { background-color: #238636; color: white; border-radius: 6px; border: 1px solid #3fb950; }
    .stButton>button:hover { background-color: #2ea043; border-color: #56d364; }
    .metric-card {
        background-color: #161b22;
        border: 1px solid #30363d;
        border-radius: 8px;
        padding: 15px;
        margin-bottom: 15px;
        text-align: center;
    }
    .metric-value { font-size: 24px; font-weight: bold; color: #3fb950; }
    .metric-label { font-size: 14px; color: #8b949e; }
</style>
""", unsafe_allow_html=True)

# Define paths
APP_DIR = Path(__file__).parent if "__file__" in locals() else Path.cwd()
PROJECT_ROOT = APP_DIR.parent
MODELS_DIR = PROJECT_ROOT / "models" / "saved_models"
DATA_FEATURES = PROJECT_ROOT / "data" / "features"

@st.cache_resource
def load_best_model():
    """Reads registry and loads the best model serialized on disk."""
    registry_path = PROJECT_ROOT / "models" / "model_registry.json"
    if not registry_path.exists():
        return None, "Model registry file missing."
        
    with open(registry_path, "r") as f:
        registry = json.load(f)
        
    best_name = registry.get("best_model")
    if not best_name:
        return None, "No best model identified in registry."
        
    model_path = MODELS_DIR / f"{best_name}.joblib"
    if not model_path.exists():
        return None, f"Model file {best_name}.joblib missing."
        
    model = joblib.load(model_path)
    return model, best_name

@st.cache_data
def load_feature_data():
    """Loads engineered customer features from disk."""
    feat_path = DATA_FEATURES / "customer_features.csv"
    if feat_path.exists():
        return pd.read_csv(feat_path)
    return pd.DataFrame()

# Load assets
model, model_info = load_best_model()
features_df = load_feature_data()

# ─── Sidebar Navigation ──────────────────────────────────────────────────────
st.sidebar.image("https://img.icons8.com/color/96/000000/dashboard.png", width=80)
st.sidebar.title("CLTV Predictor VIP")
st.sidebar.markdown("*Fortune 500 E-Commerce*")
st.sidebar.markdown("---")

app_mode = st.sidebar.selectbox(
    "Choose Interface",
    ["Executive KPI Dashboard", "Single Customer Lookup", "Batch Upload Prediction"]
)

st.sidebar.markdown("---")
st.sidebar.markdown(f"**Best Model**: `{model_info}`")
st.sidebar.info("Model outputs forecast customer spending in the next 90-day horizon.")

# ==============================================================================
# View 1: Executive KPI Dashboard
# ==============================================================================
if app_mode == "Executive KPI Dashboard":
    st.title("🏆 Executive Customer Value Dashboard")
    st.markdown("Overview of customer equity assets, cohort sizes, and average lifetime value projections.")
    
    if features_df.empty:
        st.warning("No customer feature dataset found. Please run the model training pipeline first.")
    else:
        # Compute summary metrics
        total_customers = len(features_df)
        avg_recency = features_df["Recency"].mean()
        avg_frequency = features_df["Frequency"].mean()
        avg_monetary = features_df["Monetary"].mean()
        
        # Display cards
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{total_customers:,}</div>
                <div class="metric-label">Active Customer Equity Base</div>
            </div>
            """, unsafe_allow_html=True)
            
        with col2:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">£{avg_monetary:,.2f}</div>
                <div class="metric-label">Avg Historical Customer Value</div>
            </div>
            """, unsafe_allow_html=True)
            
        with col3:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{avg_frequency:.1f}</div>
                <div class="metric-label">Avg Order Frequency (Orders)</div>
            </div>
            """, unsafe_allow_html=True)
            
        with col4:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{avg_recency:.1f} days</div>
                <div class="metric-label">Avg Recency Index (Days)</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("### 📈 Customer Segment Analysis")
        # Visualizing segment counts using Plotly
        fig = px.scatter(
            features_df,
            x="Frequency",
            y="Monetary",
            color="Recency",
            size="Monetary",
            log_x=True,
            log_y=True,
            title="Customer Portfolio distribution (Frequency vs Spend)",
            color_continuous_scale="Viridis",
            labels={"Monetary": "Monetary Value (£)", "Frequency": "Order Frequency (Log)"}
        )
        fig.update_layout(template="plotly_dark", paper_bgcolor='#0d1117', plot_bgcolor='#161b22')
        st.plotly_chart(fig, use_container_width=True)

# ==============================================================================
# View 2: Single Customer Lookup
# ==============================================================================
elif app_mode == "Single Customer Lookup":
    st.title("🔍 Single Customer Value Predictor")
    st.markdown("Search existing Customer IDs or simulate a new customer transaction record to fetch LTV forecasts.")
    
    if model is None:
        st.error(f"Error loading model: {model_info}")
    else:
        # Search panel
        st.markdown("### Search Customer Registry")
        
        search_id = st.text_input("Enter Customer ID (e.g. 12345 or select from drop-down)", "")
        
        # Prefill values if customer exists
        default_vals = {
            "Recency": 30, "Frequency": 3, "Monetary": 150.0, "Tenure": 365,
            "Product_Diversity": 5, "Avg_Basket_Size": 6.0, "Avg_Order_Value": 50.0,
            "Avg_Monthly_Spend": 45.0, "Seasonal_Score_Q4": 0.25,
            "Avg_Purchase_Interval": 30.0, "Revenue_Growth": 0.0, "Is_UK": 1
        }
        
        found = False
        if search_id and not features_df.empty:
            cust_record = features_df[features_df["CustomerID"].astype(str) == str(search_id)]
            if not cust_record.empty:
                st.success(f"Customer {search_id} found in database!")
                row = cust_record.iloc[0]
                for k in default_vals.keys():
                    if k in row:
                        default_vals[k] = row[k]
                found = True
            else:
                st.warning("Customer ID not found. Displaying default simulation values.")
        
        st.markdown("### Transactional Metrics Panel")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            recency = st.slider("Recency (Days since last purchase)", 0, 730, int(default_vals["Recency"]))
            frequency = st.slider("Frequency (Unique Invoice count)", 1, 200, int(default_vals["Frequency"]))
            monetary = st.number_input("Monetary (£ Net historical spend)", 0.0, 100000.0, float(default_vals["Monetary"]))
            
        with col2:
            tenure = st.slider("Tenure (Customer Relationship Days)", 1, 730, int(default_vals["Tenure"]))
            prod_div = st.slider("Product Diversity (Unique items bought)", 1, 100, int(default_vals["Product_Diversity"]))
            avg_basket = st.slider("Average Basket Size (Units per order)", 1.0, 50.0, float(default_vals["Avg_Basket_Size"]))
            
        with col3:
            avg_o_val = st.number_input("Average Order Value (AOV £)", 0.0, 10000.0, float(default_vals["Avg_Order_Value"]))
            avg_m_spend = st.number_input("Average Monthly Spend (£)", 0.0, 10000.0, float(default_vals["Avg_Monthly_Spend"]))
            rev_growth = st.slider("Revenue Growth rate index", -1.0, 5.0, float(default_vals["Revenue_Growth"]))
            
        # Hidden or binary parameters
        is_uk = st.selectbox("Location", ["United Kingdom (Domestic)", "International"], index=0 if default_vals["Is_UK"] == 1 else 1)
        is_uk_val = 1 if is_uk == "United Kingdom (Domestic)" else 0
        
        # Build features array matching training layout
        # ['Recency', 'Frequency', 'Monetary', 'Tenure', 'Product_Diversity', 'Avg_Basket_Size', 'Avg_Order_Value', 'Avg_Monthly_Spend', 'Seasonal_Score_Q4', 'Avg_Purchase_Interval', 'Revenue_Growth', 'Is_UK']
        feats = np.array([[
            recency, frequency, monetary, tenure, prod_div, avg_basket, 
            avg_o_val, avg_m_spend, default_vals["Seasonal_Score_Q4"],
            default_vals["Avg_Purchase_Interval"], rev_growth, is_uk_val
        ]])
        
        if st.button("Predict 90-Day Future Spend (CLTV)"):
            pred = model.predict(feats)[0]
            pred = max(0, pred) # Ensure positive
            
            st.markdown("---")
            st.markdown("## Prediction Results")
            st.metric(label="Predicted Next-90-Day Revenue Contribution", value=f"£{pred:,.2f}")
            
            # Actionable advice based on values
            if pred > 500:
                st.balloons()
                st.success("🎯 **VIP Customer Segment:** High value buyer. Eligible for VIP reward codes and dedicated customer support outreach.")
            elif pred > 100:
                st.info("👍 **Medium Value Segment:** Regular shopper. Target with category-specific cross-selling emails.")
            else:
                st.warning("⚠️ **Low Value Segment:** Nudge with entry discount codes or free delivery threshold reminders.")

# ==============================================================================
# View 3: Batch Upload Prediction
# ==============================================================================
elif app_mode == "Batch Upload Prediction":
    st.title("📂 Batch CLTV Prediction Portal")
    st.markdown("Upload a CSV file containing customer transaction records to predict CLTV in bulk and download campaign files.")
    
    uploaded_file = st.file_uploader("Upload CSV file (Must contain columns: Recency, Frequency, Monetary, Tenure, Product_Diversity, Avg_Basket_Size, Avg_Order_Value, Avg_Monthly_Spend, Seasonal_Score_Q4, Avg_Purchase_Interval, Revenue_Growth, Is_UK)", type="csv")
    
    if uploaded_file is not None:
        try:
            input_df = pd.read_csv(uploaded_file)
            st.success("CSV file successfully loaded!")
            
            # Predict
            # Drop identifier columns like CustomerID for model feeding
            drop_cols = ["CustomerID", "Customer ID"]
            model_cols = [c for c in input_df.columns if c not in drop_cols]
            
            preds = model.predict(input_df[model_cols])
            input_df["predicted_cltv_90_days"] = np.clip(preds, 0, None)
            
            st.markdown("### Prediction Head Sample")
            st.dataframe(input_df.head(10))
            
            # CSV Download button
            csv = input_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="Download Predictions Report CSV",
                data=csv,
                file_name="cltv_batch_predictions.csv",
                mime="text/csv"
            )
        except Exception as e:
            st.error(f"Failed to parse CSV or run predictions: {e}")
