import fastapi
import requests
import hashlib
import datetime
from fastapi import HTTPException, Request, Query, Depends
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

class LoginRequest(BaseModel):
    email: str
    password: str

class RefreshTokenRequest(BaseModel):
    token_hash: str

class RefreshTokenUpdateRequest(BaseModel):
    old_token_hash: str
    new_token_hash: str
    expires_at: str

# Helper function to connect to db
def connect_user_db():
    return connect_to_db("user-db", "root", "userpassword", "user_database", "3306")

# ========== ADMIN AUTHENTICATION ROUTES ==========


# Password hashing utility
def hash_password(password: str) -> str:
    return hashlib.sha1(password.encode()).hexdigest()

def verify_password(password: str, hashed_password: str) -> bool:
    return hash_password(password) == hashed_password

@app.get("/")
def read_root():
    return {"message": "User services are running"}

# ========== AUTHENTICATION ROUTES ==========
@app.post("/users/login")
async def login(login_data: LoginRequest):
    try:
        conn = connect_user_db()
        
        # Get user with role information
        query = """
            SELECT u.user_id, u.first_name, u.last_name, u.email, u.password, ur.role
            FROM users u
            INNER JOIN user_roles ur ON u.user_id = ur.user_id
            WHERE u.email = %s
        """
        result = query_db(conn, query, (login_data.email,))
        close_db(conn)
        
        if not result:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        user = result[0]
        
        # Verify password
        if not verify_password(login_data.password, user["password"]):
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        # Return user data
        return {
            "user_id": user["user_id"],
            "email": user["email"],
            "first_name": user["first_name"],
            "last_name": user["last_name"],
            "role": user["role"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/users/admin/login")
async def admin_login(login_data: LoginRequest):
    try:
        conn = connect_user_db()
        
        # Get admin user with role information
        query = """
            SELECT u.user_id, u.first_name, u.last_name, u.email, u.password, ur.role
            FROM users u
            INNER JOIN user_roles ur ON u.user_id = ur.user_id
            WHERE u.email = %s AND ur.role = 'admin'
        """
        result = query_db(conn, query, (login_data.email,))
        close_db(conn)
        
        if not result:
            raise HTTPException(status_code=401, detail="Invalid admin credentials")
        
        user = result[0]
        
        # Verify password
        if not verify_password(login_data.password, user["password"]):
            raise HTTPException(status_code=401, detail="Invalid admin credentials")
        
        # Return user data
        return {
            "user_id": user["user_id"],
            "email": user["email"],
            "first_name": user["first_name"],
            "last_name": user["last_name"],
            "role": user["role"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/users/refresh-tokens")
async def store_refresh_token(token_data: dict):
    try:
        conn = connect_user_db()
        
        # Insert refresh token
        query = """
            INSERT INTO refresh_tokens (user_id, token_hash, expires_at)
            VALUES (%s, %s, %s)
        """
        values = (
            token_data["user_id"],
            token_data["token_hash"],
            token_data["expires_at"]
        )
        execute_db(conn, query, values)
        close_db(conn)
        
        return {"message": "Refresh token stored successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/users/verify-refresh-token")
async def verify_refresh_token(token_request: RefreshTokenRequest):
    try:
        conn = connect_user_db()
        
        # Check if refresh token exists and is not expired
        query = """
            SELECT token_id, user_id, expires_at
            FROM refresh_tokens
            WHERE token_hash = %s AND expires_at > NOW()
        """
        result = query_db(conn, query, (token_request.token_hash,))
        close_db(conn)
        
        if not result:
            raise HTTPException(status_code=401, detail="Invalid or expired refresh token")
        
        return {"message": "Refresh token is valid", "user_id": result[0]["user_id"]}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/users/refresh-tokens")
async def update_refresh_token(update_data: RefreshTokenUpdateRequest):
    try:
        conn = connect_user_db()
        
        # Update refresh token (replace old with new)
        query = """
            UPDATE refresh_tokens
            SET token_hash = %s, expires_at = %s
            WHERE token_hash = %s
        """
        values = (
            update_data.new_token_hash,
            update_data.expires_at,
            update_data.old_token_hash
        )
        execute_db(conn, query, values)
        close_db(conn)
        
        return {"message": "Refresh token updated successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/users/refresh-tokens")
async def delete_refresh_token(token_data: dict):
    try:
        conn = connect_user_db()
        
        # Delete refresh token
        query = "DELETE FROM refresh_tokens WHERE token_hash = %s"
        execute_db(conn, query, (token_data["token_hash"],))
        close_db(conn)
        
        return {"message": "Refresh token deleted successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    
# ========== USER REGISTRATION ROUTES ==========
@app.post("/users/register")
async def register_user(user_data: UserCreateRequest):
    try:
        conn = connect_user_db()
        
        # Check if email already exists
        check_query = "SELECT user_id FROM users WHERE email = %s"
        existing_user = query_db(conn, check_query, (user_data.email,))
        
        if existing_user:
            raise HTTPException(status_code=409, detail="Email already registered")
        
        # Hash password
        hashed_password = hash_password(user_data.password)
        
        # Insert user into the users table
        user_query = """
            INSERT INTO users (first_name, last_name, email, password)
            VALUES (%s, %s, %s, %s)
        """
        user_values = (user_data.first_name, user_data.last_name, user_data.email, hashed_password)
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
        role_values = (user_id, user_data.role)
        execute_db(conn, role_query, role_values)
        
        close_db(conn)
        
        return {
            "message": "User registered successfully",
            "user_id": user_id,
            "email": user_data.email,
            "first_name": user_data.first_name,
            "last_name": user_data.last_name,
            "role": user_data.role
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ========== USER PROFILE ROUTES ==========
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
        query = """
            SELECT u.*, ur.role
            FROM users u
            LEFT JOIN user_roles ur ON u.user_id = ur.user_id
            WHERE u.user_id = %s
        """
        result = query_db(conn, query, (user_id,))
        close_db(conn)
        
        if not result:
            raise HTTPException(status_code=404, detail="User not found")
            
        return result[0]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
# POST /users
@app.post("/admin/users")
async def create_user(user: UserCreateRequest):
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
        role_values = (user_id, user.role)
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

# DELETE /users
@app.delete("/admin/users/{user_id}")
async def delete_user(user_id: int):
    try:   
        conn = connect_user_db()
        
        # Check if user exists
        check_query = "SELECT user_id FROM users WHERE user_id = %s"
        user_exists = query_db(conn, check_query, (user_id,))
        if not user_exists:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Check for existing orders
        orders_query = "SELECT COUNT(*) FROM orders WHERE user_id = %s"
        order_count = query_db(conn, orders_query, (user_id,))
        if order_count and order_count[0][0] > 0:
            raise HTTPException(status_code=400, detail="Cannot delete user with existing orders")
        
        # Check for cart items
        cart_query = "SELECT COUNT(*) FROM shopping_cart WHERE user_id = %s"
        cart_count = query_db(conn, cart_query, (user_id,))
        if cart_count and cart_count[0][0] > 0:
            # Delete cart items first
            delete_cart_query = "DELETE FROM shopping_cart WHERE user_id = %s"
            execute_db(conn, delete_cart_query, (user_id,))

        # Delete refresh tokens
        token_query = "DELETE FROM refresh_tokens WHERE user_id = %s"
        execute_db(conn, token_query, (user_id,))

        # Delete user role first
        role_query = "DELETE FROM user_roles WHERE user_id = %s"
        execute_db(conn, role_query, (user_id,))

        # Delete user
        user_query = "DELETE FROM users WHERE user_id = %s"
        execute_db(conn, user_query, (user_id,))

        close_db(conn)

        return {"message": "User has been deleted"}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# PUT /users role
@app.put("/admin/users/{user_id}/role")
async def update_user_role(user_id: int, request: Request):
    try:   
        data = await request.json()
        role = data.get("role")
        if not role:
            raise HTTPException(status_code=400, detail="Role is required")
        
        if role not in ["customer", "admin"]:
            raise HTTPException(status_code=400, detail="Role must be 'customer' or 'admin'")

        conn = connect_user_db()
        
        # Check if user exists
        check_query = "SELECT user_id FROM users WHERE user_id = %s"
        user_exists = query_db(conn, check_query, (user_id,))
        if not user_exists:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Check if user role exists, if not create it
        role_exists_query = "SELECT role FROM user_roles WHERE user_id = %s"
        existing_role = query_db(conn, role_exists_query, (user_id,))
        
        if existing_role:
            # Update existing role
            query = "UPDATE user_roles SET role = %s WHERE user_id = %s"
            execute_db(conn, query, (role, user_id))
        else:
            # Create new role entry
            query = "INSERT INTO user_roles (user_id, role) VALUES (%s, %s)"
            execute_db(conn, query, (user_id, role))
        
        close_db(conn)

        return {"message": f"User role updated to '{role}' successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
  

# ========== SHOPPING CART ==========
# GET /users/{user_id}/cart
@app.get("/users/{user_id}/cart")
async def get_user_cart(user_id: int):
    try:
        conn = connect_user_db()

        # Check if user exists
        check_query = "SELECT user_id FROM users WHERE user_id = %s"
        user_exists = query_db(conn, check_query, (user_id,))
        if not user_exists:
            raise HTTPException(status_code=404, detail="User not found")

        # Retrieve cart items
        cart_query = """
            SELECT product_id, quantity
            FROM shopping_cart
            WHERE user_id = %s
        """
        cart_items = query_db(conn, cart_query, (user_id,))
        close_db(conn)

        return cart_items

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/users/{user_id}/cart/{product_id}")
async def add_to_cart(user_id: int, product_id: int, quantity: int = Query(1)):
    try:
        if quantity <= 0:
            raise HTTPException(status_code=400, detail="Quantity must be greater than 0")

        conn = connect_user_db()

        # Check if user exists
        user_check = "SELECT user_id FROM users WHERE user_id = %s"
        if not query_db(conn, user_check, (user_id,)):
            close_db(conn)
            raise HTTPException(status_code=404, detail="User not found")

        # Check if item already exists in cart
        existing_query = """
            SELECT quantity FROM shopping_cart WHERE user_id = %s AND product_id = %s
        """
        existing_item = query_db(conn, existing_query, (user_id, product_id))

        if existing_item:
            # Update quantity
            new_quantity = existing_item[0]["quantity"] + quantity
            update_query = """
                UPDATE shopping_cart
                SET quantity = %s
                WHERE user_id = %s AND product_id = %s
            """
            execute_db(conn, update_query, (new_quantity, user_id, product_id))
        else:
            # Insert new item
            insert_query = """
                INSERT INTO shopping_cart (user_id, product_id, quantity)
                VALUES (%s, %s, %s)
            """
            execute_db(conn, insert_query, (user_id, product_id, quantity))

        close_db(conn)
        return {"message": "Item added to cart"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

