import requests
import json
import os
from typing import Optional, Dict, Any
from datetime import datetime

def clear_terminal():
    os.system('cls' if os.name == 'nt' else 'clear')

def format_table(headers, rows, title=""):
    if not rows:
        return f"{title}\nNo data found."
    
    # Calculate column widths
    col_widths = []
    for i, header in enumerate(headers):
        max_width = len(header)
        for row in rows:
            if i < len(row):
                max_width = max(max_width, len(str(row[i])))
        col_widths.append(max_width)
    
    # Create separator line
    separator = "+" + "+".join("-" * (width + 2) for width in col_widths) + "+"
    
    # Build table
    table = []
    if title:
        table.append(title)
        table.append("")
    
    table.append(separator)
    
    # Header row
    header_row = "|"
    for i, header in enumerate(headers):
        header_row += f" {header:<{col_widths[i]}} |"
    table.append(header_row)
    table.append(separator)
    
    # Data rows
    for row in rows:
        data_row = "|"
        for i, cell in enumerate(row):
            if i < len(row):
                data_row += f" {str(cell):<{col_widths[i]}} |"
        table.append(data_row)
    
    table.append(separator)
    return "\n".join(table)

class AdminCLI:
    def __init__(self):
        self.base_url = "http://localhost:8081"  # Admin load balancer
        self.access_token = None
        self.refresh_token = None
        self.user = None
        
    def login(self, email: str, password: str) -> bool:
        try:
            response = requests.post(f"{self.base_url}/auth/login", json={
                "email": email,
                "password": password
            })
            
            if response.status_code == 200:
                data = response.json()
                self.access_token = data["access_token"]
                self.refresh_token = data["refresh_token"]
                self.user = data["user"]
                print(f"✅ Logged in as {self.user['first_name']} {self.user['last_name']}")
                return True
            else:
                print(f"❌ Login failed: {response.json().get('detail', 'Unknown error')}")
                return False
        except requests.RequestException as e:
            print(f"❌ Connection error: {e}")
            return False
    
    def logout(self):
        if self.access_token:
            try:
                requests.post(f"{self.base_url}/auth/logout", 
                            headers={"Authorization": f"Bearer {self.access_token}"})
            except:
                pass
        self.access_token = None
        self.refresh_token = None
        self.user = None
        print("👋 Logged out")
    
    def make_request(self, method: str, endpoint: str, **kwargs) -> Optional[Dict[str, Any]]:
        if not self.access_token:
            print("❌ Not authenticated. Please login first.")
            return None
        
        headers = {"Authorization": f"Bearer {self.access_token}"}
        if "headers" in kwargs:
            headers.update(kwargs["headers"])
        kwargs["headers"] = headers
        
        try:
            response = requests.request(method, f"{self.base_url}{endpoint}", **kwargs)
            
            if response.status_code == 401:
                print("❌ Token expired. Please login again.")
                return None
            
            return response.json() if response.content else None
        except requests.RequestException as e:
            print(f"❌ Request failed: {e}")
            return None
    
    def list_users(self, role: Optional[str] = None, search: Optional[str] = None):
        params = {}
        if role:
            params["role"] = role
        if search:
            params["search"] = search
        
        data = self.make_request("GET", "/users", params=params)
        if data:
            headers = ["ID", "First Name", "Last Name", "Email", "Role"]
            rows = []
            for user in data:
                rows.append([
                    user['user_id'],
                    user['first_name'],
                    user['last_name'],
                    user['email'],
                    user.get('role', 'customer')
                ])
            
            title = f"👥 Users ({len(data)} found)"
            if role:
                title += f" - Role: {role}"
            if search:
                title += f" - Search: {search}"
            
            print(format_table(headers, rows, title))
        else:
            print("❌ No users found or error occurred.")
    
    def get_user(self, user_id: int):
        data = self.make_request("GET", f"/users/{user_id}")
        if data:
            print(f"\n👤 User Details:")
            print("-" * 40)
            print(f"ID: {data['user_id']}")
            print(f"Name: {data['first_name']} {data['last_name']}")
            print(f"Email: {data['email']}")
            print(f"Role: {data.get('role', 'customer')}")
            
            # Display shipping address information
            if data.get('shipping_address'):
                shipping = data['shipping_address']
                print(f"\n📍 Shipping Address:")
                print(f"  Address: {shipping['line1']}")
                if shipping.get('line2'):
                    print(f"          {shipping['line2']}")
                print(f"  City: {shipping['city']}, {shipping['state']} {shipping['zip_code']}")
                print(f"  Phone: {shipping['phone']}")
            else:
                print(f"\n📍 Shipping Address: Not set")
            
            # Display billing address information
            if data.get('billing_address'):
                billing = data['billing_address']
                print(f"\n💳 Billing Address:")
                print(f"  Address: {billing['line1']}")
                if billing.get('line2'):
                    print(f"          {billing['line2']}")
                print(f"  City: {billing['city']}, {billing['state']} {billing['zip_code']}")
                print(f"  Phone: {billing['phone']}")
            else:
                print(f"\n💳 Billing Address: Not set")
    
    def create_user(self, first_name: str, last_name: str, email: str, password: str, role: str = "customer"):
        data = self.make_request("POST", "/users", json={
            "first_name": first_name,
            "last_name": last_name,
            "email": email,
            "password": password,
            "role": role
        })
        if data:
            print(f"✅ User created successfully: {data.get('user_id')}")
    
    def update_user_role(self, user_id: int, role: str):
        data = self.make_request("PUT", f"/users/{user_id}/role?role={role}")
        if data:
            print(f"✅ User role updated to {role}")
    
    def delete_user(self, user_id: int):
        data = self.make_request("DELETE", f"/users/{user_id}")
        if data:
            print(f"✅ User deleted successfully")
    
    def list_products(self, brand: Optional[str] = None, search: Optional[str] = None):
        params = {}
        if brand:
            params["brand"] = brand
        if search:
            params["search"] = search
        
        data = self.make_request("GET", "/inventory", params=params)
        if data:
            headers = ["ID", "Product Name", "Brand", "Price", "Discount", "Final Price", "Quantity"]
            rows = []
            for product in data:
                price = product.get('market_price', 0)
                discount = product.get('discount_percent', 0)
                final_price = price * (1 - discount / 100)
                rows.append([
                    product['product_id'],
                    product['product_name'],
                    product.get('brand_name', 'N/A'),
                    f"${price:.2f}",
                    f"{discount}%",
                    f"${final_price:.2f}",
                    product.get('quantity', 0)
                ])
            
            title = f"📦 Products ({len(data)} found)"
            if brand:
                title += f" - Brand: {brand}"
            if search:
                title += f" - Search: {search}"
            
            print(format_table(headers, rows, title))
        else:
            print("❌ No products found or error occurred.")
    
    def get_product(self, product_id: int):
        data = self.make_request("GET", f"/inventory/{product_id}")
        if data:
            print(f"\n📦 Product Details:")
            print("-" * 40)
            print(f"ID: {data['product_id']}")
            print(f"Name: {data['product_name']}")
            print(f"Brand: {data.get('brand_name', 'N/A')}")
            print(f"Price: ${data.get('market_price', 0):.2f}")
            print(f"Discount: {data.get('discount_percent', 0)}%")
            print(f"Quantity: {data.get('quantity', 0)}")
            print(f"Description: {data.get('description', 'No description')}")
    
    def create_product(self, brand_id: int, product_name: str, 
                      market_price: float, discount_percent: float = 0, description: str = "", quantity: int = 0):
        data = self.make_request("POST", "/inventory", json={
            "brand_id": brand_id,
            "product_name": product_name,
            "description": description,
            "market_price": market_price,
            "discount_percent": discount_percent,
            "quantity": quantity
        })
        if data:
            print(f"✅ Product created successfully: {data.get('product_id')}")
    
    def update_product(self, product_id: int, **kwargs):
        data = self.make_request("PUT", f"/inventory/{product_id}", json=kwargs)
        if data:
            print(f"✅ Product updated successfully")
    
    def list_brands(self):
        data = self.make_request("GET", "/brands")
        if data:
            headers = ["ID", "Brand Name"]
            rows = []
            for brand in data:
                rows.append([
                    brand['brand_id'],
                    brand['brand_name']
                ])
            
            print(format_table(headers, rows, f"🏷️ Brands ({len(data)} found)"))
        else:
            print("❌ No brands found or error occurred.")
    
    def create_brand(self, brand_name: str):
        data = self.make_request("POST", "/brands", json={"brand_name": brand_name})
        if data:
            print(f"✅ Brand created successfully: {data.get('brand_id')}")
    
    def list_orders(self, user_id: Optional[int] = None, status: Optional[str] = None, 
                   search: Optional[str] = None, date_from: Optional[str] = None, 
                   date_to: Optional[str] = None):
        params = {}
        if user_id:
            params["user_id"] = user_id
        if status:
            params["status"] = status
        if search:
            params["search"] = search
        if date_from:
            params["date_from"] = date_from
        if date_to:
            params["date_to"] = date_to
        
        data = self.make_request("GET", "/orders", params=params)
        if data:
            headers = ["ID", "Customer", "Status", "Created Date"]
            rows = []
            for order in data:
                # Handle both string and dictionary responses
                if isinstance(order, dict):
                    # Get user name from the order data
                    first_name = order.get('first_name', 'Unknown')
                    last_name = order.get('last_name', '')
                    customer_name = f"{first_name} {last_name}".strip()
                    
                    rows.append([
                        order.get('order_id', 'N/A'),
                        customer_name,
                        order.get('order_status', 'N/A'),
                        order.get('order_date', 'N/A')
                    ])
                else:
                    # If order is a string, skip it
                    continue
            
            title = f"📋 Orders ({len(data)} found)"
            if user_id:
                title += f" - User ID: {user_id}"
            if status:
                title += f" - Status: {status}"
            if search:
                title += f" - Search: {search}"
            if date_from or date_to:
                date_range = []
                if date_from:
                    date_range.append(f"from {date_from}")
                if date_to:
                    date_range.append(f"to {date_to}")
                title += f" - Date: {' '.join(date_range)}"
            
            print(format_table(headers, rows, title))
        else:
            print("❌ No orders found or error occurred.")
    
    def get_order(self, order_id: int):
        data = self.make_request("GET", f"/orders/{order_id}")
        if data:
            print(f"\n📋 Order Details:")
            print("-" * 40)
            print(f"ID: {data.get('order_id', 'N/A')}")
            
            # Get customer name
            first_name = data.get('first_name', 'Unknown')
            last_name = data.get('last_name', '')
            customer_name = f"{first_name} {last_name}".strip()
            print(f"Customer: {customer_name}")
            print(f"Email: {data.get('email', 'N/A')}")
            print(f"Status: {data.get('order_status', 'N/A')}")
            print(f"Created: {data.get('order_date', 'N/A')}")
            print(f"Subtotal: ${data.get('subtotal_amount', 0):.2f}")
            print(f"Tax: ${data.get('tax_amount', 0):.2f}")
            print(f"Total: ${data.get('total_amount', 0):.2f}")
            if 'items' in data:
                print(f"Items ({len(data['items'])}):")
                for item in data['items']:
                    print(f"  - {item.get('product_name', 'Unknown')} x{item.get('quantity', 1)}")
    
    def update_order_status(self, order_id: int, status: str):
        data = self.make_request("PUT", f"/orders/{order_id}/status?status={status}")
        if data:
            print(f"✅ Order status updated to {status}")
    
    def show_analytics(self):
        print("\n📊 Analytics Dashboard")
        print("=" * 50)
        
        # User analytics
        user_analytics = self.make_request("GET", "/analytics/users")
        if user_analytics:
            headers = ["Metric", "Value"]
            rows = [
                ["Total Users", user_analytics.get('total_users', 0)],
                ["Active Users", user_analytics.get('active_users', 0)],
                ["New Users (Today)", user_analytics.get('new_users_today', 0)]
            ]
            print(format_table(headers, rows, "👥 User Statistics"))
            print()
        
        # Inventory analytics
        inventory_analytics = self.make_request("GET", "/analytics/inventory")
        if inventory_analytics:
            headers = ["Metric", "Value"]
            rows = [
                ["Total Products", inventory_analytics.get('total_products', 0)],
                ["Total Brands", inventory_analytics.get('total_brands', 0)],
                ["Products on Discount", inventory_analytics.get('discounted_products', 0)]
            ]
            print(format_table(headers, rows, "📦 Inventory Statistics"))
            print()
        
        # Sales analytics
        sales_analytics = self.make_request("GET", "/analytics/sales")
        if sales_analytics:
            headers = ["Metric", "Value"]
            rows = [
                ["Total Sales", f"${sales_analytics.get('total_sales', 0):.2f}"],
                ["Total Orders", sales_analytics.get('total_orders', 0)],
                ["Average Order Value", f"${sales_analytics.get('avg_order_value', 0):.2f}"]
            ]
            print(format_table(headers, rows, "💰 Sales Statistics"))

