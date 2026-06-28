# 📚 Data Dictionary — E-Commerce CLTV Prediction System

This document outlines the schema details, descriptions, constraints, and business logic for all tables, views, and output CSV data in the Customer Lifetime Value (CLTV) Prediction project.

---

## 1. Raw Transaction Log Schema (`data/raw/online_retail_II.csv`)

This is the transactional logging dataset representing purchases on the e-commerce store.

| Column | Data Type | Constraint / Value Range | Description & Business Usage |
| :--- | :--- | :--- | :--- |
| **Invoice** | `String` | 6-digits (or starting with 'C') | Unique purchase invoice document. Starts with 'C' for refund/cancellations. |
| **StockCode** | `String` | 5-digits or alphanumeric code | Unique product SKU code. Used to analyze product performance. |
| **Description** | `String` | Free Text | Text description of the product or service transaction line. |
| **Quantity** | `Integer` | Negative to Positive values | Number of units sold. Negative indicates a cancellation/return request. |
| **InvoiceDate** | `Datetime` | 2009-12-01 to 2011-12-09 | Exact date and time the order was checked out. Used for recency indices. |
| **Price** | `Float` | Unit Price > 0 | Cost of a single product unit in GBP. |
| **Customer ID** | `String` | 5-digits (can be NULL) | Unique client identifier. Empty rows represent guest (unregistered) purchases. |
| **Country** | `String` | Geographic names | Country of customer residence. United Kingdom is the domestic home market (90%+). |

---

## 2. Engineered Customer Profile Schema (`data/features/customer_features.csv`)

These features are engineered from the **Observation Window** (transactions prior to September 1, 2011) to forecast customer spending in the subsequent **Holdout Window** (next 90 days).

| Feature Column | Data Type | Range / Domain | Purpose & Technical Explanation |
| :--- | :--- | :--- | :--- |
| **CustomerID** | `String` | Primary Key | Identifier for joining tables. |
| **Recency** | `Integer` | $[0, 730]$ days | Days between the customer's last purchase in the observation window and the split date. *Strong indicator of active status.* |
| **Frequency** | `Integer` | $\ge 1$ orders | Number of unique invoices (cancellation-free) during the observation period. |
| **Monetary** | `Float` | $\ge 0.0$ (£) | Total cumulative spend of the customer in the observation period. |
| **Tenure** | `Integer` | $[0, 730]$ days | Days since the customer's very first recorded transaction up to the split date. |
| **Product_Diversity**| `Integer` | $\ge 1$ SKUs | Number of unique product StockCodes purchased. High diversity indicates wholesale buyers or collectors. |
| **Avg_Basket_Size** | `Float` | $\ge 1.0$ units | Mean number of product units purchased per invoice order. |
| **Avg_Order_Value**  | `Float` | $\ge 0.0$ (£) | Average revenue per order invoice. Formula: `Monetary / Frequency`. |
| **Avg_Monthly_Spend**| `Float` | $\ge 0.0$ (£) | Mean net revenue generated per calendar month. |
| **Seasonal_Score_Q4**| `Float` | $[0.0, 1.0]$ ratio | Percentage of lifetime spend occurring in Quarter 4. Used to capture holiday buyer behavior. |
| **Avg_Purchase_Interval**| `Float` | $[0.0, 999.0]$ days | Mean days between consecutive orders. Single-purchase users are filled with 999.0. |
| **Revenue_Growth** | `Float` | $[-1.0, \infty)$ index | Percentage change in spend comparing the second half of customer history to the first half. |
| **Is_UK** | `Integer` | $\{0, 1\}$ binary | Flag identifying domestic UK buyers vs. international clients. |
| **target_revenue** | `Float` | $\ge 0.0$ (£) | **The target variable**. Sum of customer purchases in the subsequent 90-day holdout window. |
