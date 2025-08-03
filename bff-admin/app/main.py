import fastapi
import requests
from fastapi import HTTPException, Query, Header, Depends
from typing import Optional
from pydantic import BaseModel

app = fastapi.FastAPI()

# Data models for request/response
class AdminLoginRequest(BaseModel):
    email: str
    password: str

class UserCreateRequest(BaseModel):
    first_name: str
    last_name: str
    email: str
    password: str
    role: str = "customer"  # customer or admin

class ProductCreateRequest(BaseModel):
    brand_id: int
    product_name: str
    description: Optional[str] = None
    market_price: float
    discount_percent: float = 0.0
    quantity: int

class BrandCreateRequest(BaseModel):
    brand_name: str

class RefreshRequest(BaseModel):
    refresh_token: str

# Authentication dependency
async def get_current_admin(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")
    
    try:
        # Call IDP to verify token
        response = requests.post("http://idp-service:8080/verify", 
                               headers={"Authorization": authorization})
        
        if response.status_code == 200:
            user_data = response.json()
            # Verify admin role
            if user_data.get("role") != "admin":
                raise HTTPException(status_code=403, detail="Admin access required")
            return user_data
        else:
            raise HTTPException(status_code=401, detail="Invalid or expired token")
            
    except requests.RequestException:
        raise HTTPException(status_code=503, detail="Authentication service unavailable")

# Health check
@app.get("/")
def read_root():
    return {"message": "Admin BFF is running"}

# ========== ADMIN AUTHENTICATION ROUTES ==========
@app.post("/auth/login")
def admin_login(login_data: AdminLoginRequest):
    try:
        # Call IDP service for admin authentication
        response = requests.post("http://idp-service:8080/admin/login", json=login_data.dict())
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

@app.post("/auth/logout")
def admin_logout(authorization: str = Header(None)):
    try:
        response = requests.post("http://idp-service:8080/logout", 
                               headers={"Authorization": authorization})
        return response.json()
    except requests.RequestException:
        raise HTTPException(status_code=503, detail="Authentication service unavailable")

# ========== USER MANAGEMENT ROUTES ==========
@app.get("/users")
def get_all_users(
    role: Optional[str] = Query(None, description="Filter by role: customer or admin"),
    search: Optional[str] = Query(None, description="Search by name or email"),
    limit: Optional[int] = Query(50, description="Number of results to return"),
    offset: Optional[int] = Query(0, description="Number of results to skip"),
    current_admin: dict = Depends(get_current_admin)
):
    try:
        params = {
            "role": role,
            "search": search,
            "limit": limit,
            "offset": offset
        }
        params = {k: v for k, v in params.items() if v is not None}
        
        response = requests.get("http://user-service:8080/admin/users", params=params)
        return response.json()
    except requests.RequestException:
        raise HTTPException(status_code=503, detail="User service unavailable")

@app.get("/users/{user_id}")
def get_user_details(user_id: int, current_admin: dict = Depends(get_current_admin)):
    try:
        response = requests.get(f"http://user-service:8080/admin/users/{user_id}")
        return response.json()
    except requests.RequestException:
        raise HTTPException(status_code=503, detail="User service unavailable")

@app.post("/users")
def create_user(user_data: UserCreateRequest, current_admin: dict = Depends(get_current_admin)):
    try:
        response = requests.post("http://user-service:8080/admin/users", json=user_data.dict())
        return response.json()
    except requests.RequestException:
        raise HTTPException(status_code=503, detail="User service unavailable")

@app.put("/users/{user_id}")
def update_user(user_id: int, user_data: dict, current_admin: dict = Depends(get_current_admin)):
    try:
        response = requests.put(f"http://user-service:8080/admin/users/{user_id}", json=user_data)
        return response.json()
    except requests.RequestException:
        raise HTTPException(status_code=503, detail="User service unavailable")

@app.delete("/users/{user_id}")
def delete_user(user_id: int, current_admin: dict = Depends(get_current_admin)):
    try:
        response = requests.delete(f"http://user-service:8080/admin/users/{user_id}")
        return response.json()
    except requests.RequestException:
        raise HTTPException(status_code=503, detail="User service unavailable")

@app.put("/users/{user_id}/role")
def update_user_role(user_id: int, role: str = Query(..., description="New role: customer or admin"), current_admin: dict = Depends(get_current_admin)):
    try:
        response = requests.put(f"http://user-service:8080/admin/users/{user_id}/role", json={"role": role})
        return response.json()
    except requests.RequestException:
        raise HTTPException(status_code=503, detail="User service unavailable")

# ========== INVENTORY MANAGEMENT ROUTES ==========
@app.get("/inventory")
def get_all_inventory(
    brand: Optional[str] = Query(None, description="Filter by brand name"),
    min_price: Optional[float] = Query(None, description="Minimum price filter"),
    max_price: Optional[float] = Query(None, description="Maximum price filter"),
    search: Optional[str] = Query(None, description="Search in product name or description"),
    sort_by: Optional[str] = Query("name", description="Sort by: name, price, brand, discount, date_added"),
    sort_order: Optional[str] = Query("asc", description="Sort order: asc or desc"),
    limit: Optional[int] = Query(100, description="Number of results to return"),
    offset: Optional[int] = Query(0, description="Number of results to skip"),
    current_admin: dict = Depends(get_current_admin)
):
    try:
        params = {
            "brand": brand,
            "min_price": min_price,
            "max_price": max_price,
            "search": search,
            "sort_by": sort_by,
            "sort_order": sort_order,
            "limit": limit,
            "offset": offset
        }
        params = {k: v for k, v in params.items() if v is not None}
        
        response = requests.get("http://inventory-service:8080/admin/products", params=params)
        return response.json()
    except requests.RequestException:
        raise HTTPException(status_code=503, detail="Inventory service unavailable")

@app.get("/inventory/{product_id}")
def get_product_details(product_id: int, current_admin: dict = Depends(get_current_admin)):
    try:
        response = requests.get(f"http://inventory-service:8080/admin/products/{product_id}")
        return response.json()
    except requests.RequestException:
        raise HTTPException(status_code=503, detail="Inventory service unavailable")

@app.post("/inventory")
def create_product(product_data: ProductCreateRequest, current_admin: dict = Depends(get_current_admin)):
    try:
        response = requests.post("http://inventory-service:8080/admin/products", json=product_data.dict())
        return response.json()
    except requests.RequestException:
        raise HTTPException(status_code=503, detail="Inventory service unavailable")

@app.put("/inventory/{product_id}")
def update_product(product_id: int, product_data: dict, current_admin: dict = Depends(get_current_admin)):
    try:
        response = requests.put(f"http://inventory-service:8080/admin/products/{product_id}", json=product_data)
        return response.json()
    except requests.RequestException:
        raise HTTPException(status_code=503, detail="Inventory service unavailable")

@app.delete("/inventory/{product_id}")
def delete_product(product_id: int, current_admin: dict = Depends(get_current_admin)):
    try:
        response = requests.delete(f"http://inventory-service:8080/admin/products/{product_id}")
        return response.json()
    except requests.RequestException:
        raise HTTPException(status_code=503, detail="Inventory service unavailable")

# ========== BRAND MANAGEMENT ROUTES ==========
@app.get("/brands")
def get_all_brands(current_admin: dict = Depends(get_current_admin)):
    try:
        response = requests.get("http://inventory-service:8080/admin/brands")
        return response.json()
    except requests.RequestException:
        raise HTTPException(status_code=503, detail="Inventory service unavailable")

@app.post("/brands")
def create_brand(brand_data: BrandCreateRequest, current_admin: dict = Depends(get_current_admin)):
    try:
        response = requests.post("http://inventory-service:8080/admin/brands", json=brand_data.dict())
        return response.json()
    except requests.RequestException:
        raise HTTPException(status_code=503, detail="Inventory service unavailable")

@app.put("/brands/{brand_id}")
def update_brand(brand_id: int, brand_data: dict, current_admin: dict = Depends(get_current_admin)):
    try:
        response = requests.put(f"http://inventory-service:8080/admin/brands/{brand_id}", json=brand_data)
        return response.json()
    except requests.RequestException:
        raise HTTPException(status_code=503, detail="Inventory service unavailable")

@app.delete("/brands/{brand_id}")
def delete_brand(brand_id: int, current_admin: dict = Depends(get_current_admin)):
    try:
        response = requests.delete(f"http://inventory-service:8080/admin/brands/{brand_id}")
        return response.json()
    except requests.RequestException:
        raise HTTPException(status_code=503, detail="Inventory service unavailable")

# ========== ORDER MANAGEMENT ROUTES ==========
@app.get("/orders")
def get_all_orders(
    user_id: Optional[int] = Query(None, description="Filter by user ID"),
    status: Optional[str] = Query(None, description="Filter by order status"),
    date_from: Optional[str] = Query(None, description="Filter orders from date (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="Filter orders to date (YYYY-MM-DD)"),
    search: Optional[str] = Query(None, description="Search by customer name or email"),
    limit: Optional[int] = Query(50, description="Number of results to return"),
    offset: Optional[int] = Query(0, description="Number of results to skip"),
    current_admin: dict = Depends(get_current_admin)
):
    try:
        params = {
            "user_id": user_id,
            "status": status,
            "date_from": date_from,
            "date_to": date_to,
            "search": search,
            "limit": limit,
            "offset": offset
        }
        params = {k: v for k, v in params.items() if v is not None}
        
        # Get orders from user service
        orders_response = requests.get("http://user-service:8080/admin/orders", params=params)
        if orders_response.status_code != 200:
            return orders_response.json()
        
        orders = orders_response.json()
        
        for order in orders if isinstance(orders, list) else [orders]:
            if "items" in order:
                for item in order["items"]:
                    if "product_id" in item:
                        try:
                            # Get product details from inventory service
                            product_response = requests.get(f"http://inventory-service:8080/admin/products/{item['product_id']}")
                            if product_response.status_code == 200:
                                product_data = product_response.json()
                                # Merge product details into order item
                                item.update({
                                    "product_name": product_data.get("product_name"),
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
def get_order_details(order_id: int, current_admin: dict = Depends(get_current_admin)):
    try:
        # Get order from user service
        order_response = requests.get(f"http://user-service:8080/admin/orders/{order_id}")
        if order_response.status_code != 200:
            return order_response.json()
        
        order = order_response.json()
        
        if "items" in order:
            for item in order["items"]:
                if "product_id" in item:
                    try:
                        # Get product details from inventory service
                        product_response = requests.get(f"http://inventory-service:8080/admin/products/{item['product_id']}")
                        if product_response.status_code == 200:
                            product_data = product_response.json()
                            # Merge product details into order item
                            item.update({
                                "product_name": product_data.get("product_name"),
                                "description": product_data.get("description"),
                                "brand_name": product_data.get("brand_name"),
                                "market_price": product_data.get("market_price")
                            })
                    except requests.RequestException:
                        pass
        
        return order
    except requests.RequestException:
        raise HTTPException(status_code=503, detail="User service unavailable")

@app.put("/orders/{order_id}/status")
def update_order_status(order_id: int, status: str = Query(..., description="New order status"), current_admin: dict = Depends(get_current_admin)):
    try:
        # First, get the current order status and items
        order_response = requests.get(f"http://user-service:8080/admin/orders/{order_id}")
        if order_response.status_code != 200:
            return order_response.json()
        
        order_data = order_response.json()
        current_status = order_data.get("status", "pending")
        
        # Update order status in user service
        response = requests.put(f"http://user-service:8080/admin/orders/{order_id}/status", json={"status": status})
        if response.status_code != 200:
            return response.json()
        
        # Handle stock management based on status transition
        if "items" in order_data:
            for item in order_data["items"]:
                product_id = item.get("product_id")
                quantity = item.get("quantity", 1)
                
                try:
                    # Stock management logic based on status transitions
                    if current_status == "pending" and status in ["cancelled", "refunded"]:
                        # Order cancelled/refunded - release stock back to inventory
                        release_response = requests.post(f"http://inventory-service:8080/admin/products/{product_id}/release-stock?quantity={quantity}")
                        if release_response.status_code != 200:
                            print(f"Warning: Failed to release stock for product {product_id}")
                    
                    elif current_status in ["cancelled", "refunded"] and status == "pending":
                        # Order reactivated - reserve stock again
                        reserve_response = requests.post(f"http://inventory-service:8080/admin/products/{product_id}/reserve-stock?quantity={quantity}")
                        if reserve_response.status_code != 200:
                            print(f"Warning: Failed to reserve stock for product {product_id}")
                    
                    elif current_status == "pending" and status in ["processing", "shipped", "delivered"]:
                        # Order confirmed - ensure stock is reserved (should already be done during order creation)
                        # This is a safety check in case stock wasn't properly reserved during order creation
                        validate_response = requests.post(f"http://inventory-service:8080/admin/products/{product_id}/validate-stock?quantity={quantity}")
                        if validate_response.status_code != 200:
                            print(f"Warning: Stock validation failed for product {product_id}")
                    
                except requests.RequestException as e:
                    print(f"Warning: Failed to manage stock for product {product_id}: {e}")
        
        return response.json()
    except requests.RequestException:
        raise HTTPException(status_code=503, detail="User service unavailable")

# ========== ANALYTICS ROUTES ==========
@app.get("/analytics/users")
def get_user_analytics(current_admin: dict = Depends(get_current_admin)):
    try:
        response = requests.get("http://user-service:8080/admin/analytics/users")
        return response.json()
    except requests.RequestException:
        raise HTTPException(status_code=503, detail="User service unavailable")

@app.get("/analytics/inventory")
def get_inventory_analytics(current_admin: dict = Depends(get_current_admin)):
    try:
        response = requests.get("http://inventory-service:8080/admin/analytics/inventory")
        return response.json()
    except requests.RequestException:
        raise HTTPException(status_code=503, detail="Inventory service unavailable")

@app.get("/analytics/sales")
def get_sales_analytics(
    date_from: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    current_admin: dict = Depends(get_current_admin)
):
    try:
        params = {
            "date_from": date_from,
            "date_to": date_to
        }
        params = {k: v for k, v in params.items() if v is not None}
        
        response = requests.get("http://user-service:8080/admin/analytics/sales", params=params)
        return response.json()
    except requests.RequestException:
        raise HTTPException(status_code=503, detail="User service unavailable")

