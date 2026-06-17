import email
import json
import os
import random
import re
import smtplib
import uuid
from datetime import datetime, timedelta
from email.message import EmailMessage
from pathlib import Path

from flask import Flask, flash, make_response, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash


app = Flask(__name__)
app.config["SECRET_KEY"] = "change-this-secret-key"

DATA_DIR = Path("data")
DATA_FILE = DATA_DIR / "ecommerce_data.json"
UPLOAD_DIR = Path("static/products/uploads")

def get_product_image_path(name="", category=""):
    name_lower = (name or "").lower()
    category_lower = (category or "").lower()

    if any(keyword in name_lower for keyword in ("smartphone", "mobile", "phone")):
        return "products/mobile.svg"
    if "router" in name_lower or "wifi" in name_lower:
        return "products/router.svg"
    if "speaker" in name_lower:
        return "products/speaker.svg"
    if any(keyword in name_lower for keyword in ("earbud", "headphone")):
        return "products/earbuds.svg"
    if "backpack" in name_lower:
        return "products/backpack.svg"
    if any(keyword in name_lower for keyword in ("tv", "television")):
        return "products/tv.svg"
    if "chair" in name_lower:
        return "products/chair.svg"
    if any(keyword in name_lower for keyword in ("shoe", "sneaker", "sport")):
        return "products/shoes.svg"
    if category_lower == "fashion":
        return "products/shoes.svg"
    if category_lower == "accessories":
        return "products/backpack.svg"
    return "products/generic.svg"


def get_product_image_paths(name="", category=""):
    image = get_product_image_path(name, category)
    return [image]


def get_product_image_urls(name="", category=""):
    name_lower = (name or "").lower()
    if any(keyword in name_lower for keyword in ("smartphone", "mobile", "phone")):
        return ["https://images.unsplash.com/photo-1511707171634-5f897ff02aa9?auto=format&fit=crop&w=900&q=80"]
    if "router" in name_lower or "wifi" in name_lower:
        return ["https://images.unsplash.com/photo-1516321497487-e288fb19713f?auto=format&fit=crop&w=900&q=80"]
    if "speaker" in name_lower:
        return ["https://images.unsplash.com/photo-1518444065439-e933c06ce9cd?auto=format&fit=crop&w=900&q=80"]
    if any(keyword in name_lower for keyword in ("earbud", "headphone")):
        return ["https://images.unsplash.com/photo-1491926626787-62db157af940?auto=format&fit=crop&w=900&q=80"]
    if "backpack" in name_lower:
        return ["https://images.unsplash.com/photo-1542291026-7eec264c27ff?auto=format&fit=crop&w=900&q=80"]
    if any(keyword in name_lower for keyword in ("tv", "television")):
        return ["https://images.unsplash.com/photo-1593359677879-a4bb92f829d1?auto=format&fit=crop&w=900&q=80"]
    if "chair" in name_lower:
        return ["https://images.unsplash.com/photo-1519947486511-46149fa0a254?auto=format&fit=crop&w=900&q=80"]
    if any(keyword in name_lower for keyword in ("shoe", "sneaker", "sport")):
        return ["https://images.unsplash.com/photo-1525966222134-fcfa99b8ae77?auto=format&fit=crop&w=900&q=80"]
    if category.lower() == "fashion":
        return ["https://images.unsplash.com/photo-1525966222134-fcfa99b8ae77?auto=format&fit=crop&w=900&q=80"]
    if category.lower() == "accessories":
        return ["https://images.unsplash.com/photo-1526170375885-4d8ecf77b99f?auto=format&fit=crop&w=900&q=80"]
    return ["https://images.unsplash.com/photo-1512436991641-6745cdb1723f?auto=format&fit=crop&w=900&q=80"]


def get_product_reviews(name="", category=""):
    return [
        "⭐ 4.8/5 — Customers love the quality and quick delivery.",
        "⭐ 4.7/5 — Reliable seller and premium packaging.",
        "⭐ 4.9/5 — Great value for money and easy returns.",
    ]


