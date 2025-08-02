import fastapi
import requests
from fastapi import HTTPException, Query, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
from pydantic import BaseModel
from shared.email_utils import send_email, create_order_confirmation_email_content, create_password_reset_email_content

app = fastapi.FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=False,  # Set to False when using allow_origins=["*"]
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Data models for request/response
class LoginRequest(BaseModel):
    email: str
    password: str

class UserRegistration(BaseModel):
    first_name: str
    last_name: str
    email: str
    password: str

class RefreshRequest(BaseModel):
    refresh_token: str

class PasswordResetRequest(BaseModel):
    email: str

class PasswordResetConfirmRequest(BaseModel):
    reset_token: str
    new_password: str

# Authentication dependency
async def get_current_user(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")
    
    try:
        # Call IDP to verify token
        response = requests.post("http://idp-service:8080/verify", 
                               headers={"Authorization": authorization})
        
        if response.status_code == 200:
            return response.json()
        else:
            raise HTTPException(status_code=401, detail="Invalid or expired token")
            
    except requests.RequestException:
        raise HTTPException(status_code=503, detail="Authentication service unavailable")

# Health check
@app.get("/")
def read_root():
    return {"message": "User BFF is running"}

# Handle OPTIONS requests for CORS preflight
@app.options("/{full_path:path}")
async def options_handler(full_path: str):
    return {}

# Add explicit OPTIONS handlers for specific routes
@app.options("/auth/login")
async def options_login():
    return {}

@app.options("/auth/register")
async def options_register():
    return {}

@app.options("/auth/request-password-reset")
async def options_request_password_reset():
    return {}

@app.options("/auth/confirm-password-reset")
async def options_confirm_password_reset():
    return {}

@app.options("/cart")
async def options_cart():
    return {}

@app.options("/cart/add")
async def options_cart_add():
    return {}

@app.options("/cart/remove")
async def options_cart_remove():
    return {}

@app.options("/orders")
async def options_orders():
    return {}

@app.options("/inventory")
async def options_inventory():
    return {}

# ========== AUTHENTICATION ROUTES ==========
@app.post("/auth/login")
def login(login_data: LoginRequest):
    try:
        # Call IDP service for authentication
        response = requests.post("http://idp-service:8080/login", json=login_data.dict())
        return response.json()
    except requests.RequestException:
        raise HTTPException(status_code=503, detail="Authentication service unavailable")

@app.post("/auth/refresh")
def refresh_token(refresh_data: RefreshRequest):
    try:
        # Call IDP service for token refresh
        response = requests.post("http://idp-service:8080/refresh", json=refresh_data.dict())
        return response.json()
    except requests.RequestException:
        raise HTTPException(status_code=503, detail="Authentication service unavailable")

@app.post("/auth/verify")
def verify_token(authorization: str = Header(None)):
    try:
        # Call IDP service to verify token
        response = requests.post("http://idp-service:8080/verify", 
                               headers={"Authorization": authorization})
        return response.json()
    except requests.RequestException:
        raise HTTPException(status_code=503, detail="Authentication service unavailable")

@app.post("/auth/logout")
def logout(authorization: str = Header(None)):
    try:
        response = requests.post("http://idp-service:8080/logout", 
                               headers={"Authorization": authorization})
        return response.json()
    except requests.RequestException:
        raise HTTPException(status_code=503, detail="Authentication service unavailable")

@app.post("/auth/register")
def register(user_data: UserRegistration):
    try:
        # Call user service to create account
        response = requests.post("http://user-service:8080/users/register", json=user_data.dict())
        return response.json()
    except requests.RequestException:
        raise HTTPException(status_code=503, detail="User service unavailable")

@app.post("/auth/request-password-reset")
def request_password_reset(reset_request: PasswordResetRequest):
    try:
        # Call user service to request password reset
        response = requests.post("http://user-service:8080/users/request-password-reset", json=reset_request.dict())
        reset_result = response.json()
        
        if response.status_code != 200:
            return reset_result
        
        # If password reset was successful, we need to send the email
        # The user service should return the user_id and reset_token
        user_id = reset_result.get("user_id")
        reset_token = reset_result.get("reset_token")
        
        if user_id and reset_token:
            # Get user info for email
            user_response = requests.get(f"http://user-service:8080/users/{user_id}")
            if user_response.status_code == 200:
                user_info = user_response.json()
                
                # Send password reset email
                try:
                    subject, body, html_body = create_password_reset_email_content(user_info, reset_token)
                    email_sent = send_email(user_info["email"], subject, body, html_body)
                    if email_sent:
                        print(f"Password reset email sent to {user_info['email']}")
                    else:
                        print(f"Failed to send password reset email to {user_info['email']}")
                except Exception as e:
                    print(f"Error sending password reset email: {e}")
        
        return reset_result
        
    except requests.RequestException:
        raise HTTPException(status_code=503, detail="User service unavailable")

@app.post("/auth/confirm-password-reset")
def confirm_password_reset(confirm_request: PasswordResetConfirmRequest):
    try:
        # Call user service to confirm password reset
        response = requests.post("http://user-service:8080/users/confirm-password-reset", json=confirm_request.dict())
        return response.json()
    except requests.RequestException:
        raise HTTPException(status_code=503, detail="User service unavailable")

# ========== USER PROFILE ROUTES ==========
@app.get("/profile")
def get_user_profile(current_user: dict = Depends(get_current_user)):
    try:
        user_id = current_user["sub"]
        response = requests.get(f"http://user-service:8080/users/{user_id}")
        return response.json()
    except requests.RequestException:
        raise HTTPException(status_code=503, detail="User service unavailable")

@app.put("/profile")
def update_user_profile(profile_data: dict, current_user: dict = Depends(get_current_user)):
    try:
        user_id = current_user["sub"]
        response = requests.put(f"http://user-service:8080/users/{user_id}", json=profile_data)
        return response.json()
    except requests.RequestException:
        raise HTTPException(status_code=503, detail="User service unavailable")

# ========== INVENTORY BROWSING ROUTES ==========
@app.get("/inventory")
def get_inventory(
    brand: Optional[str] = Query(None, description="Filter by brand name"),
    min_price: Optional[float] = Query(None, description="Minimum price filter"),
    max_price: Optional[float] = Query(None, description="Maximum price filter"),
    discount_only: Optional[bool] = Query(False, description="Show only discounted items"),
    search: Optional[str] = Query(None, description="Search in product name or description"),
    sort_by: Optional[str] = Query("name", description="Sort by: name, price, brand, discount"),
    sort_order: Optional[str] = Query("asc", description="Sort order: asc or desc"),
    limit: Optional[int] = Query(50, description="Number of results to return"),
    offset: Optional[int] = Query(0, description="Number of results to skip")
):
    try:
        # Build query parameters for inventory service
        params = {
            "brand": brand,
            "min_price": min_price,
            "max_price": max_price,
            "discount_only": discount_only,
            "search": search,
            "sort_by": sort_by,
            "sort_order": sort_order,
            "limit": limit,
            "offset": offset
        }
        
        # Remove None values
        params = {k: v for k, v in params.items() if v is not None}
        
        response = requests.get("http://inventory-service:8080/products", params=params)
        return response.json()
    except requests.RequestException:
        raise HTTPException(status_code=503, detail="Inventory service unavailable")

@app.get("/inventory/brands")
def get_brands():
    try:
        response = requests.get("http://inventory-service:8080/brands")
        return response.json()
    except requests.RequestException:
        raise HTTPException(status_code=503, detail="Inventory service unavailable")

@app.get("/inventory/filters")
def get_filter_options():
    try:
        # Get brands
        brands_response = requests.get("http://inventory-service:8080/brands")
        
        # Get price ranges and other filter data
        stats_response = requests.get("http://inventory-service:8080/products/stats")
        
        return {
            "brands": brands_response.json() if brands_response.status_code == 200 else [],
            "price_range": stats_response.json() if stats_response.status_code == 200 else {},
            "sort_options": [
                {"value": "name", "label": "Product Name"},
                {"value": "price", "label": "Price"},
                {"value": "description", "label": "Description"},
                {"value": "brand", "label": "Brand"},
                {"value": "discount", "label": "Discount %"},
                {"value": "date_added", "label": "Date Added"}
            ],
            "sort_orders": [
                {"value": "asc", "label": "Ascending"},
                {"value": "desc", "label": "Descending"}
            ]
        }
    except requests.RequestException:
        raise HTTPException(status_code=503, detail="Inventory service unavailable")

@app.get("/inventory/{product_id}")
def get_product_details(product_id: int):
    try:
        response = requests.get(f"http://inventory-service:8080/products/{product_id}")
        return response.json()
    except requests.RequestException:
        raise HTTPException(status_code=503, detail="Inventory service unavailable")

# ========== SHOPPING CART ROUTES ==========
@app.get("/cart")
def get_cart(current_user: dict = Depends(get_current_user)):
    try:
        user_id = current_user["sub"]
        # Get cart from user service
        cart_response = requests.get(f"http://user-service:8080/users/{user_id}/cart")
        if cart_response.status_code != 200:
            return cart_response.json()
        
        cart_items = cart_response.json()
        
        for item in cart_items if isinstance(cart_items, list) else [cart_items]:
            if "product_id" in item:
                try:
                    # Get product details from inventory service
                    product_response = requests.get(f"http://inventory-service:8080/products/{item['product_id']}")
                    if product_response.status_code == 200:
                        product_data = product_response.json()
                        # Merge product details into cart item
                        item.update({
                            "product_name": product_data.get("product_name"),
                            "product_code": product_data.get("product_code"),
                            "description": product_data.get("description"),
                            "brand_name": product_data.get("brand_name"),
                            "market_price": product_data.get("market_price"),
                            "discount_percent": product_data.get("discount_percent", 0),
                            "current_price": product_data.get("market_price", 0) * (1 - product_data.get("discount_percent", 0) / 100)
                        })
                except requests.RequestException:
                    pass
        
        return cart_items
    except requests.RequestException:
        raise HTTPException(status_code=503, detail="User service unavailable")

@app.post("/cart/add")
def add_to_cart(product_id: int = Query(...), quantity: int = Query(1), current_user: dict = Depends(get_current_user)):
    try:
        user_id = current_user["sub"]
        response = requests.post(f"http://user-service:8080/users/{user_id}/cart/{product_id}?quantity={quantity}")
        return response.json()
    except requests.RequestException:
        raise HTTPException(status_code=503, detail="User service unavailable")

@app.delete("/cart/remove")
def remove_from_cart(product_id: int = Query(...), current_user: dict = Depends(get_current_user)):
    try:
        user_id = current_user["sub"]
        response = requests.delete(f"http://user-service:8080/users/{user_id}/cart/{product_id}")
        return response.json()
    except requests.RequestException:
        raise HTTPException(status_code=503, detail="User service unavailable")

# ========== ORDER ROUTES ==========
@app.get("/orders")
def get_user_orders(current_user: dict = Depends(get_current_user)):
    try:
        user_id = current_user["sub"]
        # Get orders from user service
        orders_response = requests.get(f"http://user-service:8080/users/{user_id}/orders")
        if orders_response.status_code != 200:
            return orders_response.json()
        
        orders = orders_response.json()
        
        for order in orders if isinstance(orders, list) else [orders]:
            if "items" in order:
                for item in order["items"]:
                    if "product_id" in item:
                        try:
                            # Get product details from inventory service
                            product_response = requests.get(f"http://inventory-service:8080/products/{item['product_id']}")
                            if product_response.status_code == 200:
                                product_data = product_response.json()
                                # Merge product details into order item
                                item.update({
                                    "product_name": product_data.get("product_name"),
                                    "product_code": product_data.get("product_code"),
                                    "description": product_data.get("description"),
                                    "brand_name": product_data.get("brand_name"),
                                    "market_price": product_data.get("market_price")
                                })
                        except requests.RequestException:
                            pass
        
        return orders
    except requests.RequestException:
        raise HTTPException(status_code=503, detail="User service unavailable")

@app.get("/orders/{order_id}")
def get_order_details(order_id: int, current_user: dict = Depends(get_current_user)):
    try:
        user_id = current_user["sub"]
        # Get order from user service
        order_response = requests.get(f"http://user-service:8080/users/{user_id}/orders/{order_id}")
        if order_response.status_code != 200:
            return order_response.json()
        
        order = order_response.json()
        
        if "items" in order:
            for item in order["items"]:
                if "product_id" in item:
                    try:
                        # Get product details from inventory service
                        product_response = requests.get(f"http://inventory-service:8080/products/{item['product_id']}")
                        if product_response.status_code == 200:
                            product_data = product_response.json()
                            # Merge product details into order item
                            item.update({
                                "product_name": product_data.get("product_name"),
                                "product_code": product_data.get("product_code"),
                                "description": product_data.get("description"),
                                "brand_name": product_data.get("brand_name"),
                                "market_price": product_data.get("market_price")
                            })
                    except requests.RequestException:
                        pass
        
        return order
    except requests.RequestException:
        raise HTTPException(status_code=503, detail="User service unavailable")

@app.post("/orders")
def create_order(order_data: dict = {}, current_user: dict = Depends(get_current_user)):
    try:
        user_id = current_user["sub"]
        
        # Create order in user service
        response = requests.post(f"http://user-service:8080/users/{user_id}/orders", json=order_data)
        order_result = response.json()
        
        if response.status_code != 200:
            return order_result
        
        # Get order details for email
        order_id = order_result.get("order_id")
        if not order_id:
            return order_result
        
        # Get user info
        user_response = requests.get(f"http://user-service:8080/users/{user_id}")
        if user_response.status_code != 200:
            return order_result
        
        user_info = user_response.json()
        
        # Get order details with items
        order_response = requests.get(f"http://user-service:8080/users/{user_id}/orders/{order_id}")
        if order_response.status_code != 200:
            return order_result
        
        order_info = order_response.json()
        
        # Get product details for each item
        items_with_details = []
        total_amount = 0.0
        
        for item in order_info.get("items", []):
            try:
                product_response = requests.get(f"http://inventory-service:8080/products/{item['product_id']}")
                if product_response.status_code == 200:
                    product_info = product_response.json()
                    # Calculate final price with discount
                    final_price = product_info["market_price"] * (1 - product_info.get("discount_percent", 0) / 100)
                    item_total = final_price * item["quantity"]
                    total_amount += item_total
                    
                    items_with_details.append({
                        "product_name": product_info["product_name"],
                        "brand_name": product_info.get("brand_name", "Unknown"),
                        "quantity": item["quantity"],
                        "unit_price": final_price,
                        "item_total": item_total
                    })
            except requests.RequestException:
                pass
        
        # Send order confirmation email
        try:
            subject, body, html_body = create_order_confirmation_email_content(user_info, order_info, items_with_details, total_amount)
            email_sent = send_email(user_info["email"], subject, body, html_body)
            if email_sent:
                print(f"Order confirmation email sent for order {order_id}")
            else:
                print(f"Failed to send order confirmation email for order {order_id}")
        except Exception as e:
            print(f"Error sending order confirmation email: {e}")
        
        return order_result
        
    except requests.RequestException:
        raise HTTPException(status_code=503, detail="User service unavailable")