import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from shared.models import connect_to_db, query_db, close_db
import mysql.connector


# ***BACKEND TEAM CONFIRM WHETHER IMPORTS BELOW ARE NECESSARY***
import fastapi
import requests

app = fastapi.FastAPI()

@app.get("/")
def read_root():
    return {"message": "Hello, World!"}


DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "inventorypassword",
    "database": "inventory_database",
    "port": 3307
}

def list_products():
    try:
        conn = connect_to_db(**DB_CONFIG)
        query = """
            SELECT product_id, product_name,
                   market_price,
                   discount_percent,
                   ROUND(market_price * (1 - discount_percent / 100), 2) AS final_price,
                   quantity
            FROM products
            ORDER BY product_id
        """
        results = query_db(conn, query)

        print("\n" + "-" * 80)
        print(f"{'ID':<5} {'Product':<27} {'Price':>10} {'Discount':>12} {'Final Price':>14} {'Qty':>7}")
        print("-" * 80)
        for pid, name, price, discount, final_price, qty in results:
            print(f"{pid:<5} {name:<30} ${price:>8.2f} {discount:>9.2f}%     ${final_price:>7.2f} {qty:>8}")

    finally:
        close_db(conn)

def place_order():
    try:
        conn = connect_to_db(**DB_CONFIG)
        cursor = conn.cursor()

        # Step 1: Get desired product ID
        pid = int(input("Enter Product ID to order: "))

        # Step 2: Check if product exists and get available quantity
        cursor.execute("SELECT product_name, quantity FROM products WHERE product_id = %s", (pid,))
        result = cursor.fetchone()

        if not result:
            print("Product not found.")
            return
    
        product_name, quantity = result

        # Step 3: Get desireed quantity
        qty_requested = int(input("Enter quantity to order: "))

    
        # Step 3: Ensure quantity is an integer & Check stock
        if isinstance(quantity, int) and qty_requested > quantity :
            print(f"Not enough stock. Only {quantity} available.")
            return

        # Step 4: Insert order
        insert_query = """
            INSERT INTO orders (product_id, quantity)
            VALUES (%s, %s)
        """
        cursor.execute(insert_query, (pid, qty_requested))

        # Step 5: Update inventory
        update_query = """
            UPDATE products
            SET quantity = quantity - %s
            WHERE product_id = %s
        """
        cursor.execute(update_query, (qty_requested, pid))

        conn.commit() # what do it do
        print(f"Order placed for '{product_name}' (x{qty_requested})")

    except ValueError:
        print("Invalid input. Please enter numeric values only.")
    except mysql.connector.Error as err:
        print(f"Database error: {err}")
    finally:
        if conn.is_connected():
            cursor.close()
            close_db(conn)

def main():
    print("Welcome to SneakerSpot's Inventory CLI")
    while True:
        print("\nChoose an option:")
        print("1 - List Products")
        print("2 - Place an Order")
        print("0 - Exit")

        choice = input("Enter choice: ").strip()
        if choice == '1':
            list_products()
        elif choice == '2':
            place_order()
        elif choice == '0':
            print("Exited.")
            break
        else:
            print("Invalid choice.")

if __name__ == "__main__":
    main()