def print_main_menu():
    print("\n" + "="*50)
    print("🛡️  ADMIN CLI - Sneaker Store Management")
    print("="*50)
    if not cli.access_token:
        print("🔐 Authentication")
        print("1.  Login")
        print("0.  Exit")
    else:
        print(f"👤 Logged in as: {cli.user['first_name']} {cli.user['last_name']}")
        print("\n📊 Management")
        print("2.  Show Analytics Dashboard")
        print("3.  User Management")
        print("4.  Product Management")
        print("5.  Order Management")
        print("6.  Logout")
        print("0.  Exit")
    print("-"*50)

def print_user_menu():
    print("\n" + "="*40)
    print("👥 USER MANAGEMENT")
    print("="*40)
    print("1.  List All Users")
    print("2.  Search Users")
    print("3.  Get User Details")
    print("4.  Create New User")
    print("5.  Update User Role")
    print("6.  Delete User")
    print("0.  Back to Main Menu")
    print("-"*40)

def print_product_menu():
    print("\n" + "="*40)
    print("📦 PRODUCT MANAGEMENT")
    print("="*40)
    print("1.  List All Products")
    print("2.  Search Products")
    print("3.  Get Product Details")
    print("4.  Create New Product")
    print("5.  Update Product")
    print("6.  List All Brands")
    print("7.  Create New Brand")
    print("0.  Back to Main Menu")
    print("-"*40)

