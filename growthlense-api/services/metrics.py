import pandas as pd
from typing import Dict, Any

def calculate_metrics(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Computes a premium set of e-commerce metrics from a normalized DataFrame.
    """
    if df.empty:
        return {
            "revenue": 0.0,
            "orders": 0,
            "aov": 0.0,
            "customers": 0,
            "repeat_rate": 0.0,
            "top_products": {},
            "top_products_qty": {},
            "regional_sales": {},
            "payment_methods": {},
            "sales_trend": []
        }

    # 1. Total Revenue
    revenue = float(df["total_price"].sum())

    # 2. Total Orders
    orders = int(df["order_id"].nunique())

    # 3. Average Order Value
    aov = float(revenue / orders) if orders > 0 else 0.0

    # 4. Total Customers
    customers = int(df["customer_id"].nunique())

    # 5. Repeat Purchase Rate (RPR)
    # Number of customers with > 1 order / total customers
    customer_order_counts = df.groupby("customer_id")["order_id"].nunique()
    repeat_customers = int((customer_order_counts > 1).sum())
    repeat_rate = float(repeat_customers / customers) if customers > 0 else 0.0

    # 6. Top Products by Revenue
    top_products = (
        df.groupby("product_name")["total_price"]
        .sum()
        .sort_values(ascending=False)
        .head(5)
        .to_dict()
    )
    # Round revenue values
    top_products = {k: round(float(v), 2) for k, v in top_products.items()}

    # 7. Top Products by Quantity
    top_products_qty = (
        df.groupby("product_name")["quantity"]
        .sum()
        .sort_values(ascending=False)
        .head(5)
        .to_dict()
    )
    top_products_qty = {k: int(v) for k, v in top_products_qty.items()}

    # 8. Regional Distribution
    regional_sales = (
        df.groupby("region")["total_price"]
        .sum()
        .sort_values(ascending=False)
        .head(5)
        .to_dict()
    )
    regional_sales = {k: round(float(v), 2) for k, v in regional_sales.items()}

    # 9. Payment Methods Distribution
    payment_methods = (
        df.groupby("payment_method")["total_price"]
        .sum()
        .sort_values(ascending=False)
        .to_dict()
    )
    payment_methods = {k: round(float(v), 2) for k, v in payment_methods.items()}

    # 10. Monthly/Weekly Sales Trend for Recharts
    # Let's group by date (formatted as YYYY-MM or YYYY-MM-DD depending on span)
    # We will format dates to string "YYYY-MM"
    df_trend = df.copy()
    df_trend["period"] = df_trend["date"].dt.strftime("%Y-%m")
    
    trend_group = df_trend.groupby("period").agg(
        revenue=("total_price", "sum"),
        orders=("order_id", "nunique")
    ).sort_index()

    sales_trend = []
    for idx, row in trend_group.iterrows():
        sales_trend.append({
            "name": str(idx), # e.g. "2026-05"
            "revenue": round(float(row["revenue"]), 2),
            "orders": int(row["orders"])
        })

    # If the dates are mostly within the same month, let's group by day
    if len(sales_trend) <= 1:
        df_trend["period"] = df_trend["date"].dt.strftime("%Y-%m-%d")
        trend_group = df_trend.groupby("period").agg(
            revenue=("total_price", "sum"),
            orders=("order_id", "nunique")
        ).sort_index().tail(15) # last 15 days if single month
        
        sales_trend = []
        for idx, row in trend_group.iterrows():
            sales_trend.append({
                "name": str(idx),
                "revenue": round(float(row["revenue"]), 2),
                "orders": int(row["orders"])
            })

    return {
        "revenue": round(revenue, 2),
        "orders": orders,
        "aov": round(aov, 2),
        "customers": customers,
        "repeat_rate": round(repeat_rate * 100, 2), # In percentage (e.g. 24.5%)
        "top_products": top_products,
        "top_products_qty": top_products_qty,
        "regional_sales": regional_sales,
        "payment_methods": payment_methods,
        "sales_trend": sales_trend
    }
