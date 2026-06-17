from fastmcp import FastMCP

from app import (
    SAMPLE_PRODUCTS,
    get_supplier_products,
    product_matches_search,
    load_database,
    save_database,
    find_user
)

mcp = FastMCP("EBuy Assistant")


# ==========================================================
# PRODUCTS
# ==========================================================

@mcp.tool()
def list_products():
    """Return all platform and supplier products"""
    return SAMPLE_PRODUCTS + get_supplier_products()


@mcp.tool()
def search_products(query: str):
    """Search products by keyword"""

    products = SAMPLE_PRODUCTS + get_supplier_products()

    return [
        product
        for product in products
        if product_matches_search(product, query)
    ]

@mcp.tool()
def delete_user(username: str):
    """Delete a user by username"""

    data = load_database()

    original_count = len(data["users"])

    data["users"] = [
        user
        for user in data["users"]
        if user["username"] != username
    ]

    if len(data["users"]) == original_count:
        return {
            "success": False,
            "message": "User not found"
        }

    save_database(data)

    return {
        "success": True,
        "message": f"User '{username}' deleted"
    }

# ==========================================================
# ADVANCED USER MANAGEMENT
# ==========================================================

@mcp.tool()
def create_user(
    username: str,
    full_name: str,
    email: str,
    role: str = "buyer"
):
    """Create a new user"""

    data = load_database()

    existing = next(
        (u for u in data["users"] if u["username"] == username),
        None
    )

    if existing:
        return {
            "success": False,
            "message": "Username already exists"
        }

    new_user = {
        "role": role,
        "full_name": full_name,
        "username": username,
        "email": email,
        "phone": "",
        "address": "",
        "credits": 100000
    }

    data["users"].append(new_user)

    save_database(data)

    return {
        "success": True,
        "username": username
    }


@mcp.tool()
def delete_user(username: str):
    """Delete a user"""

    data = load_database()

    original = len(data["users"])

    data["users"] = [
        u for u in data["users"]
        if u["username"] != username
    ]

    if len(data["users"]) == original:
        return {
            "success": False,
            "message": "User not found"
        }

    save_database(data)

    return {
        "success": True,
        "message": f"{username} deleted"
    }


@mcp.tool()
def update_user_email(
    username: str,
    email: str
):
    """Update user email"""

    data = load_database()

    for user in data["users"]:

        if user["username"] == username:

            user["email"] = email

            save_database(data)

            return {
                "success": True,
                "email": email
            }

    return {
        "success": False,
        "message": "User not found"
    }


@mcp.tool()
def reset_wallet(username: str):
    """Reset wallet to default"""

    data = load_database()

    for user in data["users"]:

        if user["username"] == username:

            user["credits"] = 100000

            save_database(data)

            return {
                "success": True,
                "credits": 100000
            }

    return {
        "success": False
    }


# ==========================================================
# PRODUCT MANAGEMENT
# ==========================================================

@mcp.tool()
def add_product(
    supplier_username: str,
    name: str,
    description: str,
    price: float,
    quantity: int
):
    """Add supplier product"""

    data = load_database()

    supplier = next(
        (
            u for u in data["users"]
            if u["username"] == supplier_username
        ),
        None
    )

    if not supplier:
        return {
            "success": False,
            "message": "Supplier not found"
        }

    supplier["item"] = {
        "name": name,
        "description": description,
        "price": str(price),
        "quantity": quantity
    }

    save_database(data)

    return {
        "success": True,
        "product": name
    }


@mcp.tool()
def delete_product(
    supplier_username: str
):
    """Delete supplier product"""

    data = load_database()

    supplier = next(
        (
            u for u in data["users"]
            if u["username"] == supplier_username
        ),
        None
    )

    if not supplier:
        return {
            "success": False
        }

    supplier.pop("item", None)

    save_database(data)

    return {
        "success": True
    }


@mcp.tool()
def update_product_price(
    supplier_username: str,
    price: float
):
    """Update product price"""

    data = load_database()

    for user in data["users"]:

        if (
            user["username"] == supplier_username
            and "item" in user
        ):

            user["item"]["price"] = str(price)

            save_database(data)

            return {
                "success": True,
                "price": price
            }

    return {
        "success": False
    }


