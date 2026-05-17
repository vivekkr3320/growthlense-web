import io
import pandas as pd
from typing import Optional, Tuple

def parse_shopify_export(file_content: bytes, filename: str) -> Tuple[pd.DataFrame, Optional[str]]:
    """
    Parses a Shopify order export (CSV or Excel) and normalizes it to a predictable schema:
    - order_id
    - date
    - customer_id
    - product_name
    - quantity
    - price
    - total_price
    - payment_method
    - status
    - region

    Returns:
        (DataFrame, error_message)
    """
    try:
        # Load the file based on its extension
        if filename.endswith(".csv"):
            df = pd.read_csv(io.BytesIO(file_content), encoding="utf-8-sig")
        elif filename.endswith((".xlsx", ".xls")):
            df = pd.read_excel(io.BytesIO(file_content))
        else:
            return pd.DataFrame(), "Unsupported file format. Please upload a .csv or .xlsx file."
        
        if df.empty:
            return pd.DataFrame(), "The uploaded file is empty."

        # Debug print columns for server logs
        print(f"Loaded file {filename} with columns: {list(df.columns)}")

        # Define mapping from possible Shopify/standard headers to our normalized schema
        column_mappings = {
            "order_id": ["Name", "Id", "Order ID", "order_id", "Order No", "OrderNumber"],
            "date": ["Created at", "Date", "Created At", "date", "Order Date", "created_at"],
            "customer_id": ["Email", "Customer ID", "Customer", "customer_id", "CustomerEmail", "User ID"],
            "product_name": ["Lineitem name", "Product Name", "Line item name", "product_name", "Title", "Item Name"],
            "quantity": ["Lineitem quantity", "Quantity", "Line item quantity", "quantity", "Qty", "Item Qty"],
            "price": ["Lineitem price", "Price", "Line item price", "price", "Item Price", "Unit Price"],
            "total_price": ["total_price", "Total Price", "Lineitem total", "Line item total", "Total"],
            "payment_method": ["Payment Method", "Payment Method Column", "payment_method", "Gateway", "Payment Gateway"],
            "status": ["Financial Status", "Fulfillment Status", "Status", "status", "Order Status"],
            "region": ["Billing Province", "Billing Province Name", "Billing Region", "Region", "Billing Country", "region"]
        }

        normalized_df = pd.DataFrame()

        # Build normalized dataframe by locating and mapping columns
        for norm_col, matching_fields in column_mappings.items():
            found_col = None
            for field in matching_fields:
                # Case-insensitive comparison and strip whitespace
                matching_cols = [c for c in df.columns if str(c).strip().lower() == field.lower()]
                if matching_cols:
                    found_col = matching_cols[0]
                    break
            
            if found_col is not None:
                normalized_df[norm_col] = df[found_col]
            else:
                # If optional fields are missing, initialize with default values
                if norm_col in ["payment_method", "status", "region"]:
                    normalized_df[norm_col] = "Unknown"
                elif norm_col == "total_price":
                    # We will compute total_price below if we have quantity and price
                    normalized_df[norm_col] = None
                else:
                    # Missing critical columns
                    # We can assign an empty column or generate placeholder if we want to be flexible,
                    # but let's try to fall back gracefully or return error for critical fields.
                    if norm_col == "order_id":
                        # If order_id is missing, look for any column containing 'id' or 'name' or use index
                        id_cols = [c for c in df.columns if "id" in str(c).lower() or "name" in str(c).lower()]
                        if id_cols:
                            normalized_df[norm_col] = df[id_cols[0]]
                        else:
                            normalized_df[norm_col] = [f"ORD-{i+1000}" for i in range(len(df))]
                    elif norm_col == "date":
                        # Look for date columns
                        date_cols = [c for c in df.columns if "date" in str(c).lower() or "time" in str(c).lower()]
                        if date_cols:
                            normalized_df[norm_col] = df[date_cols[0]]
                        else:
                            normalized_df[norm_col] = pd.Timestamp.now()
                    elif norm_col == "customer_id":
                        email_cols = [c for c in df.columns if "email" in str(c).lower() or "customer" in str(c).lower()]
                        if email_cols:
                            normalized_df[norm_col] = df[email_cols[0]]
                        else:
                            normalized_df[norm_col] = "guest-customer"
                    elif norm_col == "product_name":
                        name_cols = [c for c in df.columns if "product" in str(c).lower() or "item" in str(c).lower()]
                        if name_cols:
                            normalized_df[norm_col] = df[name_cols[0]]
                        else:
                            normalized_df[norm_col] = "Standard Product"
                    elif norm_col == "quantity":
                        normalized_df[norm_col] = 1
                    elif norm_col == "price":
                        normalized_df[norm_col] = 0.0

        # Type conversion & cleanups
        # 1. Clean numbers
        for col in ["quantity", "price", "total_price"]:
            if col in normalized_df.columns and normalized_df[col] is not None:
                # Remove currency symbols and commas, then convert to numeric
                normalized_df[col] = pd.to_numeric(
                    normalized_df[col].astype(str).str.replace(r"[^\d\.]", "", regex=True), 
                    errors="coerce"
                )

        normalized_df["quantity"] = normalized_df["quantity"].fillna(1).astype(int)
        normalized_df["price"] = normalized_df["price"].fillna(0.0).astype(float)

        # 2. Compute total price if missing or null
        if "total_price" not in normalized_df.columns or normalized_df["total_price"].isnull().all():
            normalized_df["total_price"] = normalized_df["quantity"] * normalized_df["price"]
        else:
            normalized_df["total_price"] = normalized_df["total_price"].fillna(normalized_df["quantity"] * normalized_df["price"]).astype(float)

        # 3. Standardize dates
        normalized_df["date"] = pd.to_datetime(normalized_df["date"], errors="coerce")
        # Fill missing dates with current time
        normalized_df["date"] = normalized_df["date"].fillna(pd.Timestamp.now())

        # 4. Fill strings
        normalized_df["order_id"] = normalized_df["order_id"].astype(str).str.strip()
        normalized_df["customer_id"] = normalized_df["customer_id"].astype(str).str.strip()
        normalized_df["product_name"] = normalized_df["product_name"].astype(str).str.strip()
        normalized_df["payment_method"] = normalized_df["payment_method"].fillna("Unknown").astype(str).str.strip()
        normalized_df["status"] = normalized_df["status"].fillna("Paid").astype(str).str.strip()
        normalized_df["region"] = normalized_df["region"].fillna("Unknown").astype(str).str.strip()

        # Filter out rows that have null order_ids or empty names
        normalized_df = normalized_df[normalized_df["order_id"] != "nan"]

        return normalized_df, None
    except Exception as e:
        import traceback
        traceback.print_exc()
        return pd.DataFrame(), f"Failed to parse sheet: {str(e)}"
