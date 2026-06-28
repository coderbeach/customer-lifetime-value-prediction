# 🎓 Technical & Business Interview Preparation Guide

This document contains 50 interview questions across five core domains, complete with professional, industry-grade responses designed for senior data science and analytics roles.

---

## 🐍 Section 1: Python & Data Engineering (Questions 1 - 10)

### Q1: What is the difference between a shallow copy and a deep copy in pandas?
* **Answer:** A **shallow copy** (e.g. `df.copy(deep=False)`) creates a new DataFrame object but references the original data buffers. Changes to values in the copy will affect the original DataFrame. A **deep copy** (e.g. `df.copy()`, which defaults to `deep=True`) duplicates both the structure and the underlying data. We use deep copies when writing data cleaner modules (`DataCleaner`) to ensure cleaning transformations do not modify the raw input DataFrame in-place.

### Q2: How do you handle datetime conversions in pandas for large datasets efficiently?
* **Answer:** Instead of calling `.apply(pd.to_datetime)` or loops, use `pd.to_datetime(df['column'], format='%Y-%m-%d %H:%M:%S', cache=True)`. Specifying the exact format prevents pandas from invoking its slow parser heuristics, and `cache=True` speeds up parsing of duplicate dates.

### Q3: What is data leakage and how did you prevent it in your feature engineering module?
* **Answer:** Data leakage occurs when information from outside the training dataset is used to train the model. In CLTV, predicting future spend using features calculated over the *entire* transactional timeline is a classic leak. I prevented this by using **out-of-time validation**: I split transactions at September 1, 2011. All features were calculated using data *before* this date (observation window), and the target revenue was calculated using transactions *after* this date (holdout window).

### Q4: Why did you use `joblib` instead of `pickle` for model serialization?
* **Answer:** `joblib` is optimized for serializing Python objects that carry large numpy arrays internally, which is typical for scikit-learn models (especially tree ensembles like Random Forest). It performs faster compression and decompression compared to standard `pickle` by using memory mapping.

### Q5: How do you handle missing values in a categorical feature like `Customer ID` in production?
* **Answer:** In this e-commerce project, records missing a `Customer ID` represent guest checkouts. Because they cannot be linked to a customer identity, they are fundamentally unsuited for a customer-level CLTV model. The business decision was to drop them during cleaning. In production, we log these guest transactions separately for aggregate sales dashboard tracking but filter them from the ML feature engineering pipeline.

### Q6: What is Winsorization and why did you use it?
* **Answer:** Winsorization is the practice of capping extreme outliers at specific percentiles (e.g. 1st and 99th percentiles) rather than deleting the rows. Deleting transactions with large quantities or prices destroys valuable transaction history. Capping them allows us to retain the transactions while preventing extreme values from inflating model weights or skewing distributions.

### Q7: Explain the significance of the `__init__.py` file in your project.
* **Answer:** The `__init__.py` file tells Python that the `src/` directory should be treated as a package. This allows us to import our custom classes (e.g. `from src.data_cleaner import DataCleaner`) in our notebooks and deployment apps.

### Q8: How would you scale the data loading pipeline for 100 million rows?
* **Answer:** For 100M rows, standard memory-based pandas will hit limits. I would:
  1. Use **chunking** (`pd.read_csv(..., chunksize=100000)`) to process records in blocks.
  2. Transition to **Dask** or **Polars** for parallelized processing.
  3. Load the raw transactions into a distributed database (like PostgreSQL or BigQuery) and perform the aggregation via SQL before reading it into Python.

### Q9: What is PEP-8 and how did you ensure compliance?
* **Answer:** PEP-8 is the official style guide for Python code. I followed it by grouping imports (stdlib, third-party, local), using type hints, writing docstrings, using snake_case for functions/variables, and maintaining appropriate line spacing.

### Q10: How do you handle potential division-by-zero errors in Python calculations?
* **Answer:** When calculating ratios like `Revenue_Growth = (rev_sh - rev_fh) / rev_fh`, a customer with zero spend in the first half (`rev_fh = 0`) will cause a division-by-zero error. I solved this by adding a tiny epsilon value to the denominator: `rev_fh + 1e-5`.