@mcp.tool()
def restock_product(
    supplier_username: str,
    amount: int
):
    """Increase stock"""

    data = load_database()

    for user in data["users"]:

        if (
            user["username"] == supplier_username
            and "item" in user
        ):

            current = int(
                user["item"].get("quantity", 0)
            )

            user["item"]["quantity"] = current + amount

            save_database(data)

            return {
                "success": True,
                "new_quantity":
                user["item"]["quantity"]
            }

    return {
        "success": False
    }

@mcp.tool()
def cancel_order(order_number: str):
    """Cancel order"""

    data = load_database()

    for order in data["orders"]:

        if order["order_number"] == order_number:

            order["status"] = "Cancelled"

            save_database(data)

            return {
                "success": True
            }

    return {
        "success": False
    }


@mcp.tool()
def update_order_status(
    order_number: str,
    status: str
):
    """Update order status"""

    data = load_database()

    for order in data["orders"]:

        if order["order_number"] == order_number:

            order["status"] = status

            save_database(data)

            return {
                "success": True,
                "status": status
            }

    return {
        "success": False
    }


# ==========================================================
# ANALYTICS
# ==========================================================

@mcp.tool()
def revenue_report():
    """Revenue summary"""

    data = load_database()

    total_sales = sum(
        float(order.get("total", 0))
        for order in data["orders"]
    )

    return {
        "orders": len(data["orders"]),
        "sales": round(total_sales, 2),
        "platform_credits":
        data.get("platform_credits", 0)
    }


@mcp.tool()
def database_summary():
    """Database overview"""

    data = load_database()

    return {
        "users": len(data["users"]),
        "orders": len(data["orders"]),
        "emails":
        len(data.get("email_outbox", [])),
        "platform_credits":
        data.get("platform_credits", 0)
    }

@mcp.tool()
def supplier_inventory():
    """Show all supplier inventory"""

    data = load_database()

    inventory = []

    for user in data["users"]:

        if user.get("role") != "supplier":
            continue

        item = user.get("item", {})

        inventory.append({
            "supplier": user["username"],
            "product": item.get("name"),
            "description": item.get("description"),
            "price": item.get("price"),
            "quantity": item.get("quantity")
        })

    return inventory


@mcp.tool()
def low_stock_products(threshold: int = 5):
    """Products below stock threshold"""

    data = load_database()

    result = []

    for user in data["users"]:

        if user.get("role") != "supplier":
            continue

        item = user.get("item", {})

        try:
            quantity = int(item.get("quantity", 0))
        except:
            quantity = 0

        if quantity <= threshold:

            result.append({
                "supplier": user["username"],
                "product": item.get("name"),
                "quantity": quantity
            })

    return result


# ==========================================================
# USERS
# ==========================================================

@mcp.tool()
def list_users():
    """List all users"""

    data = load_database()

    return [
        {
            "username": user["username"],
            "full_name": user["full_name"],
            "role": user["role"],
            "email": user["email"],
            "credits": user.get("credits", 0)
        }
        for user in data["users"]
    ]


@mcp.tool()
def get_user(username: str):
    """Get a single user"""

    user = find_user(username)

    if not user:
        return {"error": "User not found"}

    return user


@mcp.tool()
def list_buyers():
    """List all buyers"""

    data = load_database()

    return [
        user
        for user in data["users"]
        if user["role"] == "buyer"
    ]


@mcp.tool()
def list_suppliers():
    """List all suppliers"""

    data = load_database()

    return [
        user
        for user in data["users"]
        if user["role"] == "supplier"
    ]


@mcp.tool()
def buyer_count():
    """Total buyers"""

    data = load_database()

    return len([
        user
        for user in data["users"]
        if user["role"] == "buyer"
    ])


@mcp.tool()
def supplier_count():
    """Total suppliers"""

    data = load_database()

    return len([
        user
        for user in data["users"]
        if user["role"] == "supplier"
    ])


# ==========================================================
# ORDERS
# ==========================================================

@mcp.tool()
def list_orders():
    """List all orders"""

    data = load_database()

    return data["orders"]