def print_order_menu():
    print("\n" + "="*40)
    print("📋 ORDER MANAGEMENT")
    print("="*40)
    print("1.  List All Orders")
    print("2.  Search Orders")
    print("3.  Get Order Details")
    print("4.  Update Order Status")
    print("0.  Back to Main Menu")
    print("-"*40)

def main():
    global cli
    cli = AdminCLI()
    
    clear_terminal()
    print("🛡️  Welcome to Admin CLI")
    print("Make sure the backend services are running!")
    
    while True:
        clear_terminal()
        print_main_menu()
        
        if not cli.access_token:
            choice = input("\nEnter your choice (0-1): ").strip()
            
            if choice == "0":
                print("👋 Goodbye!")
                break
            elif choice == "1":
                email = input("Email: ").strip()
                password = input("Password: ").strip()
                cli.login(email, password)
            else:
                print("❌ Invalid choice. Please try again.")
                input("\nPress Enter to continue...")
        else:
            choice = input("\nEnter your choice (0-6): ").strip()
            
            if choice == "0":
                print("👋 Goodbye!")
                break
            elif choice == "2":
                clear_terminal()
                cli.show_analytics()
            elif choice == "3":
                user_management_loop()
            elif choice == "4":
                product_management_loop()
            elif choice == "5":
                order_management_loop()
            elif choice == "6":
                cli.logout()
            else:
                print("❌ Invalid choice. Please try again.")
            
            input("\nPress Enter to continue...")