SEARCH_KEYWORDS = {
    "mobile": ["mobile", "mobiles", "moblie", "moblile", "phone", "phones", "smartphone", "smartphones", "cellphone", "cell"],
    "router": ["router", "wifi", "wi fi", "wireless", "internet"],
    "earbud": ["earbud", "earbuds", "headphone", "headphones", "earphone", "earphones"],
    "backpack": ["backpack", "bag", "laptop bag", "travel bag"],
    "tv": ["tv", "television", "led tv", "smart tv", "display"],
    "chair": ["chair", "office chair", "gaming chair"],
    "shoe": ["shoe", "shoes", "sneaker", "sneakers", "sports shoe", "sports shoes"],
    "speaker": ["speaker", "bluetooth speaker", "audio"],
}


def normalize_search_text(text):
    return " ".join((text or "").lower().replace("-", " ").replace("_", " ").replace("/", " ").replace("&", " ").split())


def product_matches_search(product, query):
    normalized_query = normalize_search_text(query)
    if not normalized_query:
        return True

    searchable_text = normalize_search_text(" ".join([
        product.get("name", ""),
        product.get("category", ""),
        product.get("seller", ""),
        product.get("description", ""),
    ]))

    if normalized_query in searchable_text:
        return True

    for _, aliases in SEARCH_KEYWORDS.items():
        if normalized_query in aliases or any(term in normalized_query for term in aliases):
            if any(alias in searchable_text for alias in aliases):
                return True

    return False


def password_meets_rules(password):
    return (
        len(password) >= 8
        and any(char.isupper() for char in password)
        and any(char.islower() for char in password)
        and any(char.isdigit() for char in password)
        and any(not char.isalnum() for char in password)
    )
def is_valid_email(email):
    pattern = r'^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'
    return re.match(pattern, email) is not None


def generate_tracking_snapshot(order_number):
    random.seed(order_number)
    stages = [
        ("Order placed", "Payment confirmed and your order is ready for packing."),
        ("Packed", "Items are packed with care and labelled for dispatch."),
        ("Shipped", "Your parcel has left the warehouse and is on its way to a hub."),
        ("Out for delivery", "A delivery partner is now preparing your route."),
    ]
    active_index = random.randint(0, len(stages) - 1)
    timeline = []
    for index, (label, detail) in enumerate(stages):
        timeline.append({
            "label": label,
            "detail": detail,
            "done": index <= active_index,
            "current": index == active_index,
        })
    return {
        "tracking_code": f"TRK-{uuid.uuid4().hex[:8].upper()}",
        "timeline": timeline,
    }


