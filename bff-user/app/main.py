import fastapi
import requests
from fastapi import HTTPException, Query
from typing import Optional
from pydantic import BaseModel

app = fastapi.FastAPI()

# Data models for request/response
class LoginRequest(BaseModel):
    email: str
    password: str

class UserRegistration(BaseModel):
    first_name: str
    last_name: str
    email: str
    password: str

# Health check
@app.get("/")
def read_root():
    return {"message": "User BFF is running"}

# ========== AUTHENTICATION ROUTES ==========
@app.post("/auth/login")
def login(login_data: LoginRequest):
    try:
        # Call IDP service for authentication
        response = requests.post("http://idp-service:8080/login", json=login_data.dict())
        return response.json()
    except requests.RequestException:
        raise HTTPException(status_code=503, detail="Authentication service unavailable")

@app.post("/auth/register")
def register(user_data: UserRegistration):
    try:
        # Call user service to create account
        response = requests.post("http://user-service:8080/users", json=user_data.dict())
        return response.json()
    except requests.RequestException:
        raise HTTPException(status_code=503, detail="User service unavailable")

@app.post("/auth/logout")
def logout():
    try:
        response = requests.post("http://idp-service:8080/logout")
        return response.json()
    except requests.RequestException:
        raise HTTPException(status_code=503, detail="Authentication service unavailable")

# ========== USER PROFILE ROUTES ==========
@app.get("/profile")
def get_user_profile(user_id: int = Query(..., description="User ID")):
    try:
        response = requests.get(f"http://user-service:8080/users/{user_id}")
        return response.json()
    except requests.RequestException:
        raise HTTPException(status_code=503, detail="User service unavailable")

@app.put("/profile")
def update_user_profile(user_id: int = Query(...), profile_data: dict = {}):
    try:
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
def get_cart(user_id: int = Query(...)):
    try:
        response = requests.get(f"http://user-service:8080/users/{user_id}/cart")
        return response.json()
    except requests.RequestException:
        raise HTTPException(status_code=503, detail="User service unavailable")

@app.post("/cart/add")
def add_to_cart(user_id: int = Query(...), product_id: int = Query(...), quantity: int = Query(1)):
    try:
        cart_data = {"product_id": product_id, "quantity": quantity}
        response = requests.post(f"http://user-service:8080/users/{user_id}/cart", json=cart_data)
        return response.json()
    except requests.RequestException:
        raise HTTPException(status_code=503, detail="User service unavailable")

@app.delete("/cart/remove")
def remove_from_cart(user_id: int = Query(...), product_id: int = Query(...)):
    try:
        response = requests.delete(f"http://user-service:8080/users/{user_id}/cart/{product_id}")
        return response.json()
    except requests.RequestException:
        raise HTTPException(status_code=503, detail="User service unavailable")

# ========== ORDER ROUTES ==========
@app.get("/orders")
def get_user_orders(user_id: int = Query(...)):
    try:
        response = requests.get(f"http://user-service:8080/users/{user_id}/orders")
        return response.json()
    except requests.RequestException:
        raise HTTPException(status_code=503, detail="User service unavailable")

@app.post("/orders")
def create_order(user_id: int = Query(...), order_data: dict = {}):
    try:
        response = requests.post(f"http://user-service:8080/users/{user_id}/orders", json=order_data)
        return response.json()
    except requests.RequestException:
        raise HTTPException(status_code=503, detail="User service unavailable")