def user_management_loop():
    while True:
        clear_terminal()
        print_user_menu()
        choice = input("\nEnter your choice (0-6): ").strip()
        
        if choice == "0":
            break
        elif choice == "1":
            clear_terminal()
            cli.list_users()
        elif choice == "2":
            clear_terminal()
            role = input("Filter by role (customer/admin) [Enter for all]: ").strip() or None
            search = input("Search term [Enter for none]: ").strip() or None
            cli.list_users(role, search)
        elif choice == "3":
            clear_terminal()
            print("👤 Get User Details")
            print("=" * 40)
            print("📋 Current Users:")
            cli.list_users()
            print("\n" + "=" * 40)
            user_id = input("User ID: ").strip()
            try:
                cli.get_user(int(user_id))
            except ValueError:
                print("❌ Invalid user ID")
        elif choice == "4":
            clear_terminal()
            print("👤 Create New User")
            print("=" * 40)
            print("📋 Current Users:")
            cli.list_users()
            print("\n" + "=" * 40)
            first_name = input("First Name: ").strip()
            last_name = input("Last Name: ").strip()
            email = input("Email: ").strip()
            password = input("Password: ").strip()
            role = input("Role (customer/admin) [customer]: ").strip() or "customer"
            cli.create_user(first_name, last_name, email, password, role)
        elif choice == "5":
            clear_terminal()
            print("👤 Update User Role")
            print("=" * 40)
            print("📋 Current Users:")
            cli.list_users()
            print("\n" + "=" * 40)
            user_id = input("User ID: ").strip()
            role = input("New Role (customer/admin): ").strip()
            try:
                cli.update_user_role(int(user_id), role)
            except ValueError:
                print("❌ Invalid user ID")
        elif choice == "6":
            clear_terminal()
            print("👤 Delete User")
            print("=" * 40)
            print("📋 Current Users:")
            cli.list_users()
            print("\n" + "=" * 40)
            user_id = input("User ID: ").strip()
            confirm = input("Are you sure? (y/N): ").strip().lower()
            if confirm == 'y':
                try:
                    cli.delete_user(int(user_id))
                except ValueError:
                    print("❌ Invalid user ID")
            else:
                print("❌ Cancelled")
        else:
            print("❌ Invalid choice. Please try again.")
        
        input("\nPress Enter to continue...")

