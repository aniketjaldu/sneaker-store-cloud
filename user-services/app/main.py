import fastapi
import requests
from fastapi import HTTPException, Request, Query
from pydantic import BaseModel
from typing import Optional
from shared.models import connect_to_db, query_db, close_db, execute_db

app = fastapi.FastAPI()

class UserCreateRequest(BaseModel):
    first_name: str
    last_name: str
    email: str
    password: str
    role: str = "customer"

# Helper function to connect to db
def connect_user_db():
    return connect_to_db("user-db", "root", "userpassword", "user_database", "3306")

def connect_inventory_db():
    return connect_to_db("inventory-db", "root", "inventorypassword", "inventory_database", "3306")

# ========== USER ROUTES ==========
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
    
# ========== ADMIN ROUTES ==========
# GET /users
@app.get("/admin/users")
async def get_all_users(
    role: Optional[str] = Query(None, description="Filter by role: customer or admin"),
    search: Optional[str] = Query(None, description="Search by name or email"),
    limit: Optional[int] = Query(50, description="Number of results to return"),
    offset: Optional[int] = Query(0, description="Number of results to skip")
):
    try:
        conn = connect_user_db()
        query = """
            SELECT *
            FROM users u
            INNER JOIN user_roles ur
            ON ur.user_id = u.user_id
        """
        filter = []
        params = []

        if role:
            filter.append("role = %s")
            params.append(role)

        if search:
            filter.append("""
                        (
                        LOWER(first_name) LIKE LOWER(%s) OR
                        LOWER(last_name) LIKE LOWER(%s) OR
                        LOWER(email) LIKE LOWER(%s)
                        )
                        """)
            search_value = f"%{search}%"
            params.extend([search_value, search_value, search_value])

        if filter:
            query += " WHERE " + " AND ".join(filter)

        query += " LIMIT %s OFFSET %s"
        params.extend([limit, offset])

        result = query_db(conn, query, tuple(params))
        close_db(conn)
        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
# GET /users/{user_id}
@app.get("/admin/users/{user_id}")
async def get_user_details(user_id: int):
    try:
        conn = connect_user_db()
        query = f"SELECT * FROM users WHERE user_id = {user_id}"

        result = query_db(conn, query)
        close_db(conn)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
# TODO: Fix this route with foreign constraints
# POST /users
@app.post("/admin/users")
async def create_user(user: UserCreateRequest, role: str = Query("customer")):
    try:
        conn = connect_user_db()
        
        # Insert user into the users table
        user_query = """
            INSERT INTO users (first_name, last_name, email, password)
            VALUES (%s, %s, %s, %s)
        """
        user_values = (user.first_name, user.last_name, user.email, user.password)
        cursor = conn.cursor()
        cursor.execute(user_query, user_values)
        user_id = cursor.lastrowid
        conn.commit()
        cursor.close()
        
        # Insert into user_roles table
        role_query = """
            INSERT INTO user_roles (user_id, role)
            VALUES (%s, %s)
        """
        role_values = (user_id, role)
        execute_db(conn, role_query, role_values)
        
        close_db(conn)
        return {"message": "User created successfully", "user_id": user_id}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# PUT /users
@app.put("/admin/users/{user_id}")
async def update_user(user_id: int, request: Request):
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
        return {"message": "User updated successfully"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# TODO: Fix foreign key constraints with inventory
# DELETE /users
@app.delete("/admin/users/{user_id}")
async def delete_user(user_id: int):
    try:   
        conn = connect_user_db()

        # Delete user role first
        role_query = "DELETE FROM user_roles WHERE user_id = %s"
        execute_db(conn, role_query, (user_id,))

        # Delete user
        user_query = "DELETE FROM users WHERE user_id = %s"
        execute_db(conn, user_query, (user_id,))

        close_db(conn)

        return {"message": "User has been deleted"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# PUT /users role
@app.post("/admin/users")
async def update_user_role():
    try:   
        conn = connect_user_db()
        close_db(conn)
        return
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))