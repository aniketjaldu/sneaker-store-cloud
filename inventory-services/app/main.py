import os
import sys
import mysql.connector
import requests
from typing import List, Optional

from fastapi import FastAPI, HTTPException, Query, Body
from fastapi.responses import JSONResponse
from pydantic import BaseModel

# Add shared module to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from shared.models import connect_to_db, query_db, close_db, execute_db

app = FastAPI()

def connect_inventory_db():
    return connect_to_db("inventory-db", "root", "inventorypassword", "inventory_database", "3306")

@app.get("/")
def health_check():
    return {"message": "Inventory FastAPI service is operational."}


# ================== ADMIN ROUTES ==================

# ============= Product Management Routes =============

# GET Inventory
@app.get("/admin/products")
async def get_all_inventory(
    brand: Optional[str] = Query(None),
    min_price: Optional[float] = Query(None),
    max_price: Optional[float] = Query(None),
    discount_only: Optional[bool] = Query(False),
    search: Optional[str] = Query(None),
    sort_by: Optional[str] = Query("name"),
    sort_order: Optional[str] = Query("asc"),
    limit: Optional[int] = Query(50),
    offset: Optional[int] = Query(0)
    ):
    try:
        conn = connect_inventory_db()
        query = """
            SELECT p.* from products p
            INNER JOIN brands b ON p.brand_id = b.brand_id
            """
        filters = []
        params = []

        if brand:
            filters.append("brand_name = %s")
            params.append(brand)
        if min_price is not None:
            filters.append("market_price >= %s")
            params.append(min_price)
        if max_price is not None:
            filters.append("market_price <= %s")
            params.append(max_price)
        if discount_only:
            filters.append("discount_percent > 0")
        if search:
            filters.append("(product_name LIKE %s OR description LIKE %s)")
            params.extend([f"%{search}%", f"%{search}%"])

        if filters:
            query += " WHERE " + " AND ".join(filters)

        sort_columns = {
            "name": "product_name",
            "price": "market_price",
            "brand": "brand_id",
            "discount": "discount_percent"
        }

        if sort_by in sort_columns:
            sort_column = sort_columns[sort_by]
            query += f" ORDER BY {sort_column} {'DESC' if sort_order == 'desc' else 'ASC'}"

        query += " LIMIT %s OFFSET %s"
        params.extend([limit, offset])

        result = query_db(conn, query, tuple(params))
        close_db(conn)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# GET Product Details
@app.get("/admin/products/{product_id}")
async def get_product_details(product_id: int):
    try:
        conn = connect_inventory_db()
        query = """
            SELECT p.product_id, p.product_name, p.description, b.brand_name,
                   p.market_price, p.discount_percent,
                   ROUND(p.market_price * (1 - p.discount_percent / 100), 2) AS final_price,
                   p.quantity
            FROM products p
            JOIN brands b ON p.brand_id = b.brand_id
            WHERE p.product_id = %s
        """
        result = query_db(conn, query, (product_id,))
        close_db(conn)

        if not result:
            raise HTTPException(status_code=404, detail="Product not found")

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


#POST Create Product
class ProductCreate(BaseModel):
    brand_id: int
    product_name: str
    description: str
    market_price: float
    discount_percent: float
    quantity: int

