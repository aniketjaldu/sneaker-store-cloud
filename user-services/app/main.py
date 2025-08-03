import fastapi
import requests
import hashlib
import datetime
import secrets
from fastapi import HTTPException, Request, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from shared.models import connect_to_db, query_db, close_db, execute_db


app = fastapi.FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
)

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

class PasswordResetRequest(BaseModel):
    email: str

class PasswordResetConfirmRequest(BaseModel):
    reset_token: str
    new_password: str

# Helper function to connect to db
def connect_user_db():
    return connect_to_db("user-db", "root", "userpassword", "user_database", "3306")

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
        from datetime import datetime, timezone
        utc_now = datetime.now(timezone.utc)
        query = """
            SELECT token_id, user_id, expires_at
            FROM refresh_tokens
            WHERE token_hash = %s AND expires_at > %s
        """
        result = query_db(conn, query, (token_request.token_hash, utc_now))
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

# ========== PASSWORD RESET ROUTES ==========
@app.post("/users/request-password-reset")
async def request_password_reset(reset_request: PasswordResetRequest):
    try:
        conn = connect_user_db()
        
        # Check if user exists
        check_query = "SELECT user_id, first_name FROM users WHERE email = %s"
        user = query_db(conn, check_query, (reset_request.email,))
        
        if not user:
            # Don't reveal if email exists or not for security
            return {"message": "If the email exists, a password reset link has been sent"}
        
        user_data = user[0]
        
        # Generate reset token
        reset_token = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(reset_token.encode()).hexdigest()
        
        # Store reset token with expiration (1 hour)
        expires_at = datetime.datetime.utcnow() + datetime.timedelta(hours=1)
        
        # Delete any existing reset tokens for this user
        delete_query = "DELETE FROM password_reset_tokens WHERE user_id = %s"
        execute_db(conn, delete_query, (user_data["user_id"],))
        
        # Insert new reset token
        insert_query = """
            INSERT INTO password_reset_tokens (user_id, token_hash, expires_at)
            VALUES (%s, %s, %s)
        """
        execute_db(conn, insert_query, (user_data["user_id"], token_hash, expires_at))
        
        close_db(conn)
        
        # Return user_id and reset_token for BFF to handle email sending
        return {
            "message": "Password reset link has been sent to your email",
            "user_id": user_data["user_id"],
            "reset_token": reset_token
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/users/confirm-password-reset")
async def confirm_password_reset(confirm_request: PasswordResetConfirmRequest):
    try:
        conn = connect_user_db()
        
        # Hash the provided token
        token_hash = hashlib.sha256(confirm_request.reset_token.encode()).hexdigest()
        
        # Check if reset token exists and is not expired
        from datetime import datetime, timezone
        utc_now = datetime.now(timezone.utc)
        check_query = """
            SELECT user_id FROM password_reset_tokens
            WHERE token_hash = %s AND expires_at > %s
        """
        result = query_db(conn, check_query, (token_hash, utc_now))
        
        if not result:
            raise HTTPException(status_code=400, detail="Invalid or expired reset token")
        
        user_id = result[0]["user_id"]
        
        # Hash new password
        hashed_password = hash_password(confirm_request.new_password)
        
        # Update user password
        update_query = "UPDATE users SET password = %s WHERE user_id = %s"
        execute_db(conn, update_query, (hashed_password, user_id))
        
        # Delete the used reset token
        delete_query = "DELETE FROM password_reset_tokens WHERE token_hash = %s"
        execute_db(conn, delete_query, (token_hash,))
        
        close_db(conn)
        
        return {"message": "Password has been reset successfully"}
        
    except HTTPException:
        raise
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
        
        # Get user information
        user_query = "SELECT * FROM users WHERE user_id = %s"
        user_result = query_db(conn, user_query, (user_id,))
        
        if not user_result:
            close_db(conn)
            raise HTTPException(status_code=404, detail="User not found")
        
        user = user_result[0]
        
        # Get shipping address if exists
        if user.get("shipping_address_id"):
            shipping_query = "SELECT * FROM addresses WHERE address_id = %s"
            shipping_result = query_db(conn, shipping_query, (user["shipping_address_id"],))
            if shipping_result:
                user["shipping_address"] = shipping_result[0]
        
        # Get billing address if exists
        if user.get("billing_address_id"):
            billing_query = "SELECT * FROM addresses WHERE address_id = %s"
            billing_result = query_db(conn, billing_query, (user["billing_address_id"],))
            if billing_result:
                user["billing_address"] = billing_result[0]
        
        close_db(conn)
        return user
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# PUT /profile
@app.put("/users/{user_id}")
async def update_user_profile(user_id: int, request: Request):
    try:
        profile_data = await request.json()
        if not profile_data:
            raise HTTPException(status_code=400, detail="No profile data provided")
        
        conn = connect_user_db()
        
        # Handle user profile updates
        user_updates = {}
        address_updates = {}
        
        for key, value in profile_data.items():
            if key in ["first_name", "last_name", "email"]:
                user_updates[key] = value
            elif key == "phone":
                address_updates["phone"] = value
            elif key == "address_line1":
                address_updates["line1"] = value
            elif key == "address_line2":
                address_updates["line2"] = value
            elif key == "address_city":
                address_updates["city"] = value
            elif key == "address_state":
                address_updates["state"] = value
            elif key == "address_zip_code":
                address_updates["zip_code"] = value
        
        # Update user information
        if user_updates:
            set_clause = ", ".join(f"{key} = %s" for key in user_updates.keys())
            values = list(user_updates.values())
            values.append(user_id)
            user_query = f"UPDATE users SET {set_clause} WHERE user_id = %s"
            execute_db(conn, user_query, values)
        
        # Handle address updates
        if address_updates:
            # Get current user to see if they have addresses
            user_query = "SELECT shipping_address_id, billing_address_id FROM users WHERE user_id = %s"
            user_result = query_db(conn, user_query, (user_id,))
            
            if user_result:
                user = user_result[0]
                shipping_address_id = user.get("shipping_address_id")
                billing_address_id = user.get("billing_address_id")
                
                # Update shipping address (use shipping as primary address for now)
                if shipping_address_id:
                    # Handle empty line2 properly
                    if "line2" in address_updates and address_updates["line2"] == "":
                        address_updates["line2"] = None
                    
                    set_clause = ", ".join(f"{key} = %s" for key in address_updates.keys())
                    values = list(address_updates.values())
                    values.append(shipping_address_id)
                    address_query = f"UPDATE addresses SET {set_clause} WHERE address_id = %s"
                    execute_db(conn, address_query, values)
                else:
                    # Create new shipping address
                    address_fields = ["line1", "line2", "city", "state", "zip_code", "phone"]
                    address_values = [address_updates.get(field, "") for field in address_fields]
                    
                    # Handle empty line2 properly
                    if address_values[1] == "":
                        address_values[1] = None
                    
                    insert_query = """
                        INSERT INTO addresses (line1, line2, city, state, zip_code, phone)
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """
                    cursor = conn.cursor()
                    cursor.execute(insert_query, address_values)
                    new_address_id = cursor.lastrowid
                    
                    # Update user to reference new address
                    update_query = "UPDATE users SET shipping_address_id = %s WHERE user_id = %s"
                    execute_db(conn, update_query, (new_address_id, user_id))
                    cursor.close()
        
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
        if order_count and order_count[0]["COUNT(*)"] > 0:
            raise HTTPException(status_code=400, detail="Cannot delete user with existing orders")
        
        # Check for cart items
        cart_query = "SELECT COUNT(*) FROM shopping_cart WHERE user_id = %s"
        cart_count = query_db(conn, cart_query, (user_id,))
        if cart_count and cart_count[0]["COUNT(*)"] > 0:
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

# ========== ADMIN ORDER ROUTES ==========
@app.get("/admin/orders")
async def get_all_orders():
    try:
        conn = connect_user_db()
        
        # Get all orders with user information
        query = """
            SELECT o.*, u.first_name, u.last_name, u.email
            FROM orders o
            JOIN users u ON o.user_id = u.user_id
            ORDER BY o.order_date DESC
        """
        orders = query_db(conn, query)
        
        # For each order, get order items
        for order in orders:
            items_query = """
                SELECT product_id, quantity, unit_price, total_price
                FROM order_items
                WHERE order_id = %s
            """
            items = query_db(conn, items_query, (order["order_id"],))
            order["items"] = items
        
        close_db(conn)
        return orders
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/admin/orders/{order_id}")
async def get_admin_order_details(order_id: int):
    try:
        conn = connect_user_db()
        
        # Get the order with user information
        order_query = """
            SELECT o.*, u.first_name, u.last_name, u.email
            FROM orders o
            JOIN users u ON o.user_id = u.user_id
            WHERE o.order_id = %s
        """
        order_result = query_db(conn, order_query, (order_id,))
        if not order_result:
            raise HTTPException(status_code=404, detail="Order not found")
        
        order = order_result[0]
        
        # Get order items
        items_query = """
            SELECT product_id, quantity, unit_price, total_price
            FROM order_items
            WHERE order_id = %s
        """
        items = query_db(conn, items_query, (order_id,))
        order["items"] = items
        
        close_db(conn)
        return order
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ========== ORDER MANAGEMENT ==========
@app.put("/admin/orders/{order_id}/status")
async def update_admin_order_status(order_id: int, request: Request):
    try:
        data = await request.json()
        new_status = data.get("status")
        
        if not new_status:
            raise HTTPException(status_code=400, detail="Status is required")
        
        conn = connect_user_db()
        
        # Get current order status
        current_status_query = "SELECT order_status FROM orders WHERE order_id = %s"
        current_result = query_db(conn, current_status_query, (order_id,))
        if not current_result:
            close_db(conn)
            raise HTTPException(status_code=404, detail="Order not found")
        
        current_status = current_result[0]["order_status"]
        
        # Update order status
        update_query = "UPDATE orders SET order_status = %s WHERE order_id = %s"
        execute_db(conn, update_query, (new_status, order_id))
        
        # Get order items for stock management
        items_query = "SELECT product_id, quantity FROM order_items WHERE order_id = %s"
        order_items = query_db(conn, items_query, (order_id,))
        
        close_db(conn)
        return {"message": f"Order status updated to '{new_status}' successfully"}
        
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

# Remove a specific product from a user's cart
@app.delete("/users/{user_id}/cart/{product_id}")
async def remove_from_cart(user_id: int, product_id: int):
    try:
        conn = connect_user_db()

        # Check if item exists
        check_query = """
            SELECT * FROM shopping_cart
            WHERE user_id = %s AND product_id = %s
        """
        item = query_db(conn, check_query, (user_id, product_id))

        if not item:
            close_db(conn)
            raise HTTPException(status_code=404, detail="Item not found in cart")

        # Delete the item
        delete_query = """
            DELETE FROM shopping_cart
            WHERE user_id = %s AND product_id = %s
        """
        execute_db(conn, delete_query, (user_id, product_id))

        close_db(conn)
        return {"message": "Item removed from cart"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/users/{user_id}/orders")
async def get_user_orders(user_id: int):
    try:
        conn = connect_user_db()

        # Check if user exists
        check_query = "SELECT user_id FROM users WHERE user_id = %s"
        user_exists = query_db(conn, check_query, (user_id,))
        if not user_exists:
            raise HTTPException(status_code=404, detail="User not found")

        # Get all orders for the user
        orders_query = "SELECT * FROM orders WHERE user_id = %s"
        orders = query_db(conn, orders_query, (user_id,))
        
        # For each order, get order items
        for order in orders:
            items_query = """
                SELECT product_id, quantity, unit_price, total_price
                FROM order_items
                WHERE order_id = %s
            """
            items = query_db(conn, items_query, (order["order_id"],))
            order["items"] = items

        close_db(conn)

        return orders

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/users/{user_id}/orders/{order_id}")
async def get_order_details(user_id: int, order_id: int):
    try:
        conn = connect_user_db()

        # Check if user exists
        check_user_query = "SELECT user_id FROM users WHERE user_id = %s"
        user_exists = query_db(conn, check_user_query, (user_id,))
        if not user_exists:
            raise HTTPException(status_code=404, detail="User not found")

        # Get the order
        order_query = "SELECT * FROM orders WHERE order_id = %s AND user_id = %s"
        order_result = query_db(conn, order_query, (order_id, user_id))
        if not order_result:
            raise HTTPException(status_code=404, detail="Order not found")

        order = order_result[0]

        # Get order items
        items_query = """
            SELECT product_id, quantity, unit_price, total_price
            FROM order_items
            WHERE order_id = %s
        """
        items = query_db(conn, items_query, (order_id,))
        order["items"] = items

        close_db(conn)
        return order

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Create order from cart (checkout)
@app.post("/users/{user_id}/orders")
async def create_order(user_id: int, request: Request):
    try:
        conn = connect_user_db()

        # Validate user
        check_query = "SELECT user_id FROM users WHERE user_id = %s"
        if not query_db(conn, check_query, (user_id,)):
            raise HTTPException(status_code=404, detail="User not found")

        # Fetch cart items
        cart_query = "SELECT product_id, quantity FROM shopping_cart WHERE user_id = %s"
        cart_items = query_db(conn, cart_query, (user_id,))
        if not cart_items:
            raise HTTPException(status_code=400, detail="Cart is empty")

        # Get user email
        user_query = "SELECT email FROM users WHERE user_id = %s"
        user_result = query_db(conn, user_query, (user_id,))
        if not user_result:
            raise HTTPException(status_code=404, detail="User not found")
        
        user_email = user_result[0]["email"]
        
        # Get order data from request (provided by BFF)
        order_data = await request.json()
        subtotal_amount = order_data.get("subtotal_amount", 0.0)
        tax_amount = order_data.get("tax_amount", 0.0)
        total_amount = order_data.get("total_amount", 0.0)
        order_items_data = order_data.get("order_items", [])
        
        # If no order data provided, use placeholder values
        if not order_items_data:
            for item in cart_items:
                order_items_data.append({
                    "product_id": item["product_id"],
                    "quantity": item["quantity"],
                    "unit_price": 0.0,
                    "total_price": 0.0
                })
        
        # Create order with calculated amounts including tax
        # Use UTC time for order_date
        from datetime import datetime, timezone
        utc_now = datetime.now(timezone.utc)
        order_query = "INSERT INTO orders (user_id, order_date, email, subtotal_amount, tax_amount, total_amount) VALUES (%s, %s, %s, %s, %s, %s)"
        cursor = conn.cursor()
        cursor.execute(order_query, (user_id, utc_now, user_email, subtotal_amount, tax_amount, total_amount))
        order_id = cursor.lastrowid

        # Add order items with actual prices
        for item_data in order_items_data:
            item_query = """
                INSERT INTO order_items (order_id, product_id, quantity, unit_price, total_price)
                VALUES (%s, %s, %s, %s, %s)
            """
            execute_db(conn, item_query, (
                order_id, 
                item_data["product_id"], 
                item_data["quantity"], 
                item_data["unit_price"], 
                item_data["total_price"]
            ))

        # Clear cart
        clear_cart_query = "DELETE FROM shopping_cart WHERE user_id = %s"
        execute_db(conn, clear_cart_query, (user_id,))

        conn.commit()
        cursor.close()
        close_db(conn)

        return {"message": "Order placed successfully", "order_id": order_id}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ========== ANALYTICS ROUTES ==========
@app.get("/admin/analytics/users")
async def get_user_analytics():
    try:
        conn = connect_user_db()
        
        # Get total users
        total_users_query = "SELECT COUNT(*) as total_users FROM users"
        total_users_result = query_db(conn, total_users_query)
        total_users = total_users_result[0]["total_users"] if total_users_result else 0
        
        # Get users by role
        role_query = """
            SELECT role, COUNT(*) as count
            FROM users u
            INNER JOIN user_roles ur ON u.user_id = ur.user_id
            GROUP BY role
        """
        role_results = query_db(conn, role_query)
        
        # Calculate active users (users with orders in last 30 days)
        from datetime import datetime, timedelta
        thirty_days_ago = datetime.now() - timedelta(days=30)
        active_users_query = """
            SELECT COUNT(DISTINCT user_id) as active_users
            FROM orders
            WHERE order_date >= %s
        """
        active_users_result = query_db(conn, active_users_query, (thirty_days_ago,))
        active_users = active_users_result[0]["active_users"] if active_users_result else 0
        
        # Get new users today (approximate - using order_date as proxy)
        today = datetime.now().date()
        new_users_query = """
            SELECT COUNT(*) as new_users_today
            FROM users u
            WHERE EXISTS (
                SELECT 1 FROM orders o 
                WHERE o.user_id = u.user_id 
                AND DATE(o.order_date) = %s
            )
        """
        new_users_result = query_db(conn, new_users_query, (today,))
        new_users_today = new_users_result[0]["new_users_today"] if new_users_result else 0
        
        close_db(conn)
        
        return {
            "total_users": total_users,
            "active_users": active_users,
            "new_users_today": new_users_today,
            "users_by_role": {row["role"]: row["count"] for row in role_results}
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/admin/analytics/sales")
async def get_sales_analytics(
    date_from: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="End date (YYYY-MM-DD)")
):
    try:
        conn = connect_user_db()
        
        # Build date filter
        date_filter = ""
        params = []
        if date_from and date_to:
            date_filter = "WHERE order_date BETWEEN %s AND %s"
            params = [date_from, date_to]
        elif date_from:
            date_filter = "WHERE order_date >= %s"
            params = [date_from]
        elif date_to:
            date_filter = "WHERE order_date <= %s"
            params = [date_to]
        
        # Get total sales
        total_sales_query = f"""
            SELECT 
                SUM(total_amount) as total_sales,
                COUNT(*) as total_orders,
                AVG(total_amount) as avg_order_value
            FROM orders
            {date_filter}
        """
        sales_result = query_db(conn, total_sales_query, tuple(params))
        
        if sales_result and sales_result[0]["total_sales"]:
            total_sales = float(sales_result[0]["total_sales"])
            total_orders = sales_result[0]["total_orders"]
            avg_order_value = float(sales_result[0]["avg_order_value"])
        else:
            total_sales = 0.0
            total_orders = 0
            avg_order_value = 0.0
        
        # Get sales by status
        status_query = f"""
            SELECT 
                order_status,
                COUNT(*) as count,
                SUM(total_amount) as total
            FROM orders
            {date_filter}
            GROUP BY order_status
        """
        status_results = query_db(conn, status_query, tuple(params))
        
        # Get top customers
        top_customers_query = f"""
            SELECT 
                u.first_name,
                u.last_name,
                u.email,
                COUNT(o.order_id) as order_count,
                SUM(o.total_amount) as total_spent
            FROM orders o
            JOIN users u ON o.user_id = u.user_id
            {date_filter}
            GROUP BY o.user_id, u.first_name, u.last_name, u.email
            ORDER BY total_spent DESC
            LIMIT 5
        """
        top_customers = query_db(conn, top_customers_query, tuple(params))
        
        close_db(conn)
        
        return {
            "total_sales": total_sales,
            "total_orders": total_orders,
            "avg_order_value": avg_order_value,
            "sales_by_status": {row["order_status"]: {"count": row["count"], "total": float(row["total"])} for row in status_results},
            "top_customers": [
                {
                    "name": f"{customer['first_name']} {customer['last_name']}",
                    "email": customer["email"],
                    "order_count": customer["order_count"],
                    "total_spent": float(customer["total_spent"])
                }
                for customer in top_customers
            ]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))