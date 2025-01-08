import os
import json
import uuid
import hashlib
import argparse
from functools import wraps
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse
from datetime import datetime, timedelta
import requests
from security.TokenManager import TokenManager

# File paths
MENU_FILE = "data/menu.json"
USERS_FILE = "data/clients.json"
ORDERS_FILE = "data/orders.json"

# Initialization of token manager
token_manager = None

def get_token_manager():
    """
    Getting token manager
    """
    global token_manager
    if token_manager is None:
        token_manager = TokenManager()
    return token_manager

def get_order_status(order):
    """Calculate the current status based on time"""
    order_time = datetime.fromisoformat(order["order_time"])
    delivery_time = datetime.fromisoformat(order["delivery_time"])
    current_time = datetime.now()

    if current_time >= delivery_time:
        return "delivered"
    elif current_time >= order_time + timedelta(minutes=5):
        return "in delivery"
    elif current_time >= order_time + timedelta(minutes=2):
        return "preparing"
    else:
        return "pending"

def login_required(func):
    """
    Checking if u need to login
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        response = requests.get("http://localhost:8000/whoami")
        data = response.json()
        if "user" not in data:
            print("You need to be logged in first.")
            if login_user():
                return func(*args, **kwargs)
            return False
        return func(*args, **kwargs)
    return wrapper

def load_menu():
    """Loading Menu"""
    os.makedirs(os.path.dirname(MENU_FILE), exist_ok=True)
    if os.path.exists(MENU_FILE):
        try:
            with open(MENU_FILE, "r") as f:
                return json.load(f)
        except json.JSONDecodeError:
            print("Warning: Menu file is corrupted. Loading default menu.")
    return {
        "1": {"name": "Margherita", "price": 8.99},
        "2": {"name": "Pepperoni", "price": 9.99},
        "3": {"name": "Veggie", "price": 10.99}
    }

def load_users():
    """Loading Users"""
    os.makedirs(os.path.dirname(USERS_FILE), exist_ok=True)
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, "r") as f:
                return json.load(f)
        except json.JSONDecodeError:
            print("Warning: Users file is corrupted. Creating new users file.")
    return {}

def load_orders():
    """Loading orders"""
    os.makedirs(os.path.dirname(ORDERS_FILE), exist_ok=True)
    if os.path.exists(ORDERS_FILE):
        try:
            with open(ORDERS_FILE, "r") as f:
                return json.load(f)
        except json.JSONDecodeError:
            print("Warning: Orders file is corrupted. Creating new orders file.")
    return {}

def save_menu():
    """Saving menu"""
    os.makedirs(os.path.dirname(MENU_FILE), exist_ok=True)
    with open(MENU_FILE, "w") as f:
        json.dump(menu, f, indent=4)

def save_users(users):
    """Saving users"""
    os.makedirs(os.path.dirname(USERS_FILE), exist_ok=True)
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=4)

def save_orders(orders):
    """Saving orders"""
    os.makedirs(os.path.dirname(ORDERS_FILE), exist_ok=True)
    with open(ORDERS_FILE, "w") as f:
        json.dump(orders, f, indent=4)

def hash_password(password):
    """Hashing password"""
    return hashlib.sha256(password.encode()).hexdigest()

menu = load_menu()
users = load_users()
orders = load_orders()
current_user = None

class PizzaServer(BaseHTTPRequestHandler):
    """Class responsible for server side"""
    def _send_response(self, status_code, data):
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def _validate_admin(self):
        """Validating Admin token"""
        headers = self.headers
        token = headers.get("Admin-Token")
        if not token:
            self._send_response(401, {"error": "Admin token required"})
            return False

        manager = get_token_manager()
        is_valid, message = manager.validate_token(token)
        if not is_valid:
            self._send_response(401, {"error": f"Unauthorized access. {message}"})
            return False
        return True

    def do_GET(self):
        """Do get"""
        global menu, current_user, orders
        menu = load_menu()
        orders = load_orders()

        if self.path == "/menu":
            self._send_response(200, menu)
        elif self.path.startswith("/order/status"):
            query = parse_qs(urlparse(self.path).query)
            order_id = query.get("order_id", [None])[0]
            if not order_id or order_id not in orders:
                self._send_response(404, {"error": "Order not found."})
                return

            # Update the order status based on current time
            orders[order_id]["status"] = get_order_status(orders[order_id])
            save_orders(orders)  # Save the updated status

            self._send_response(200, orders[order_id])
        elif self.path == "/whoami":
            if current_user is None:
                self._send_response(200, {"message": "No user is currently logged in."})
                return

            self._send_response(200, {
                "message": f"Logged in as {current_user['name']}",
                "user": current_user
            })
        else:
            self._send_response(404, {"error": "Invalid endpoint."})

    def do_POST(self):
        """Do Post"""
        global current_user, menu, users, orders
        content_length = int(self.headers['Content-Length'])
        post_data = json.loads(self.rfile.read(content_length))

        if self.path == "/register":
            name = post_data.get("name")
            password = post_data.get("password")
            street = post_data.get("street")

            if not all([name, password, street]):
                self._send_response(400, {"error": "Name, password, and street are required."})
                return

            if name in users:
                self._send_response(409, {"error": "Username already exists."})
                return

            users[name] = {
                "password": hash_password(password),
                "street": street
            }
            save_users(users)
            self._send_response(201, {"message": "User registered successfully."})

        elif self.path == "/login":
            name = post_data.get("name")
            password = post_data.get("password")

            if not all([name, password]):
                self._send_response(400, {"error": "Name and password are required."})
                return

            if name not in users or users[name]["password"] != hash_password(password):
                self._send_response(401, {"error": "Invalid username or password."})
                return

            current_user = {
                "name": name,
                "street": users[name]["street"]
            }

            self._send_response(200, {
                "message": "Login successful",
                "street": users[name]["street"]
            })

        elif self.path == "/logout":
            if current_user is None:
                self._send_response(400, {"error": "No user is currently logged in."})
                return

            logged_out_user = current_user["name"]
            current_user = None
            self._send_response(200, {"message": f"User {logged_out_user} logged out successfully."})

        elif self.path == "/menu" and self._validate_admin():
            name = post_data.get("name")
            price = post_data.get("price")

            if not name or not isinstance(price, (int, float)):
                self._send_response(400, {"error": "Invalid pizza name or price."})
                return

            pizza_id = str(len(menu) + 1)
            menu[pizza_id] = {"name": name, "price": price}
            save_menu()
            self._send_response(201, {"message": f"Pizza '{name}' added successfully."})

        elif self.path == "/order":
            items = post_data.get("items", [])
            if current_user:
                address = current_user["street"]
            else:
                address = post_data.get("address")
                if not address:
                    self._send_response(400, {"error": "Address is required for non-logged in users."})
                    return

            if not items:
                self._send_response(400, {"error": "Items are required."})
                return

            validated_items = []
            for item in items:
                pizza_id = item.get("pizza_id")
                quantity = item.get("quantity", 0)

                if pizza_id not in menu:
                    self._send_response(400, {"error": f"Pizza ID {pizza_id} does not exist."})
                    return
                if quantity <= 0:
                    self._send_response(400, {"error": f"Invalid quantity {quantity} for pizza ID {pizza_id}."})
                    return

                validated_items.append({"pizza_id": pizza_id, "quantity": quantity})

            order_id = str(uuid.uuid4())
            order_time = datetime.now()
            delivery_time = order_time + timedelta(minutes=30)

            orders[order_id] = {
                "user": current_user["name"] if current_user else "Guest",
                "items": validated_items,
                "status": "pending",
                "address": address,
                "order_time": order_time.isoformat(),
                "delivery_time": delivery_time.isoformat()
            }
            save_orders(orders)
            self._send_response(201, {"order_id": order_id})

    def do_DELETE(self):
        """Do delete"""
        if self.path.startswith("/menu/"):
            if not self._validate_admin():
                return
            pizza_id = self.path.split("/")[-1]
            if pizza_id in menu:
                del menu[pizza_id]
                save_menu()
                self._send_response(200, {"message": "Pizza deleted successfully."})
            else:
                self._send_response(404, {"error": "Pizza not found."})

        elif self.path.startswith("/order/"):
            order_id = self.path.split("/")[-1]

            if order_id not in orders:
                self._send_response(404, {"error": "Order not found"})
                return

            # Get the order details
            order = orders[order_id]

            # Check if order can still be cancelled (within 1 minute)
            order_time = datetime.fromisoformat(order["order_time"])
            time_elapsed = datetime.now() - order_time
            if time_elapsed.total_seconds() > 60:  # 60 seconds = 1 minute
                self._send_response(400, {"error": "Order cannot be cancelled after 1 minute"})
                return

            is_guest_order = order["user"] == "Guest"
            is_user_order = current_user and order["user"] == current_user["name"]

            # Check if admin token is provided
            headers = self.headers
            token = headers.get("Admin-Token")
            is_admin = False
            if token:
                manager = get_token_manager()
                is_admin, _ = manager.validate_token(token)

            # Authorization check
            if not (is_admin or is_guest_order or is_user_order):
                self._send_response(403, {"error": "Unauthorized to cancel this order"})
                return

            del orders[order_id]
            save_orders(orders)
            self._send_response(200, {"message": "Order cancelled successfully"})

def list_menu():
    """Listing menu"""
    try:
        response = requests.get("http://localhost:8000/menu",timeout=10)
        if response.status_code == 200:
            menu_data = response.json()
        else:
            raise requests.RequestException("Server returned an error.")
    except requests.RequestException:
        print("Server not available. Loading menu from local file.")
        menu_data = load_menu()

    print("\n--- Pizza Menu ---")
    for pizza_id, details in menu_data.items():
        print(f"{pizza_id}. {details['name']} - ${details['price']:.2f}")

def create_order():
    """Creating order"""
    print("\n--- Create Order ---")
    order_items = []

    while True:
        pizza_id = input("Enter pizza ID (or press Enter to finish): ")
        if not pizza_id:
            break
        try:
            quantity = int(input("Enter quantity: "))
            order_items.append({"pizza_id": pizza_id, "quantity": quantity})
        except ValueError:
            print("Invalid quantity. Try again.")

    # Check if user is logged in
    whoami = requests.get("http://localhost:8000/whoami",timeout=10)
    data = whoami.json()

    if "user" not in data:
        address = input("Enter delivery address: ")
        order_data = {"items": order_items, "address": address}
    else:
        order_data = {"items": order_items}

    response = requests.post("http://localhost:8000/order", json=order_data,timeout=10)

    if response.status_code == 201:
        print(f"Order created successfully! Order ID: {response.json()['order_id']}")
    else:
        print("Failed to create order.", response.json())

def check_order_status():
    """Checking order status"""
    order_id = input("Enter order ID to check status: ")
    response = requests.get(f"http://localhost:8000/order/status?order_id={order_id}",timeout=10)
    if response.status_code == 200:
        order = response.json()
        order_time = datetime.fromisoformat(order["order_time"])
        delivery_time = datetime.fromisoformat(order["delivery_time"])
        current_time = datetime.now()
        time_elapsed = current_time - order_time
        time_to_delivery = delivery_time - current_time if delivery_time > current_time else timedelta(0)
        print("\n--- Order Status ---")
        print(f"Order ID: {order_id}")
        print(f"User: {order.get('user', 'Unknown')}")
        print(f"Address: {order['address']}")
        print(f"Status: {order['status'].upper()}")
        print(f"Order Time: {order['order_time']}")
        print(f"Time Elapsed: {int(time_elapsed.total_seconds() // 60)} minutes {int(time_elapsed.total_seconds() % 60)} seconds")
        if order['status'] != "delivered":
            print(f"Estimated Time to Delivery: {int(time_to_delivery.total_seconds() // 60)} minutes")
        
        print("Items:")
        menu_data = load_menu()
        for item in order['items']:
            pizza_name = menu_data[item['pizza_id']]['name']
            print(f"  {item['quantity']} x {pizza_name} (ID: {item['pizza_id']})")
    else:
        print("Failed to fetch order status.", response.json())

def cancel_order():
    """Function for cancelling order"""
    order_id = input("Enter order ID to cancel: ")

    try:
        status_response = requests.get(f"http://localhost:8000/order/status?order_id={order_id}",timeout=10)
        if status_response.status_code != 200:
            print("Order not found.")
            return

        order_info = status_response.json()

        order_time = datetime.fromisoformat(order_info["order_time"])
        time_elapsed = datetime.now() - order_time

        if time_elapsed.total_seconds() > 60:
            print("Error: Orders can only be cancelled within 1 minute of placing them.")
            print(f"This order was placed {int(time_elapsed.total_seconds())} seconds ago.")
            return

        response = requests.delete(f"http://localhost:8000/order/{order_id}",timeout=10)

        try:
            response_data = response.json()
        except json.JSONDecodeError:
            print(f"Error: Could not parse server response. Status code: {response.status_code}")
            print(f"Response text: {response.text}")
            return

        if response.status_code == 200:
            print("Order cancelled successfully!")
        elif response.status_code == 404:
            print("Order not found.")
        elif response.status_code == 403:
            print("You are not authorized to cancel this order.")
        else:
            error_msg = response_data.get('error', 'Unknown error')
            print(f"Failed to cancel order: {error_msg}")

    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to server. Make sure the server is running.")
    except Exception as e:
        print(f"Error: {str(e)}")
        print("If the problem persists, please contact support.")

def register_user():
    """Register user"""
    print("\n--- User Registration ---")
    name = input("Enter username: ").strip()
    password = input("Enter password: ").strip()
    street = input("Enter street address: ").strip()

    response = requests.post("http://localhost:8000/register",
                           json={"name": name, "password": password, "street": street},timeout=10)

    if response.status_code == 201:
        print("Registration successful!")
    else:
        print("Registration failed:", response.json().get("error"))

def login_user():
    """Login user"""
    print("\n--- User Login ---")
    name = input("Enter username: ").strip()
    password = input("Enter password: ").strip()

    response = requests.post("http://localhost:8000/login",
                           json={"name": name, "password": password},timeout=10)

    if response.status_code == 200:
        print("Login successful!")
        data = response.json()
        print(f"Welcome back! Your delivery address is: {data['street']}")
        return True
    else:
        print("Login failed:", response.json().get("error"))
        return False

def logout_user():
    """Logout user"""
    try:
        response = requests.post("http://localhost:8000/logout", json={},timeout=10)
        if response.status_code == 200:
            print(response.json()["message"])
        else:
            print("Logout failed:", response.json().get("error"))
    except requests.exceptions.ConnectionError:
        print("Error: Server is not running. Please start the server first.")
    except Exception as e:
        print(f"Logout failed: {str(e)}")

def check_current_user():
    """Checking current user"""
    response = requests.get("http://localhost:8000/whoami",timeout=10)
    data = response.json()
    print(data["message"])
    if "user" in data:
        print(f"Delivery address: {data['user']['street']}")

def admin_panel():
    """Admin Panel"""
    print("\n--- Generate New Admin Token ---")
    manager = get_token_manager()
    token = manager.generate_token()
    print(f"Your new admin token is: {token}")
    print("Please save this token securely. It will expire in 24 hours.")

    print("\n--- Admin Panel ---")
    while True:
        print("\n1. Add Pizza to Menu")
        print("2. Delete Pizza from Menu")
        print("3. Cancel Any Order")
        print("4. Generate New Admin Token")
        print("5. Quit Admin Panel")
        choice = input("Select an option: ").strip()

        if choice == "1":
            pizza_name = input("Enter pizza name: ").strip()
            try:
                pizza_price = float(input("Enter pizza price: "))
                response = requests.post(
                    "http://localhost:8000/menu",
                    json={"name": pizza_name, "price": pizza_price},
                    headers={"Admin-Token": token},timeout=10
                )
                if response.status_code == 201:
                    print(response.json()["message"])
                else:
                    print(response.json()["error"])
            except ValueError:
                print("Invalid price. Please try again.")

        elif choice == "2":
            pizza_id = input("Enter the ID of the pizza to delete: ").strip()
            response = requests.delete(
                f"http://localhost:8000/menu/{pizza_id}",
                headers={"Admin-Token": token},timeout=10
            )
            if response.status_code == 200:
                print(response.json()["message"])
            else:
                print(response.json()["error"])

        elif choice == "3":
            order_id = input("Enter the ID of the order to cancel: ").strip()
            response = requests.delete(
                f"http://localhost:8000/order/{order_id}",
                headers={"Admin-Token": token},timeout=10
            )
            if response.status_code == 200:
                print(response.json()["message"])
            else:
                print(response.json()["error"])

        elif choice == "4":
            token = manager.generate_token()
            print(f"Your new admin token is: {token}")
            print("Please save this token securely. It will expire in 24 hours.")

        elif choice == "5":
            print("Exiting Admin Panel.")
            break
        else:
            print("Invalid option. Please try again.")

def cli_interface(args):
    """Cli interface"""
    if args.register:
        register_user()
    elif args.login:
        login_user()
    elif args.logout:
        logout_user()
    elif args.whoami:
        check_current_user()
    elif args.menu:
        list_menu()
    elif args.create:
        create_order()
    elif args.status:
        check_order_status()
    elif args.cancel:
        cancel_order()
    elif args.admin:
        admin_panel()
    elif args.commands:
        print("\n--- Commands ---")
        print("--register: Register a new user account")
        print("--login: Login to your account")
        print("--logout: Logout from your account")
        print("--whoami: Check who is currently logged in")
        print("--menu: List the pizza menu")
        print("--create: Create a new order")
        print("--status: Check the status of an order")
        print("--cancel: Cancel an order")
        print("--server: Run the HTTP server")
        print("--admin: Access the admin panel")
    else:
        print("Invalid option. Use --commands to see available commands.")

def run_server():
    """Running server"""
    server = HTTPServer(('localhost', 8000), PizzaServer)
    print("Server running on port 8000...")
    server.serve_forever()

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Pizza Ordering CLI System")
    parser.add_argument("--register", action="store_true", help="Register a new user account")
    parser.add_argument("--login", action="store_true", help="Login to your account")
    parser.add_argument("--logout", action="store_true", help="Logout from your account")
    parser.add_argument("--whoami", action="store_true", help="Check who is currently logged in")
    parser.add_argument("--menu", action="store_true", help="List the pizza menu")
    parser.add_argument("--create", action="store_true", help="Create a new order")
    parser.add_argument("--status", action="store_true", help="Check the status of an order")
    parser.add_argument("--cancel", action="store_true", help="Cancel an order")
    parser.add_argument("--server", action="store_true", help="Run the HTTP server")
    parser.add_argument("--admin", action="store_true", help="Access the admin panel")
    parser.add_argument("--commands", action="store_true", help="Show all available commands")

    args = parser.parse_args()

    if args.server:
        run_server()
    else:
        cli_interface(args)

if __name__ == "__main__":
    main()