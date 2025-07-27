import fastapi
import requests
from fastapi import HTTPException, Request, Query
from pydantic import BaseModel
from typing import Optional
from shared.models import connect_to_db, query_db, close_db, execute_db

app = fastapi.FastAPI()

# Helper function to connect to db
def connect_user_db():
    return connect_to_db("user-db", "root", "userpassword", "user_database", "3306")

def connect_inventory_db():
    return connect_to_db("inventory-db", "root", "inventorypassword", "inventory_database", "3306")

@app.get("/")
def read_root():
    return {"message": "Hello, World!"}

@app.get("/users")
def get_user_info():
    conn = connect_user_db()
    query = f"SELECT * FROM users"
    result = query_db(conn, query)
    close_db(conn)
    return result

# GET /profile
@app.get("/users/{user_id}")
async def get_user_profile(user_id: int):
    try:   
        conn = connect_user_db()
        query = "SELECT * FROM users WHERE user_id = %s"
        result = query_db(conn, query, (user_id,))
        close_db(conn)

        if not result:
            raise HTTPException(status_code=404, detail="User not found")
    
        return result[0]
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# PUT /profile
@app.put("/users/{user_id}")
async def update_user_profile(user_id: int, request: Request):
    try:
        profile_data = await request.json()
        if not profile_data:
            raise HTTPException(status_code=400, detail="No profile data provided")
        
        set_clause = ", ".join(f"{key} = %s" for key in profile_data.keys())
        values = list(profile_data.values())
        values.append(user_id)

        conn = connect_user_db()
        query = f"UPDATE users SET {set_clause} where user_id = %s"
        execute_db(conn, query, values)
        close_db(conn)

        return {"message": "User profile updated successfully"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
# GET /inventory
@app.get("/products")
async def get_inventory(
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