@mcp.tool()
def get_order(order_number: str):
    """Get order by order number"""

    data = load_database()

    for order in data["orders"]:

        if order["order_number"] == order_number:
            return order

    return {"error": "Order not found"}


@mcp.tool()
def orders_by_user(username: str):
    """Get orders for a buyer"""

    data = load_database()

    return [
        order
        for order in data["orders"]
        if order["buyer"] == username
    ]


@mcp.tool()
def recent_orders(limit: int = 10):
    """Latest orders"""

    data = load_database()

    orders = sorted(
        data["orders"],
        key=lambda x: x["created_at"],
        reverse=True
    )

    return orders[:limit]


@mcp.tool()
def order_count():
    """Total orders"""

    data = load_database()

    return len(data["orders"])


# ==========================================================
# PLATFORM ANALYTICS
# ==========================================================

@mcp.tool()
def platform_stats():
    """Platform overview"""

    data = load_database()

    buyers = len([
        user
        for user in data["users"]
        if user["role"] == "buyer"
    ])

    suppliers = len([
        user
        for user in data["users"]
        if user["role"] == "supplier"
    ])

    return {
        "total_users": len(data["users"]),
        "buyers": buyers,
        "suppliers": suppliers,
        "orders": len(data["orders"]),
        "platform_credits": data.get("platform_credits", 0)
    }


@mcp.tool()
def wallet_summary():
    """Credits summary"""

    data = load_database()

    total_user_credits = sum(
        user.get("credits", 0)
        for user in data["users"]
    )

    return {
        "platform_credits": data.get("platform_credits", 0),
        "user_wallet_credits": total_user_credits
    }


@mcp.tool()
def top_suppliers():
    """Highest earning suppliers"""

    data = load_database()

    suppliers = [
        {
            "username": user["username"],
            "credits": user.get("credits", 0)
        }
        for user in data["users"]
        if user["role"] == "supplier"
    ]

    suppliers.sort(
        key=lambda x: x["credits"],
        reverse=True
    )

    return suppliers


@mcp.tool()
def top_buyers():
    """Buyers with lowest remaining credits"""

    data = load_database()

    buyers = [
        {
            "username": user["username"],
            "credits": user.get("credits", 0)
        }
        for user in data["users"]
        if user["role"] == "buyer"
    ]

    buyers.sort(
        key=lambda x: x["credits"]
    )

    return buyers


# ==========================================================
# SAFE WRITE TOOLS
# ==========================================================

@mcp.tool()
def recharge_wallet(username: str, amount: float):
    """Add credits to a user wallet"""

    data = load_database()

    user = next(
        (
            u
            for u in data["users"]
            if u["username"] == username
        ),
        None
    )

    if not user:
        return {
            "success": False,
            "message": "User not found"
        }

    user["credits"] = round(
        user.get("credits", 0) + amount,
        2
    )

    save_database(data)

    return {
        "success": True,
        "username": username,
        "credits": user["credits"]
    }


@mcp.tool()
def update_inventory(
    supplier_username: str,
    quantity: int
):
    """Update supplier inventory quantity"""

    data = load_database()

    supplier = next(
        (
            u
            for u in data["users"]
            if u["username"] == supplier_username
        ),
        None
    )

    if not supplier:
        return {
            "success": False,
            "message": "Supplier not found"
        }

    if supplier.get("role") != "supplier":
        return {
            "success": False,
            "message": "User is not a supplier"
        }

    supplier["item"]["quantity"] = quantity

    save_database(data)

    return {
        "success": True,
        "supplier": supplier_username,
        "new_quantity": quantity
    }


# ==========================================================
# EMAILS
# ==========================================================

@mcp.tool()
def email_outbox():
    """Show email queue"""

    data = load_database()

    return data.get("email_outbox", [])


@mcp.tool()
def failed_emails():
    """Show failed emails"""

    data = load_database()

    return [
        email
        for email in data.get("email_outbox", [])
        if email.get("status") == "failed"
    ]


# ==========================================================
# SERVER
# ==========================================================

if __name__ == "__main__":
    mcp.run()