@app.post("/admin/products")
async def create_product(product: ProductCreate):
    try:
        conn = connect_inventory_db()
        cursor = conn.cursor()

        query = """
            INSERT INTO products (brand_id, product_name, description, market_price, discount_percent, quantity)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        values = (
            product.brand_id,
            product.product_name,
            product.description,
            product.market_price,
            product.discount_percent,
            product.quantity
        )

        cursor.execute(query, values)
        conn.commit()

        product_id = cursor.lastrowid
        close_db(conn)

        return {"message": "Product created successfully", "product_id": product_id}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# PUT Update Product
class ProductUpdate(BaseModel):
    brand_id: Optional[int]
    product_name: Optional[str]
    description: Optional[str]
    market_price: Optional[float]
    discount_percent: Optional[float]
    quantity: Optional[int]

@app.put("/admin/products/{product_id}")
async def update_product(product_id: int, product: ProductUpdate = Body(...)):
    try:
        conn = connect_inventory_db()
        cursor = conn.cursor()

        # Build SET clause dynamically
        fields = []
        values = []

        for field, value in product.dict(exclude_unset=True).items():
            fields.append(f"{field} = %s")
            values.append(value)

        if not fields:
            raise HTTPException(status_code=400, detail="No fields provided for update.")

        values.append(product_id)
        query = f"UPDATE products SET {', '.join(fields)} WHERE product_id = %s"

        cursor.execute(query, tuple(values))
        conn.commit()

        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Product not found")

        close_db(conn)
        return {"message": "Product updated successfully"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# DELETE product
@app.delete("/admin/products/delete/{product_id}")
async def delete_product(product_id: int):
    try:
        conn = connect_inventory_db()
        cursor = conn.cursor()

        # First, check if the product exists
        cursor.execute("SELECT * FROM products WHERE product_id = %s", (product_id,))
        if cursor.fetchone() is None:
            close_db(conn)
            raise HTTPException(status_code=404, detail="Product not found")

        # Delete the product
        cursor.execute("DELETE FROM products WHERE product_id = %s", (product_id,))
        conn.commit()
        close_db(conn)

        return JSONResponse(status_code=200, content={"message": "Product deleted successfully"})

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ================ Brand Management Routes ===============

# GET All Brands 
@app.get("/admin/brands")
def get_all_brands():
    try:
        conn = connect_inventory_db()
        query = "SELECT * FROM brands ORDER BY brand_id"
        result = query_db(conn, query)
        close_db(conn)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# POST Create Brand
class BrandCreateRequest(BaseModel):
    brand_name: str

@app.post("/admin/brands")
def create_brand(brand: BrandCreateRequest):
    try:
        conn = connect_inventory_db()
        cursor = conn.cursor()
        query = "INSERT INTO brands (brand_name) VALUES (%s)"
        cursor.execute(query, (brand.brand_name,))
        conn.commit()
        new_id = cursor.lastrowid
        close_db(conn)
        return {"message": "Brand created successfully", "brand_id": new_id}
    except mysql.connector.IntegrityError as e:
        raise HTTPException(status_code=400, detail="Brand already exists")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# PUT Update Brand
class BrandUpdate(BaseModel):
    brand_name: str

@app.put("/admin/brands/{brand_id}")
def update_brand(brand_id: int, brand_data: BrandUpdate):
    try:
        conn = connect_inventory_db()
        cursor = conn.cursor()
        query = "UPDATE brands SET brand_name = %s WHERE brand_id = %s"
        cursor.execute(query, (brand_data.brand_name, brand_id))
        if cursor.rowcount == 0:
            close_db(conn)
            raise HTTPException(status_code=404, detail="Brand not found")
        conn.commit()
        close_db(conn)
        return {"message": "Brand updated successfully"}
    except mysql.connector.IntegrityError:
        raise HTTPException(status_code=400, detail="Brand name already exists")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# DELETE Brand 
@app.delete("/admin/brands/{brand_id}")
def delete_brand(brand_id: int):
    try:
        conn = connect_inventory_db()
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM brands WHERE brand_id = %s", (brand_id,))
        if cursor.rowcount == 0:
            close_db(conn)
            raise HTTPException(status_code=404, detail="Brand not found")

        conn.commit()
        close_db(conn)
        return {"message": "Brand deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ================ USER ROUTES Management Routes ===============

# GET All Brands 
@app.get("/brands")
def list_brands():
    try:
        conn = connect_inventory_db()
        query = "SELECT * FROM brands ORDER BY brand_id"
        result = query_db(conn, query)
        close_db(conn)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# GET Inventory
@app.get("/products")
async def list_inventory(
    brand: Optional[str] = Query(None),
    min_price: Optional[float] = Query(None),
    max_price: Optional[float] = Query(None),
    discount_only: Optional[bool] = Query(False),
    search: Optional[str] = Query(None),
    sort_by: Optional[str] = Query("name"),
    sort_order: Optional[str] = Query("asc"),
    limit: Optional[int] = Query(50),
    offset: Optional[int] = Query(0)
    ):
    try:
        conn = connect_inventory_db()
        query = """
            SELECT p.* from products p
            INNER JOIN brands b ON p.brand_id = b.brand_id
            """
        filters = []
        params = []

        if brand:
            filters.append("brand_name = %s")
            params.append(brand)
        if min_price is not None:
            filters.append("market_price >= %s")
            params.append(min_price)
        if max_price is not None:
            filters.append("market_price <= %s")
            params.append(max_price)
        if discount_only:
            filters.append("discount_percent > 0")
        if search:
            filters.append("(product_name LIKE %s OR description LIKE %s)")
            params.extend([f"%{search}%", f"%{search}%"])

        if filters:
            query += " WHERE " + " AND ".join(filters)

        sort_columns = {
            "name": "product_name",
            "price": "market_price",
            "brand": "brand_id",
            "discount": "discount_percent"
        }

        if sort_by in sort_columns:
            sort_column = sort_columns[sort_by]
            query += f" ORDER BY {sort_column} {'DESC' if sort_order == 'desc' else 'ASC'}"

        query += " LIMIT %s OFFSET %s"
        params.extend([limit, offset])

        result = query_db(conn, query, tuple(params))
        close_db(conn)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# GET Product Details
@app.get("/products/{product_id}")
async def list_product_info(product_id: int):
    try:
        conn = connect_inventory_db()
        query = """
            SELECT p.product_id, p.product_name, p.description, b.brand_name,
                   p.market_price, p.discount_percent,
                   ROUND(p.market_price * (1 - p.discount_percent / 100), 2) AS final_price,
                   p.quantity
            FROM products p
            JOIN brands b ON p.brand_id = b.brand_id
            WHERE p.product_id = %s
        """
        result = query_db(conn, query, (product_id,))
        close_db(conn)

        if not result:
            raise HTTPException(status_code=404, detail="Product not found")

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# GET Custom Product Search
@app.get("/inventory/stats")
def get_custom_inventory(
    columns: List[str] = Query(..., description="Columns to select, e.g., product_name, market_price, brand_id"),
    sort_by: str = Query("product_name", description="Column to sort by"),
    sort_order: str = Query("asc", description="Sort order: asc or desc")
):
    allowed_columns = {"product_name", "description", "brand_id", "market_price", "discount_percent", "date_added"}
    if not set(columns).issubset(allowed_columns):
        raise HTTPException(status_code=400, detail="Invalid column(s) requested")

    if sort_by not in allowed_columns:
        raise HTTPException(status_code=400, detail="Invalid sort_by column")

    if sort_order.lower() not in ["asc", "desc"]:
        raise HTTPException(status_code=400, detail="Invalid sort_order value")

    selected_cols = ", ".join(columns)

    try:
        conn = connect_inventory_db()
        cursor = conn.cursor(dictionary=True)

        query = f"""
            SELECT {selected_cols}
            FROM products
            ORDER BY {sort_by} {sort_order.upper()}
        """
        cursor.execute(query)
        results = cursor.fetchall()
        return results
    except mysql.connector.Error as err:
        raise HTTPException(status_code=500, detail=f"Database error: {err}")
    finally:
        close_db(conn)

## CLI stuff

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

    
        # Step 4: Ensure quantity is an integer & Check stock
        if isinstance(quantity, int) and qty_requested > quantity :
            print(f"Not enough stock. Only {quantity} available.")
            return

        # Step 5: Insert order
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