def product_management_loop():
    while True:
        clear_terminal()
        print_product_menu()
        choice = input("\nEnter your choice (0-7): ").strip()
        
        if choice == "0":
            break
        elif choice == "1":
            clear_terminal()
            cli.list_products()
        elif choice == "2":
            clear_terminal()
            brand = input("Filter by brand [Enter for all]: ").strip() or None
            search = input("Search term [Enter for none]: ").strip() or None
            cli.list_products(brand, search)
        elif choice == "3":
            clear_terminal()
            print("📦 Get Product Details")
            print("=" * 40)
            print("📋 Current Products:")
            cli.list_products()
            print("\n" + "=" * 40)
            product_id = input("Product ID: ").strip()
            try:
                cli.get_product(int(product_id))
            except ValueError:
                print("❌ Invalid product ID")
        elif choice == "4":
            clear_terminal()
            print("📦 Create New Product")
            print("=" * 40)
            print("📋 Available Brands:")
            cli.list_brands()
            print("\n📋 Current Products:")
            cli.list_products()
            print("\n" + "=" * 40)
            brand_id = input("Brand ID: ").strip()
            product_name = input("Product Name: ").strip()
            market_price = input("Market Price: ").strip()
            discount_percent = input("Discount % [0]: ").strip() or "0"
            quantity = input("Quantity [0]: ").strip() or "0"
            description = input("Description [Enter for none]: ").strip() or ""
            try:
                cli.create_product(int(brand_id), product_name, 
                                 float(market_price), float(discount_percent), description, int(quantity))
            except ValueError:
                print("❌ Invalid numeric values")
        elif choice == "5":
            clear_terminal()
            print("📦 Update Product")
            print("=" * 40)
            print("📋 Current Products:")
            cli.list_products()
            print("\n" + "=" * 40)
            product_id = input("Product ID: ").strip()
            print("\n📋 Update Fields (press Enter to skip):")
            brand_id = input("Brand ID [Enter to skip]: ").strip() or None
            product_name = input("Product Name [Enter to skip]: ").strip() or None
            market_price = input("Market Price [Enter to skip]: ").strip() or None
            discount_percent = input("Discount % [Enter to skip]: ").strip() or None
            quantity = input("Quantity [Enter to skip]: ").strip() or None
            description = input("Description [Enter to skip]: ").strip() or None
            
            update_data = {}
            if brand_id:
                try:
                    update_data["brand_id"] = int(brand_id)
                except ValueError:
                    print("❌ Invalid brand ID")
                    continue
            if product_name:
                update_data["product_name"] = product_name
            if market_price:
                try:
                    update_data["market_price"] = float(market_price)
                except ValueError:
                    print("❌ Invalid market price")
                    continue
            if discount_percent:
                try:
                    update_data["discount_percent"] = float(discount_percent)
                except ValueError:
                    print("❌ Invalid discount percentage")
                    continue
            if quantity:
                try:
                    update_data["quantity"] = int(quantity)
                except ValueError:
                    print("❌ Invalid quantity")
                    continue
            if description:
                update_data["description"] = description
            
            if update_data:
                try:
                    cli.update_product(int(product_id), **update_data)
                except ValueError:
                    print("❌ Invalid product ID")
            else:
                print("❌ No fields to update")
        elif choice == "6":
            clear_terminal()
            print("🏷️ Available Brands")
            print("=" * 40)
            cli.list_brands()
        elif choice == "7":
            clear_terminal()
            print("🏷️ Create New Brand")
            print("=" * 40)
            print("📋 Current Brands:")
            cli.list_brands()
            print("\n" + "=" * 40)
            brand_name = input("Brand Name: ").strip()
            cli.create_brand(brand_name)
        else:
            print("❌ Invalid choice. Please try again.")
        
        input("\nPress Enter to continue...")