SAMPLE_PRODUCTS = [
    {
        "name": "5G Smartphone",
        "category": "Electronics",
        "seller": "Reliance Digital",
        "price": "14999",
        "quantity": "35",
        "description": "Fast 5G phone with bright display, long battery life, and dual camera.",
        "image_path": get_product_image_path("5G Smartphone", "Electronics"),
        "image_paths": get_product_image_paths("5G Smartphone", "Electronics"),
        "image_urls": get_product_image_urls("5G Smartphone", "Electronics"),
        "reviews": get_product_reviews("5G Smartphone", "Electronics"),
    },
    {
        "name": "JioFiber Router",
        "category": "Electronics",
        "seller": "Jio Store",
        "price": "2499",
        "quantity": "18",
        "description": "High speed Wi-Fi router for home internet and streaming.",
        "image_path": get_product_image_path("JioFiber Router", "Electronics"),
        "image_paths": get_product_image_paths("JioFiber Router", "Electronics"),
        "image_urls": get_product_image_urls("JioFiber Router", "Electronics"),
        "reviews": get_product_reviews("JioFiber Router", "Electronics"),
    },
    {
        "name": "Wireless Earbuds",
        "category": "Electronics",
        "seller": "Croma",
        "price": "1799",
        "quantity": "42",
        "description": "Compact earbuds with clear sound and charging case.",
        "image_path": get_product_image_path("Wireless Earbuds", "Electronics"),
        "image_paths": get_product_image_paths("Wireless Earbuds", "Electronics"),
        "image_urls": get_product_image_urls("Wireless Earbuds", "Electronics"),
        "reviews": get_product_reviews("Wireless Earbuds", "Electronics"),
    },
    {
        "name": "Laptop Backpack",
        "category": "Accessories",
        "seller": "JioMart",
        "price": "899",
        "quantity": "60",
        "description": "Water-resistant backpack with padded laptop storage.",
        "image_path": get_product_image_path("Laptop Backpack", "Accessories"),
        "image_paths": get_product_image_paths("Laptop Backpack", "Accessories"),
        "image_urls": get_product_image_urls("Laptop Backpack", "Accessories"),
        "reviews": get_product_reviews("Laptop Backpack", "Accessories"),
    },
    {
        "name": "LED Smart TV",
        "category": "Electronics",
        "seller": "Vijay Sales",
        "price": "28999",
        "quantity": "12",
        "description": "Full HD smart TV with built-in apps and slim design.",
        "image_path": get_product_image_path("LED Smart TV", "Electronics"),
        "image_paths": get_product_image_paths("LED Smart TV", "Electronics"),
        "image_urls": get_product_image_urls("LED Smart TV", "Electronics"),
        "reviews": get_product_reviews("LED Smart TV", "Electronics"),
    },
    {
        "name": "Bluetooth Speaker",
        "category": "Electronics",
        "seller": "Reliance Digital",
        "price": "1299",
        "quantity": "28",
        "description": "Portable speaker with punchy sound and all-day battery.",
        "image_path": get_product_image_path("Bluetooth Speaker", "Electronics"),
        "image_paths": get_product_image_paths("Bluetooth Speaker", "Electronics"),
        "image_urls": get_product_image_urls("Bluetooth Speaker", "Electronics"),
        "reviews": get_product_reviews("Bluetooth Speaker", "Electronics"),
    },
    {
        "name": "Office Chair",
        "category": "Home",
        "seller": "Urban Ladder",
        "price": "5499",
        "quantity": "14",
        "description": "Ergonomic chair for study rooms and home offices.",
        "image_path": get_product_image_path("Office Chair", "Home"),
        "image_paths": get_product_image_paths("Office Chair", "Home"),
        "image_urls": get_product_image_urls("Office Chair", "Home"),
        "reviews": get_product_reviews("Office Chair", "Home"),
    },
    {
        "name": "Sports Shoes",
        "category": "Fashion",
        "seller": "E buy Fashion",
        "price": "2199",
        "quantity": "33",
        "description": "Lightweight running shoes for daily comfort.",
        "image_path": get_product_image_path("Sports Shoes", "Fashion"),
        "image_paths": get_product_image_paths("Sports Shoes", "Fashion"),
        "image_urls": get_product_image_urls("Sports Shoes", "Fashion"),
        "reviews": get_product_reviews("Sports Shoes", "Fashion"),
    },
]


def ensure_database():
    DATA_DIR.mkdir(exist_ok=True)
    UPLOAD_DIR.mkdir(exist_ok=True, parents=True)
    if not DATA_FILE.exists():
        save_database({"users": []})


def save_uploaded_image(file_storage):
    if not file_storage or not file_storage.filename:
        return None

    allowed_extensions = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg"}
    suffix = Path(file_storage.filename).suffix.lower()
    if suffix not in allowed_extensions:
        return None

    filename = f"{uuid.uuid4().hex}{suffix}"
    save_path = UPLOAD_DIR / filename
    file_storage.save(save_path)
    return f"products/uploads/{filename}"


def save_uploaded_images(files_storage):
    paths = []
    for file_storage in files_storage:
        path = save_uploaded_image(file_storage)
        if path:
            paths.append(path)
    return paths


def ensure_data_schema(data):
    data.setdefault("orders", [])
    data.setdefault("email_outbox", [])
    data.setdefault("platform_credits", 0)
    for user in data.get("users", []):
        user.setdefault("credits", 100000 if user.get("role") == "buyer" else 0)
    return data


def load_database():
    ensure_database()
    with DATA_FILE.open("r", encoding="utf-8") as file:
        data = json.load(file)
    return ensure_data_schema(data)


def save_database(data):
    DATA_DIR.mkdir(exist_ok=True)
    data = ensure_data_schema(data)
    with DATA_FILE.open("w", encoding="utf-8") as file:
        json.dump(data, file, indent=4)
    return data


def find_user(username):
    data = load_database()
    username = username.lower().strip()
    return next(
        (user for user in data["users"] if user["username"].lower() == username),
        None,
    )


def email_exists(email):
    data = load_database()
    email = email.lower().strip()
    return any(user["email"].lower() == email for user in data["users"])


def can_access_buyer_mode(user=None):
    if user is None:
        username = session.get("username")
        user = find_user(username) if username else None
    return bool(user and (user.get("role") == "buyer" or session.get("buyer_mode", False)))