---

## 🗄️ Section 2: SQL & Database Design (Questions 11 - 20)

### Q11: What is a CTE and why is it preferred over subqueries?
* **Answer:** A **Common Table Expression (CTE)** is a temporary named result set defined using the `WITH` clause. CTEs are preferred over subqueries because they improve query readability, allow top-down query design, and can be referenced multiple times within the same query.

### Q12: How do you calculate rolling averages in SQL?
* **Answer:** I use window functions with a frame clause. For example:
  `AVG(revenue) OVER (ORDER BY year_month ROWS BETWEEN 2 PRECEDING AND CURRENT ROW)` calculates a 3-month rolling average of monthly revenue.

### Q13: What is the purpose of the `NTILE()` window function?
* **Answer:** `NTILE(N)` divides an ordered partition of rows into $N$ equal-sized buckets and assigns a bucket number from 1 to $N$ to each row. I used `NTILE(5)` in SQL to assign Recency, Frequency, and Monetary scores (1 to 5) for RFM analysis.

### Q14: How does a database index speed up queries?
* **Answer:** An index creates a lookup structure (typically a B-Tree) for the indexed column, allowing the database engine to locate matching rows in $O(\log N)$ time instead of performing a full table scan ($O(N)$). I created indexes on `CustomerID`, `InvoiceDate`, and `StockCode` to optimize RFM aggregations.

### Q15: Explain the difference between `RANK()`, `DENSE_RANK()`, and `ROW_NUMBER()`.
* **Answer:** 
  * `ROW_NUMBER()` assigns a unique sequential integer to each row starting at 1.
  * `RANK()` assigns ranking numbers but leaves gaps if there are ties (e.g. 1, 2, 2, 4).
  * `DENSE_RANK()` assigns rankings consecutively without leaving gaps (e.g. 1, 2, 2, 3).

### Q16: How do you calculate a repeat purchase rate in a single SQL query?
* **Answer:** I write a query that aggregates orders per customer in a CTE, then calculates the ratio of customers with order counts $> 1$ to the total count of unique customers. (See query 5 in `sql/03_customer_analysis.sql` for implementation).

### Q17: What is the difference between `WHERE` and `HAVING` clauses?
* **Answer:** `WHERE` filters rows *before* aggregation (grouping), while `HAVING` filters aggregated groups *after* the `GROUP BY` clause is applied.

### Q18: What is a Database View and why did you create them in this project?
* **Answer:** A **View** is a virtual table representing the result of a saved SQL query. I created views (like `v_rfm_segments`) to encapsulate complex SQL joins and aggregations, providing clean, pre-calculated endpoints for Power BI and Streamlit to query directly.

### Q19: How do you handle NULL values in SQL arithmetic?
* **Answer:** Any arithmetic operation with NULL results in NULL. To prevent this, I use the `COALESCE(column, 0)` function, which returns the column value if not null, otherwise returning 0.

### Q20: Explain the query optimization strategy you used for the transactions table.
* **Answer:** I used three strategies:
  1. Created composite indexes on foreign keys.
  2. Applied pre-filters in `WHERE` clauses (e.g. filtering out cancellations early) to minimize data processed by joins.
  3. Replaced subqueries with CTEs to allow the database compiler to optimize execution plans.

---

## 🤖 Section 3: Machine Learning & Modeling (Questions 21 - 30)

### Q21: Why is $R^2$ typical for e-commerce CLTV regression around 0.10 - 0.20?
* **Answer:** E-commerce purchase behavior in non-contractual settings is highly stochastic (random). Customers buy at irregular intervals, and can stop buying without telling the business. High $R^2$ (e.g. 0.90) in e-commerce CLTV is often a sign of data leakage (e.g. including future target metrics in features).

### Q22: What is the difference between bagging and boosting?
* **Answer:** **Bagging** (e.g. Random Forest) trains multiple models in parallel, each on a bootstrap sample of the data, and averages their predictions to reduce variance. **Boosting** (e.g. XGBoost, Gradient Boosting) trains models sequentially, where each new model is fitted to correct the errors (residuals) of the previous models, reducing bias.