def order_management_loop():
    while True:
        clear_terminal()
        print_order_menu()
        choice = input("\nEnter your choice (0-4): ").strip()
        
        if choice == "0":
            break
        elif choice == "1":
            clear_terminal()
            cli.list_orders()
        elif choice == "2":
            clear_terminal()
            print("📋 Search Orders")
            print("=" * 40)
            print("Enter search criteria (press Enter to skip):")
            print()
            
            user_id = input("Filter by User ID [Enter for all]: ").strip() or None
            status = input("Filter by Status [Enter for all]: ").strip() or None
            search = input("Search by customer name/email [Enter for none]: ").strip() or None
            date_from = input("Date from (YYYY-MM-DD) [Enter for none]: ").strip() or None
            date_to = input("Date to (YYYY-MM-DD) [Enter for none]: ").strip() or None
            
            try:
                cli.list_orders(int(user_id) if user_id else None, status, search, date_from, date_to)
            except ValueError:
                print("❌ Invalid user ID")
        elif choice == "3":
            clear_terminal()
            print("📋 Get Order Details")
            print("=" * 40)
            print("📋 Current Orders:")
            cli.list_orders()
            print("\n" + "=" * 40)
            order_id = input("Order ID: ").strip()
            try:
                cli.get_order(int(order_id))
            except ValueError:
                print("❌ Invalid order ID")
        elif choice == "4":
            clear_terminal()
            print("📋 Update Order Status")
            print("=" * 40)
            print("📋 Current Orders:")
            cli.list_orders()
            print("\n" + "=" * 40)
            order_id = input("Order ID: ").strip()
            
            # Show available status options
            print("\n📋 Available Status Options:")
            print("1. pending")
            print("2. processing")
            print("3. shipped")
            print("4. delivered")
            print("5. cancelled")
            print("6. refunded")
            
            status_choice = input("\nSelect status (1-6): ").strip()
            status_map = {
                "1": "pending",
                "2": "processing", 
                "3": "shipped",
                "4": "delivered",
                "5": "cancelled",
                "6": "refunded"
            }
            
            status = status_map.get(status_choice)
            if not status:
                print("❌ Invalid status choice")
            else:
                try:
                    cli.update_order_status(int(order_id), status)
                except ValueError:
                    print("❌ Invalid order ID")
        else:
            print("❌ Invalid choice. Please try again.")
        
        input("\nPress Enter to continue...")

if __name__ == "__main__":
    main()
