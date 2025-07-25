import fastapi
import requests
from shared.models import connect_to_db, query_db, close_db

app = fastapi.FastAPI()

@app.get("/")
def read_root():
    return {"message": "Hello, World!"}


# DB config
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "inventorypassword",
    "database": "inventory_database",
    "port": 3307
}

def get_product_info(product_id):
    try:
        conn = connect_to_db(**DB_CONFIG)
        query = f"""
            SELECT product_name, quantity
            FROM products
            WHERE product_id = {product_id}
        """
        result = query_db(conn, query)

        if result:
            name, qty = result[0]
            print(f"Product Name: {name}\nQuantity: {qty}")
        else:
            print("Product not found.")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        close_db(conn)

if __name__ == "__main__":
    try:
        pid = int(input("Enter Product ID: "))
        get_product_info(pid)
    except ValueError:
        print("Invalid input. Please enter a valid numeric Product ID.")