### Q23: Why does XGBoost outperform Linear Regression for CLTV prediction?
* **Answer:** Linear Regression assumes linear relationships and no interactions between features. XGBoost, as a tree-based ensemble, captures non-linear relationships (e.g. the effect of Recency is non-linear — after 90 days, churn risk spikes exponentially) and interactions (e.g. High Frequency is only valuable if Recency is low).

### Q24: What hyperparameters did you tune in XGBoost and how?
* **Answer:** I tuned `max_depth` (complexity of trees), `learning_rate` (step size shrink), `n_estimators` (number of trees), and `subsample` (row sampling ratio) using `RandomizedSearchCV` with 5-fold cross-validation.

### Q25: How do you evaluate a regression model when the target has a long tail?
* **Answer:** E-commerce spend distributions are heavily right-skewed. RMSE penalizes large errors heavily, making it sensitive to extreme spenders. I use **MAE** (Mean Absolute Error) as a robust measure of typical error, and log-transform the target during experimentation if needed, or evaluate models using Rank Correlation (Spearman) to see how well they rank customer values.

### Q26: Explain the bias-variance tradeoff.
* **Answer:** Bias is the error from erroneous assumptions in the learning algorithm (underfitting). Variance is the error from sensitivity to small fluctuations in the training set (overfitting). We balance them to minimize total error.

### Q27: How does Cross-Validation prevent overfitting?
* **Answer:** K-Fold cross-validation splits the training data into $K$ parts. The model is trained on $K-1$ parts and validated on the remaining part, repeating $K$ times. This ensures model metrics are averaged across different folds, indicating how well the model generalizes to unseen data.

### Q28: What is hyperparameter tuning and why is it necessary?
* **Answer:** Hyperparameters are configuration settings of the algorithm that are not learned from the data. Tuning (like Random Search) finds the combination of settings that maximizes validation performance and minimizes overfitting.

### Q29: What is the risk of having too many engineered features?
* **Answer:** Too many features can lead to the **curse of dimensionality** and overfitting, where the model learns noise in the training set. It also increases computational cost and reduces model interpretability.

### Q30: Why did you not use a Deep Learning model for this dataset?
* **Answer:** Tabular datasets with structured behavioral features (like RFM) are typically modeled best by tree-based ensembles (XGBoost/LightGBM). Deep Learning requires significantly more data to generalize well on tabular features and lacks out-of-the-box explainability like SHAP.

---

## 📊 Section 4: Business Intelligence & Power BI (Questions 31 - 40)

### Q31: What is a Star Schema and why is it used?
* **Answer:** A Star Schema is a database layout consisting of central **Fact tables** (containing transactional metrics) connected to surrounding **Dimension tables** (containing descriptive attributes). It is the standard layout for Power BI because it optimizes query speed and simplifies DAX writing.

### Q32: Explain the difference between Calculated Columns and Measures in Power BI.
* **Answer:** **Calculated Columns** are evaluated row-by-row during data refresh and stored in memory, increasing model size. **Measures** are evaluated dynamically at query time based on user filter contexts, utilizing minimal storage.

### Q33: Write a DAX formula to calculate Customer Churn.
* **Answer:** (See DAX formula 11 in `dashboard/dax_measures.md` for the exact code block).

### Q34: What is Filter Context in Power BI?
* **Answer:** Filter Context refers to any filtering applied to a visual by slicers, report filters, columns/rows in tables, or cross-filtering from other charts on the page.

### Q35: How do bookmarks work in Power BI and what is their business use case?
* **Answer:** Bookmarks capture the state of a report page (filters, visual visibility, page location). They are used to create navigation flows, switch between chart views (e.g. switching from raw numbers to percentages), or build guided walkthroughs for stakeholders.

### Q36: What is a Tooltip page and why is it useful?
* **Answer:** A Tooltip page is a custom report page that appears when a user hovers over a data point in another visual. It is useful for displaying micro-visuals or additional metadata without cluttering the main screen.

### Q37: How does drill-through work?
* **Answer:** Drill-through allows users to right-click a data point (like a customer segment) and navigate to a detailed sub-page filtered specifically for that segment.

