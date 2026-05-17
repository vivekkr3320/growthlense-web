import csv
import random
import datetime

def generate_mock_csv():
    products = [
        ("Aura Ergonomic Chair", 349.99, "Furniture"),
        ("Nebula USB-C Hub", 49.99, "Electronics"),
        ("Horizon Mechanical Keyboard", 129.99, "Electronics"),
        ("Lunar Desk Mat", 29.99, "Office"),
        ("Zenith Desk Lamp", 79.99, "Office"),
        ("Nova Leather Sleeve", 59.99, "Accessories")
    ]
    
    payment_methods = ["Shopify Payments", "PayPal", "Apple Pay", "Google Pay"]
    regions = ["CA", "NY", "TX", "FL", "WA", "IL", "MA", "CO"]
    statuses = ["paid", "paid", "paid", "paid", "pending", "refunded"]
    
    customers = [
        f"customer_{i}@example.com" for i in range(1, 40)
    ]
    
    # We will generate about 120 line items across 70 separate orders
    start_date = datetime.datetime(2026, 2, 1)
    
    orders = []
    current_order_num = 1001
    
    for i in range(70):
        # 1. Random customer
        cust = random.choice(customers)
        # Randomly choose if they purchase again to simulate a realistic repeat rate (~30%)
        if random.random() < 0.35:
            # Pick a repeat customer
            cust = random.choice(customers[:15])
            
        order_date = start_date + datetime.timedelta(
            days=random.randint(0, 100),
            hours=random.randint(0, 23),
            minutes=random.randint(0, 59)
        )
        
        pay_method = random.choice(payment_methods)
        region = random.choice(regions)
        status = random.choice(statuses)
        
        # 2. Number of items in order
        num_items = random.randint(1, 3)
        order_id = f"#{current_order_num}"
        
        for _ in range(num_items):
            prod_name, prod_price, _ = random.choice(products)
            qty = random.choices([1, 2, 3], weights=[80, 15, 5])[0]
            
            orders.append({
                "Name": order_id,
                "Created at": order_date.strftime("%Y-%m-%d %H:%M:%S %z"),
                "Email": cust,
                "Lineitem name": prod_name,
                "Lineitem quantity": qty,
                "Lineitem price": prod_price,
                "Financial Status": status,
                "Payment Method": pay_method,
                "Billing Province": region
            })
            
        current_order_num += 1

    # Write to mock CSV
    filename = "mock_shopify_orders.csv"
    with open(filename, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "Name", "Created at", "Email", "Lineitem name", 
            "Lineitem quantity", "Lineitem price", "Financial Status", 
            "Payment Method", "Billing Province"
        ])
        writer.writeheader()
        writer.writerows(orders)
        
    print(f"Successfully generated {filename} with {len(orders)} lines.")

if __name__ == "__main__":
    generate_mock_csv()
