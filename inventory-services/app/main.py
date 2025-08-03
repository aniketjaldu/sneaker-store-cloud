import os
import sys
import mysql.connector
import requests
from typing import List, Optional

from fastapi import FastAPI, HTTPException, Query, Body
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


# ================ ANALYTICS ROUTES ===============

@app.get("/admin/analytics/inventory")
def get_inventory_analytics():
    try:
        conn = connect_inventory_db()
        
        # Get total products
        total_products_query = "SELECT COUNT(*) as total FROM products"
        total_products = query_db(conn, total_products_query)[0]["total"]
        
        # Get total brands
        total_brands_query = "SELECT COUNT(*) as total FROM brands"
        total_brands = query_db(conn, total_brands_query)[0]["total"]
        
        # Get discounted products
        discounted_products_query = "SELECT COUNT(*) as total FROM products WHERE discount_percent > 0"
        discounted_products = query_db(conn, discounted_products_query)[0]["total"]
        
        # Get average price
        avg_price_query = "SELECT AVG(market_price) as avg_price FROM products"
        avg_price_result = query_db(conn, avg_price_query)[0]
        avg_price = avg_price_result["avg_price"] if avg_price_result["avg_price"] else 0
        
        # Get total inventory value
        total_value_query = "SELECT SUM(market_price * quantity) as total_value FROM products"
        total_value_result = query_db(conn, total_value_query)[0]
        total_value = total_value_result["total_value"] if total_value_result["total_value"] else 0
        
        close_db(conn)
        
        return {
            "total_products": total_products,
            "total_brands": total_brands,
            "discounted_products": discounted_products,
            "average_price": round(avg_price, 2),
            "total_inventory_value": round(total_value, 2)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ================ ADMIN ROUTES ==================

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
            SELECT p.*, b.brand_name from products p
            INNER JOIN brands b ON p.brand_id = b.brand_id
            """
        filters = []
        params = []

        if brand:
            filters.append("b.brand_name = %s")
            params.append(brand)
        if min_price is not None:
            filters.append("p.market_price >= %s")
            params.append(min_price)
        if max_price is not None:
            filters.append("p.market_price <= %s")
            params.append(max_price)
        if discount_only:
            filters.append("p.discount_percent > 0")
        if search:
            filters.append("(p.product_name LIKE %s OR p.description LIKE %s)")
            params.extend([f"%{search}%", f"%{search}%"])

        if filters:
            query += " WHERE " + " AND ".join(filters)

        sort_columns = {
            "name": "p.product_name",
            "price": "p.market_price",
            "brand": "b.brand_name",
            "discount": "p.discount_percent",
            "date_added": "p.date_added"
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
                   p.quantity, p.date_added
            FROM products p
            JOIN brands b ON p.brand_id = b.brand_id
            WHERE p.product_id = %s
        """
        result = query_db(conn, query, (product_id,))
        close_db(conn)

        if not result:
            raise HTTPException(status_code=404, detail="Product not found")

        return result[0]

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


#POST Create Product
class ProductCreate(BaseModel):
    brand_id: int
    product_name: str
    description: Optional[str] = None
    market_price: float
    discount_percent: float = 0.0

@app.post("/admin/products")
async def create_product(product: ProductCreate):
    try:
        conn = connect_inventory_db()
        cursor = conn.cursor()

        query = """
            INSERT INTO products (brand_id, product_name, description, market_price, discount_percent, quantity)
            VALUES (%s, %s, %s, %s, %s, 0)
        """
        values = (
            product.brand_id,
            product.product_name,
            product.description,
            product.market_price,
            product.discount_percent
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
    brand_id: Optional[int] = None
    product_name: Optional[str] = None
    description: Optional[str] = None
    market_price: Optional[float] = None
    discount_percent: Optional[float] = None
    quantity: Optional[int] = None

@app.put("/admin/products/{product_id}")
async def update_product(product_id: int, product: ProductUpdate = Body(...)):
    try:
        conn = connect_inventory_db()
        cursor = conn.cursor()

        # Build SET clause dynamically
        fields = []
        values = []

        for field, value in product.dict(exclude_unset=True).items():
            if value is not None:
                fields.append(f"{field} = %s")
                values.append(value)

        if not fields:
            raise HTTPException(status_code=400, detail="No fields provided for update.")

        values.append(product_id)
        query = f"UPDATE products SET {', '.join(fields)} WHERE product_id = %s"

        cursor.execute(query, tuple(values))
        conn.commit()

        close_db(conn)
        if cursor.rowcount == 0:
            return {"message": "No fields changed. Product data remains the same."}
        return {"message": "Product updated successfully"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# DELETE product
@app.delete("/admin/products/{product_id}")
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

        return {"message": "Product deleted successfully"}

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
            SELECT p.*, b.brand_name from products p
            INNER JOIN brands b ON p.brand_id = b.brand_id
            """
        filters = []
        params = []

        if brand:
            filters.append("b.brand_name = %s")
            params.append(brand)
        if min_price is not None:
            filters.append("p.market_price >= %s")
            params.append(min_price)
        if max_price is not None:
            filters.append("p.market_price <= %s")
            params.append(max_price)
        if discount_only:
            filters.append("p.discount_percent > 0")
        if search:
            filters.append("(p.product_name LIKE %s OR p.description LIKE %s)")
            params.extend([f"%{search}%", f"%{search}%"])

        if filters:
            query += " WHERE " + " AND ".join(filters)

        sort_columns = {
            "name": "p.product_name",
            "price": "p.market_price",
            "brand": "b.brand_name",
            "discount": "p.discount_percent",
            "date_added": "p.date_added"
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

# GET Product Statistics
@app.get("/products/stats")
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

# GET Product Details
@app.get("/products/{product_id}")
async def list_product_info(product_id: int):
    try:
        conn = connect_inventory_db()
        query = """
            SELECT p.product_id, p.product_name, p.description, b.brand_name,
                   p.market_price, p.discount_percent,
                   ROUND(p.market_price * (1 - p.discount_percent / 100), 2) AS final_price,
                   p.quantity, p.date_added
            FROM products p
            JOIN brands b ON p.brand_id = b.brand_id
            WHERE p.product_id = %s
        """
        result = query_db(conn, query, (product_id,))
        close_db(conn)

        if not result:
            raise HTTPException(status_code=404, detail="Product not found")

        return result[0]

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# GET Custom Product Search
# ================ STOCK MANAGEMENT ROUTES ===============

@app.get("/products/{product_id}/stock")
async def get_product_stock(product_id: int):
    try:
        conn = connect_inventory_db()
        
        # Check if product exists and get stock
        query = "SELECT product_id, product_name, quantity FROM products WHERE product_id = %s"
        result = query_db(conn, query, (product_id,))
        close_db(conn)
        
        if not result:
            raise HTTPException(status_code=404, detail="Product not found")
        
        product = result[0]
        return {
            "product_id": product["product_id"],
            "product_name": product["product_name"],
            "current_stock": product["quantity"],
            "available": product["quantity"] > 0
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/products/{product_id}/reserve-stock")
async def reserve_stock(product_id: int, quantity: int = Query(...)):
    try:
        if quantity <= 0:
            raise HTTPException(status_code=400, detail="Quantity must be greater than 0")
        
        conn = connect_inventory_db()
        
        # Check if product exists and has sufficient stock
        query = "SELECT product_id, product_name, quantity FROM products WHERE product_id = %s"
        result = query_db(conn, query, (product_id,))
        
        if not result:
            close_db(conn)
            raise HTTPException(status_code=404, detail="Product not found")
        
        product = result[0]
        current_stock = product["quantity"]
        
        if current_stock < quantity:
            close_db(conn)
            raise HTTPException(
                status_code=400, 
                detail=f"Insufficient stock. Available: {current_stock}, Requested: {quantity}"
            )
        
        # Reserve stock by reducing available quantity
        update_query = "UPDATE products SET quantity = %s WHERE product_id = %s"
        new_stock = current_stock - quantity
        execute_db(conn, update_query, (new_stock, product_id))
        
        close_db(conn)
        return {
            "message": "Stock reserved successfully",
            "product_id": product_id,
            "reserved_quantity": quantity,
            "remaining_stock": new_stock
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/products/{product_id}/release-stock")
async def release_stock(product_id: int, quantity: int = Query(...)):
    try:
        if quantity <= 0:
            raise HTTPException(status_code=400, detail="Quantity must be greater than 0")
        
        conn = connect_inventory_db()
        
        # Check if product exists
        query = "SELECT product_id, product_name, quantity FROM products WHERE product_id = %s"
        result = query_db(conn, query, (product_id,))
        
        if not result:
            close_db(conn)
            raise HTTPException(status_code=404, detail="Product not found")
        
        product = result[0]
        current_stock = product["quantity"]
        
        # Release stock by increasing available quantity
        update_query = "UPDATE products SET quantity = %s WHERE product_id = %s"
        new_stock = current_stock + quantity
        execute_db(conn, update_query, (new_stock, product_id))
        
        close_db(conn)
        return {
            "message": "Stock released successfully",
            "product_id": product_id,
            "released_quantity": quantity,
            "current_stock": new_stock
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/products/{product_id}/validate-stock")
async def validate_stock(product_id: int, quantity: int = Query(...)):
    try:
        if quantity <= 0:
            raise HTTPException(status_code=400, detail="Quantity must be greater than 0")
        
        conn = connect_inventory_db()
        
        # Check if product exists and has sufficient stock
        query = "SELECT product_id, product_name, quantity FROM products WHERE product_id = %s"
        result = query_db(conn, query, (product_id,))
        close_db(conn)
        
        if not result:
            raise HTTPException(status_code=404, detail="Product not found")
        
        product = result[0]
        current_stock = product["quantity"]
        
        return {
            "product_id": product_id,
            "product_name": product["product_name"],
            "current_stock": current_stock,
            "requested_quantity": quantity,
            "available": current_stock >= quantity,
            "sufficient_stock": current_stock >= quantity
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ========== ADMIN STOCK MANAGEMENT ROUTES ==========
@app.post("/admin/products/{product_id}/reserve-stock")
async def admin_reserve_stock(product_id: int, quantity: int = Query(...)):
    try:
        conn = connect_inventory_db()
        
        # Check if product exists
        product_query = "SELECT quantity FROM products WHERE product_id = %s"
        product_result = query_db(conn, product_query, (product_id,))
        
        if not product_result:
            close_db(conn)
            raise HTTPException(status_code=404, detail="Product not found")
        
        current_stock = product_result[0]["quantity"]
        
        if current_stock < quantity:
            close_db(conn)
            raise HTTPException(
                status_code=400, 
                detail=f"Insufficient stock. Available: {current_stock}, Requested: {quantity}"
            )
        
        # Reserve stock
        new_stock = current_stock - quantity
        update_query = "UPDATE products SET quantity = %s WHERE product_id = %s"
        execute_db(conn, update_query, (new_stock, product_id))
        
        close_db(conn)
        
        return {
            "message": f"Stock reserved successfully",
            "product_id": product_id,
            "quantity_reserved": quantity,
            "remaining_stock": new_stock
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/admin/products/{product_id}/release-stock")
async def admin_release_stock(product_id: int, quantity: int = Query(...)):
    try:
        conn = connect_inventory_db()
        
        # Check if product exists
        product_query = "SELECT quantity FROM products WHERE product_id = %s"
        product_result = query_db(conn, product_query, (product_id,))
        
        if not product_result:
            close_db(conn)
            raise HTTPException(status_code=404, detail="Product not found")
        
        current_stock = product_result[0]["quantity"]
        
        # Release stock back to inventory
        new_stock = current_stock + quantity
        update_query = "UPDATE products SET quantity = %s WHERE product_id = %s"
        execute_db(conn, update_query, (new_stock, product_id))
        
        close_db(conn)
        
        return {
            "message": f"Stock released successfully",
            "product_id": product_id,
            "quantity_released": quantity,
            "current_stock": new_stock
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/admin/products/{product_id}/validate-stock")
async def admin_validate_stock(product_id: int, quantity: int = Query(...)):
    try:
        conn = connect_inventory_db()
        
        # Check if product exists
        product_query = "SELECT quantity FROM products WHERE product_id = %s"
        product_result = query_db(conn, product_query, (product_id,))
        
        if not product_result:
            close_db(conn)
            raise HTTPException(status_code=404, detail="Product not found")
        
        current_stock = product_result[0]["quantity"]
        available = current_stock >= quantity
        
        close_db(conn)
        
        return {
            "product_id": product_id,
            "available": available,
            "current_stock": current_stock,
            "requested_quantity": quantity
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