def get_supplier_products():
    data = load_database()
    products = []

    for supplier in data["users"]:
        if supplier.get("role") != "supplier" or "item" not in supplier:
            continue

        item = supplier["item"]
        products.append(
            {
                "name": item["name"],
                "category": "Supplier Item",
                "seller": supplier["full_name"],
                "price": item["price"],
                "quantity": item["quantity"],
                "description": item["description"],
                "image_path": item.get("image_path") or get_product_image_path(item.get("name", ""), "Supplier Item"),
                "image_paths": item.get("image_paths") or [item.get("image_path") or get_product_image_path(item.get("name", ""), "Supplier Item")],
                "image_urls": item.get("image_paths") or [item.get("image_path") or get_product_image_path(item.get("name", ""), "Supplier Item")],
                "reviews": get_product_reviews(item.get("name", ""), "Supplier Item"),
                "seller_username": supplier.get("username"),
            }
        )

    return products


@app.route("/")
def home():
    return render_template("register.html")


@app.route("/register/buyer")
def buyer_registration():
    return render_template("buyer_register.html")


@app.route("/register/supplier")
def supplier_registration():
    return render_template("supplier_register.html")


@app.route("/register", methods=["POST"])
def register():
    role = request.form.get("role", "").strip()
    full_name = request.form.get("full_name", "").strip()
    username = request.form.get("username", "").strip()
    email = request.form.get("email", "").strip()
    phone = request.form.get("phone", "").strip()
    address = request.form.get("address", "").strip()
    password = request.form.get("password", "")

    if role not in {"buyer", "supplier"}:
        flash("Please choose whether you are registering as a buyer or supplier.", "error")
        return redirect(url_for("home"))

    registration_page = "buyer_registration" if role == "buyer" else "supplier_registration"

    required_fields = [full_name, username, email, phone, address, password]
    if not all(required_fields):
        flash("Please complete all required registration fields.", "error")
        return redirect(url_for(registration_page))
    
    if not phone.isdigit() or len(phone) != 10:
        flash("Phone number must contain exactly 10 digits and no special characters.", "error")
        return redirect(url_for(registration_page))
    
    if not password_meets_rules(password):
        flash("Password must be at least 8 characters with uppercase, lowercase, a number, and a symbol.", "error")
        return redirect(url_for(registration_page))

    if find_user(username):
        flash("That username is already taken. Please choose another one.", "error")
        return redirect(url_for(registration_page))

    if not is_valid_email(email):
        flash("Please enter a valid email address.", "error")
        return redirect(url_for(registration_page))

    if email_exists(email):
        flash("An account already exists with that email address.", "error")
        return redirect(url_for(registration_page))

    user = {
        "role": role,
        "full_name": full_name,
        "username": username,
        "email": email,
        "phone": phone,
        "address": address,
        "password_hash": generate_password_hash(password),
        "credits": 100000 if role == "buyer" else 0,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }

    if role == "supplier":
        user["item"] = {
            "name": "",
            "description": "",
            "price": "",
            "quantity": "",
            "image_paths": [],
            "image_path": "products/generic.svg",
        }

    data = load_database()
    data["users"].append(user)
    save_database(data)

    flash("Registration successful. You can now log in with your username and password.", "success")
    return redirect(url_for("home"))


@app.route("/login", methods=["POST"])
def login():
    username = request.form.get("login_username", "").strip()
    password = request.form.get("login_password", "")

    if not username or not password:
        flash("Please enter atleast username and password to log in.", "error")
        return redirect(url_for("home"))

    user = find_user(username)
    if not user or not check_password_hash(user["password_hash"], password):
        flash("Invalid username or password. Please check your details one more time and try again.", "error")
        return redirect(url_for("home"))

    session["username"] = user["username"]
    flash(f"Welcome back, {user['full_name']}!", "success")
    return redirect(url_for("dashboard"))


@app.route("/toggle-buyer-mode")
def toggle_buyer_mode():
    if "username" not in session:
        flash("Please log in first to switch shopping mode.", "error")
        return redirect(url_for("home"))

    user = find_user(session["username"])
    if not user:
        flash("Your session could not be found. Please log in again.", "error")
        return redirect(url_for("home"))

    session["buyer_mode"] = not session.get("buyer_mode", False)
    if session["buyer_mode"]:
        flash("Shopping mode enabled. You can browse products and place orders as a buyer.", "success")
    else:
        flash("Seller dashboard restored.", "success")
    return redirect(url_for("dashboard"))


