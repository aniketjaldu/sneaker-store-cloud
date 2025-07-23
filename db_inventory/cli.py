
import mysql.connector

def get_product_info(product_id):
    try:
        conn = mysql.connector.connect(
            host="localhost",
            user="root",       
            password="inventorypassword",
            database="inventory_database",
            port="3307"
        )
        cursor = conn.cursor()
        query = """
            SELECT product_name, quantity 
            FROM products 
            WHERE product_id = %s
        """
        cursor.execute(query, (product_id,))
        result = cursor.fetchone()

        if result:
            name, qty = result
            print(f"Product Name: {name}\nQuantity: {qty}")
        else:
            print("Product not found.")

    except mysql.connector.Error as err:
        print(f"Database error: {err}")
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

if __name__ == "__main__":
    try:
        pid = int(input("Enter Product ID: "))
        get_product_info(pid)
    except ValueError:
        print("Invalid input. Please enter a valid numeric Product ID.")
