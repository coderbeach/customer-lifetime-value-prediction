# 🛠️ Technical Model Report — E-Commerce CLTV Prediction System

This document outlines the machine learning architecture, validation strategies, feature importance rankings, and explainability findings of the CLTV Prediction project.

---

## 1. Machine Learning Goal & Target Definition

The goal is to solve a **supervised regression task**: predict the monetary spend (revenue) of each active customer in the next **90-day horizon** based on their behavioral history.

* **Target Variable:** `target_revenue` - Total spend (£) by a customer in the 90 days following September 1, 2011.
* **Feature Scope:** Transaction logs from December 1, 2009, to August 31, 2011 (Observation window).

### 🛡️ Preventing Data Leakage
By dividing the transaction timeline into an out-of-time observation block and a holdout prediction window, we guarantee no future parameters bleed into training features. Standard random splits would capture future purchases as features, causing severe model overestimation.

---

## 2. Model Performance Comparison

Six machine learning algorithms were trained with K-Fold cross-validation ($k=5$) and hyperparameter tuning. Performance metrics on the holdout test set are summarized below:

| Model | MAE (£) | RMSE (£) | $R^2$ Score | MAPE (%) |
| :--- | :--- | :--- | :--- | :--- |
| **XGBoost** | **1001.24** | **1344.20** | **0.109** | **62.76** |
| **Random Forest** | 1005.71 | 1353.84 | 0.096 | 63.04 |
| **Gradient Boosting** | 1012.05 | 1357.14 | 0.092 | 64.23 |
| **Decision Tree** | 1023.66 | 1364.40 | 0.082 | 64.15 |
| **Linear Regression** | 1016.64 | 1366.47 | 0.079 | 63.47 |
| **LightGBM** | 1018.29 | 1367.90 | 0.077 | 64.76 |

### 📈 Interpretation of Results
* **XGBoost** outperforms all other models, achieving the highest $R^2$ score (0.109) and lowest prediction error (RMSE 1344.20).
* An $R^2$ score of ~0.11 is typical for e-commerce purchase predictions. Predicting exact purchase values in non-contractual retail settings is highly challenging because customers can stop purchasing at any time without notification.
* The ensemble tree-based models (XGBoost, Random Forest, Gradient Boosting) capture complex interactions between recency and frequency that simple linear regressions miss.

---

## 3. Best Model Details (XGBoost)

* **Hyperparameters (tuned via Random Search):**
  * `objective`: `reg:squarederror`
  * `learning_rate`: 0.05
  * `max_depth`: 5
  * `n_estimators`: 100
  * `subsample`: 0.8
  * `colsample_bytree`: 0.8

---

## 4. SHAP Global Explainability Insights

Using SHAP (SHapley Additive exPlanations) values, we decompose model predictions to see which features drive the forecast.

1. **Monetary Spend (Historical):** This is the strongest driver of predicted future spend. Spenders in the past tend to remain spenders in the future.
2. **Frequency (Orders):** Customers who purchase frequently exhibit higher predicted CLTV. Each additional transaction increases confidence in customer retention.
3. **Recency:** Recency has a negative relationship with predicted CLTV. As days since last purchase increase, the model reduces the customer's predicted future value because of a higher probability of churn.
4. **Tenure:** Long-tenure customers have higher base predicted value. This represents the "loyalty anchor" where customer value compounding is recognized by the model.