@app.route("/dashboard")
def dashboard():
    username = session.get("username")
    if not username:
        flash("Please log in first to view your dashboard.", "error")
        return redirect(url_for("home"))

    user = find_user(username)
    if not user:
        session.clear()
        flash("Your session could not be found. Please log in again.", "error")
        return redirect(url_for("home"))

    products = []
    cart_items = session.get("cart", [])
    buyer_mode = can_access_buyer_mode(user)
    if buyer_mode:
        products = SAMPLE_PRODUCTS + get_supplier_products()
        search_query = (request.args.get("search", "") or "").strip().lower()
        if search_query:
            products = [product for product in products if product_matches_search(product, search_query)]
    else:
        products = []

    return render_template(
        "dashboard.html",
        user=user,
        products=products,
        cart_items=cart_items,
        search_query=(request.args.get("search", "") or ""),
        buyer_mode=buyer_mode,
    )


@app.route("/supplier/list-product", methods=["GET", "POST"])
def list_product():
    if "username" not in session:
        flash("Please log in as a supplier before listing a product.", "error")
        return redirect(url_for("home"))

    user = find_user(session["username"])
    if not user or user.get("role") != "supplier":
        flash("Only suppliers can list products.", "error")
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        item_name = request.form.get("item_name", "").strip()
        item_description = request.form.get("item_description", "").strip()
        item_price = request.form.get("item_price", "").strip()
        item_quantity = request.form.get("item_quantity", "").strip()
        uploaded_files = request.files.getlist("item_images")

        if not all([item_name, item_description, item_price, item_quantity]):
            flash("Please complete all item fields.", "error")
            return redirect(url_for("list_product"))

        image_paths = save_uploaded_images(uploaded_files)
        if len(image_paths) < 2:
            flash("Please upload at least 2 product images.", "error")
            return redirect(url_for("list_product"))

        data = load_database()
        current_user = next((entry for entry in data["users"] if entry.get("username") == user["username"]), None)
        if current_user is None:
            flash("Your account could not be found.", "error")
            return redirect(url_for("dashboard"))

        current_user["item"] = {
            "name": item_name,
            "description": item_description,
            "price": item_price,
            "quantity": item_quantity,
            "image_paths": image_paths,
            "image_path": image_paths[0],
        }
        save_database(data)

        flash("Your product has been listed successfully.", "success")
        return redirect(url_for("dashboard"))

    return render_template("supplier_list_product.html", user=user)


@app.route("/cart")
def cart():
    products = SAMPLE_PRODUCTS + get_supplier_products()
    cart_items = session.get("cart", [])
    return render_template("cart.html", products=products, cart_items=cart_items)


@app.route("/cart/add/<int:item_index>")
def add_to_cart(item_index):
    products = SAMPLE_PRODUCTS + get_supplier_products()
    if 0 <= item_index < len(products):
        product = products[item_index].copy()
        cart = session.get("cart", [])
        cart.append(product)
        session["cart"] = cart
        flash("Product added to your cart.", "success")
    else:
        flash("That product could not be found.", "error")
    return redirect(url_for("dashboard"))


def build_order_confirmation_email(buyer, order):
    item_lines = []
    for index, item in enumerate(order.get("items", []), start=1):
        item_lines.append(
            "\n".join([
                f"{index}. {item.get('name', 'Item')}",
                f"   Price: Rs. {item.get('price', 0)}",
                f"   Seller: {item.get('seller', 'E buy seller')}",
                f"   Category: {item.get('category', 'General')}",
                f"   Description: {item.get('description', 'No description provided')}",
            ])
        )

    items_text = "\n".join(item_lines) if item_lines else "- Your ordered items"
    subject = f"E buy order confirmation: {order['order_number']}"
    body = f"""Hello {buyer.get('full_name', 'Buyer')},

Thank you for shopping with E buy. Your order has been confirmed.

Order details
Order number: {order['order_number']}
Placed on: {order.get('created_at', 'Just now')}
Status: {order['status']}
Expected delivery: {order['expected_delivery']}

Buyer details
Name: {buyer.get('full_name', 'Buyer')}
Email: {buyer.get('email', 'Not provided')}
Phone: {buyer.get('phone', 'Not provided')}
Delivery address: {buyer.get('address', 'Not provided')}

Payment details
Items total: Rs. {order['total']}
Platform fee: Rs. {order.get('platform_fee', 0)}
Seller payout: Rs. {order.get('seller_share', 0)}
Amount paid: Rs. {order['total']}

Items:
{items_text}

You can open your E buy orders page to track this order.
"""
    return subject, body