### Q38: What is DAX `DIVIDE` and why is it preferred over `/`?
* **Answer:** `DIVIDE(numerator, denominator, alternate_result)` is preferred because it automatically handles division-by-zero errors. If the denominator is zero or blank, it returns the alternate result (defaults to blank/0) instead of throwing an error.

### Q39: Why is a Date table required in Power BI?
* **Answer:** A Date table ensures continuous calendar coverage (no missing days), which is required for Power BI time intelligence functions (like `YTD`, `SamePeriodLastYear`, rolling averages) to work correctly.

### Q40: What is the purpose of a custom theme JSON in Power BI?
* **Answer:** A custom theme JSON applies global styles (colors, backgrounds, fonts, visual borders) to all charts automatically, ensuring consistency and brand alignment.

---

## 💼 Section 5: Business Strategy & Behavioral (Questions 41 - 50)

### Q41: A marketing manager complains that the model's MAE is too high. How do you explain the model's value?
* **Answer:** "While the model may not predict exact pennies of future spend, it is highly accurate at ranking customers from high-to-low value (Rank Correlation). The value is not in the precision of the pennies, but in the segment prioritization. It allows us to split customers into tiers and stop wasting high-cost acquisition budgets on low-value cohorts."

### Q42: How does CLTV affect Customer Acquisition Cost (CAC) budgeting?
* **Answer:** LTV sets the upper limit on CAC. If a customer segment has a predicted CLTV of £150, our CAC cap must be strictly below £150 to ensure profitability. The standard healthy industry target is an LTV:CAC ratio $> 3x$.

### Q43: How do you identify a VIP customer segment using CLTV?
* **Answer:** VIPs are customers located in the top decile (top 10%) of predicted next-90-day spend. They are candidates for premium retention offers because they represent a disproportionate share of e-commerce revenue.

### Q44: Tell me about a time you had to justify dropping data to a business stakeholder.
* **Answer:** "I had to explain why we were dropping 20% of rows because of missing Customer IDs. The stakeholder was concerned about losing sales history. I explained that for transactional sales reporting, we retain those rows, but for a customer-level predictive model, a transaction without an ID is anonymous and cannot be used. Dropping them was necessary to prevent model bias."

### Q45: Describe how Swiggy or Zomato might use CLTV.
* **Answer:** They use CLTV to decide:
  1. Which users receive high cashback coupons (targeting at-risk high-CLTV users).
  2. Which zones to prioritize for quick delivery expansions.
  3. Partnerships with restaurants based on order frequency of high-CLTV users.

### Q46: What is a cohort analysis and how does it help retention?
* **Answer:** Cohort analysis groups customers based on their acquisition date (e.g. Month 1) and tracks their retention/revenue over subsequent months. It helps identify which acquisition periods produce the most loyal customer cohorts.

### Q47: If your model predicts high value for a customer who has already churned, what went wrong?
* **Answer:** The model likely relied too heavily on historical spend (Monetary) and did not give enough weight to Recency. This occurs when tree depth is shallow or parameters like `min_child_weight` are too high, preventing the model from isolating recently inactive high-spenders.

### Q48: How would you explain SHAP values to a non-technical C-suite executive?
* **Answer:** "SHAP values show the 'why' behind each customer prediction. If the model predicts John will spend £500, SHAP tells us: his high purchase frequency adds £300, his history of buying diverse products adds £100, but the fact that he hasn't purchased in 45 days subtracts £100. It's a scoreboard explaining the model's math in plain business metrics."

### Q49: If you could add one external dataset to improve this model, what would it be?
* **Answer:** Clickstream data (website browsing logs, cart abandonment events). Knowing what products a customer viewed or added to their cart in the last 7 days is a powerful indicator of near-term purchase intent, far outweighing simple purchase recency.

### Q50: How do you handle conflict with a product manager who wants to deploy a model quickly?
* **Answer:** "I align with their timeline but emphasize risk. I present a comparison showing the baseline model (which can be deployed today) vs. the tuned model. If the baseline has a high error rate that would cause negative customer experiences or wasted marketing spend, I present the financial cost of deploying the weaker model. This translates technical performance into a business risk decision."