def send_order_confirmation_email(buyer, order, data):
    recipient = buyer.get("email")
    subject, body = build_order_confirmation_email(buyer, order)
    email_record = {
        "to": recipient,
        "subject": subject,
        "body": body,
        "order_number": order["order_number"],
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }

    smtp_host = os.getenv("SMTP_HOST")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_username = os.getenv("SMTP_USERNAME")
    smtp_password = os.getenv("SMTP_PASSWORD")
    sender = os.getenv("SMTP_SENDER") or smtp_username

    if not smtp_host or not sender or not recipient:
        email_record["status"] = "queued"
        data.setdefault("email_outbox", []).append(email_record)
        return "queued"

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = sender
    message["To"] = recipient
    message.set_content(body)

    try:
        if os.getenv("SMTP_USE_SSL", "").lower() in {"1", "true", "yes"}:
            with smtplib.SMTP_SSL(smtp_host, smtp_port) as smtp:
                if smtp_username and smtp_password:
                    smtp.login(smtp_username, smtp_password)
                smtp.send_message(message)
        else:
            with smtplib.SMTP(smtp_host, smtp_port) as smtp:
                if os.getenv("SMTP_STARTTLS", "true").lower() not in {"0", "false", "no"}:
                    smtp.starttls()
                if smtp_username and smtp_password:
                    smtp.login(smtp_username, smtp_password)
                smtp.send_message(message)
    except (OSError, smtplib.SMTPException) as error:
        email_record["status"] = "failed"
        email_record["error"] = str(error)
        data.setdefault("email_outbox", []).append(email_record)
        return "failed"

    email_record["status"] = "sent"
    data.setdefault("email_outbox", []).append(email_record)
    return "sent"


def place_order_from_cart():
    if "username" not in session:
        flash("Please log in to place an order.", "error")
        return redirect(url_for("home"))

    buyer = find_user(session["username"])
    if not can_access_buyer_mode(buyer):
        flash("Only buyers can place orders.", "error")
        return redirect(url_for("dashboard"))

    cart_items = session.get("cart", [])
    if not cart_items:
        flash("Your cart is empty.", "error")
        return redirect(url_for("cart"))

    total_cost = 0.0
    for product in cart_items:
        try:
            total_cost += float(product.get("price", 0) or 0)
        except (TypeError, ValueError):
            continue

    data = load_database()
    buyer_record = next((entry for entry in data["users"] if entry.get("username") == buyer["username"]), None)
    if buyer_record is None:
        flash("Your account could not be found.", "error")
        return redirect(url_for("home"))

    if buyer_record.get("credits", 0) < total_cost:
        flash("You do not have enough credits to place this order.", "error")
        return redirect(url_for("recharge"))

    platform_fee = round(total_cost * 0.10, 2)
    seller_share = round(total_cost - platform_fee, 2)

    for product in cart_items:
        seller_username = product.get("seller_username")
        seller_record = next((entry for entry in data["users"] if entry.get("username") == seller_username), None) if seller_username else None
        if seller_record is not None:
            available_quantity = int(seller_record.get("item", {}).get("quantity", 0) or 0)
            if available_quantity <= 0:
                flash("One or more items in your cart are out of stock. Please update your cart.", "error")
                return redirect(url_for("cart"))
            seller_record["item"]["quantity"] = available_quantity - 1
            seller_record["credits"] = seller_record.get("credits", 0) + seller_share / len(cart_items)

    data["platform_credits"] = data.get("platform_credits", 0) + platform_fee
    buyer_record["credits"] = round(buyer_record.get("credits", 0) - total_cost, 2)

    order_number = f"ORD-{datetime.now().strftime('%Y%m%d%H%M%S')}-{len(data.get('orders', [])) + 1}"
    expected_delivery = (datetime.now() + timedelta(days=5)).strftime("%d %b %Y")
    order = {
        "order_number": order_number,
        "buyer": buyer_record["username"],
        "items": cart_items,
        "total": round(total_cost, 2),
        "platform_fee": round(platform_fee, 2),
        "seller_share": round(seller_share, 2),
        "expected_delivery": expected_delivery,
        "status": "Placed",
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    data.setdefault("orders", []).append(order)
    email_status = send_order_confirmation_email(buyer_record, order, data)

    save_database(data)
    session["cart"] = []

    if email_status == "sent":
        flash(f"Order placed successfully. A confirmation email was sent to {buyer_record['email']}. Expected delivery: {expected_delivery}", "success")
    elif email_status == "queued":
        flash(f"Order placed successfully. Confirmation email queued for {buyer_record['email']}. Expected delivery: {expected_delivery}", "success")
    else:
        flash(f"Order placed successfully, but confirmation email could not be sent. Expected delivery: {expected_delivery}", "success")
    return redirect(url_for("orders"))


@app.route("/checkout", methods=["GET", "POST"])
def checkout():
    if "username" not in session:
        flash("Please log in to place an order.", "error")
        return redirect(url_for("home"))

    buyer = find_user(session["username"])
    if not can_access_buyer_mode(buyer):
        flash("Only buyers can place orders.", "error")
        return redirect(url_for("dashboard"))

    cart_items = session.get("cart", [])
    if not cart_items:
        flash("Your cart is empty.", "error")
        return redirect(url_for("cart"))

    total_cost = 0.0
    for product in cart_items:
        try:
            total_cost += float(product.get("price", 0) or 0)
        except (TypeError, ValueError):
            continue

    if request.method == "GET":
        response = make_response(render_template("checkout.html", buyer=buyer, cart_items=cart_items, total_cost=round(total_cost, 2)))
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response

    return place_order_from_cart()


@app.route("/buy/<int:item_index>")
def buy_now(item_index):
    products = SAMPLE_PRODUCTS + get_supplier_products()
    if not 0 <= item_index < len(products):
        flash("That product could not be found.", "error")
        return redirect(url_for("dashboard"))

    session["cart"] = [products[item_index].copy()]
    return redirect(url_for("checkout"))


@app.route("/recharge", methods=["GET", "POST"])
def recharge():
    if "username" not in session:
        flash("Please log in to recharge your wallet.", "error")
        return redirect(url_for("home"))

    if request.method == "POST":
        card_number = request.form.get("card_number", "").strip()
        card_holder = request.form.get("card_holder", "").strip()
        cvv = request.form.get("cvv", "").strip()
        amount = request.form.get("amount", "0").strip()

        if not all([card_number, card_holder, cvv, amount]) or len(card_number) < 12 or len(cvv) < 3:
            flash("Please enter valid card details and an amount to recharge.", "error")
            return redirect(url_for("recharge"))

        try:
            amount_value = float(amount)
        except ValueError:
            flash("Please enter a valid recharge amount.", "error")
            return redirect(url_for("recharge"))

        if amount_value <= 0:
            flash("Please enter a positive amount to recharge your wallet.", "error")
            return redirect(url_for("recharge"))

        data = load_database()
        buyer = next((entry for entry in data["users"] if entry.get("username") == session["username"]), None)
        if not buyer:
            flash("Your account could not be found.", "error")
            return redirect(url_for("home"))

        buyer["credits"] = round(buyer.get("credits", 0) + amount_value, 2)
        save_database(data)
        flash("Wallet recharged successfully. Your credits are ready to use.", "success")
        return redirect(url_for("dashboard"))

    return render_template("recharge.html")


@app.route("/orders")
def orders():
    if "username" not in session:
        flash("Please log in to view your orders.", "error")
        return redirect(url_for("home"))

    data = load_database()
    user_orders = []
    for order in data.get("orders", []):
        if order.get("buyer") == session["username"]:
            snapshot = generate_tracking_snapshot(order.get("order_number", ""))
            enriched = dict(order)
            enriched["tracking"] = snapshot
            user_orders.append(enriched)
    response = make_response(render_template("orders.html", orders=user_orders))
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out successfully.", "success")
    return redirect(url_for("home"))


if __name__ == "__main__":
    ensure_database()
    app.run(debug=True)
