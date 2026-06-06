import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import app as app_module


class ECommerceAppTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name)
        self.data_file = self.temp_path / "ecommerce_data.json"
        self.data_file.write_text(json.dumps({"users": []}), encoding="utf-8")

        self.patcher_data_dir = mock.patch.object(app_module, "DATA_DIR", self.temp_path)
        self.patcher_data_file = mock.patch.object(app_module, "DATA_FILE", self.data_file)
        self.patcher_data_dir.start()
        self.patcher_data_file.start()

        self.client = app_module.app.test_client()

    def tearDown(self):
        self.patcher_data_file.stop()
        self.patcher_data_dir.stop()
        self.temp_dir.cleanup()

    def test_home_page_loads(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Choose how you want to join", response.text)

    def test_buyer_registration_and_login_work(self):
        unique = "buyer_test_user"
        response = self.client.post(
            "/register",
            data={
                "role": "buyer",
                "full_name": "Buyer Test",
                "username": unique,
                "email": f"{unique}@example.com",
                "phone": "1234567890",
                "address": "Test address",
                "password": "Secret123!",
            },
            follow_redirects=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("Registration successful", response.text)

        login_response = self.client.post(
            "/login",
            data={"login_username": unique, "login_password": "Secret123!"},
            follow_redirects=True,
        )

        self.assertEqual(login_response.status_code, 200)
        self.assertIn("Welcome back, Buyer Test!", login_response.text)
        self.assertIn("100000", login_response.text)

    def test_supplier_registration_and_dashboard_work(self):
        unique = "supplier_test_user"
        response = self.client.post(
            "/register",
            data={
                "role": "supplier",
                "full_name": "Supplier Test",
                "username": unique,
                "email": f"{unique}@example.com",
                "phone": "0987654321",
                "address": "Supplier address",
                "password": "Secret123!",
            },
            follow_redirects=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("Registration successful", response.text)

        login_response = self.client.post(
            "/login",
            data={"login_username": unique, "login_password": "Secret123!"},
            follow_redirects=True,
        )

        self.assertEqual(login_response.status_code, 200)
        self.assertIn("Welcome back, Supplier Test!", login_response.text)

        list_response = self.client.post(
            "/supplier/list-product",
            data={
                "item_name": "Laptop",
                "item_description": "Gaming laptop",
                "item_price": "79999",
                "item_quantity": "4",
                "item_images": [
                    (io.BytesIO(b"img-one"), "one.png"),
                    (io.BytesIO(b"img-two"), "two.png"),
                ],
            },
            content_type="multipart/form-data",
            follow_redirects=True,
        )

        self.assertEqual(list_response.status_code, 200)
        self.assertIn("listed successfully", list_response.text)

    def test_supplier_image_upload_is_saved_for_dashboard(self):
        unique = "supplier_img_user"
        self.client.post(
            "/register",
            data={
                "role": "supplier",
                "full_name": "Supplier Image User",
                "username": unique,
                "email": f"{unique}@example.com",
                "phone": "1111111111",
                "address": "Supplier address",
                "password": "Secret123!",
            },
            follow_redirects=True,
        )

        self.client.post(
            "/login",
            data={"login_username": unique, "login_password": "Secret123!"},
            follow_redirects=True,
        )

        list_response = self.client.post(
            "/supplier/list-product",
            data={
                "item_name": "Smartphone",
                "item_description": "Latest smartphone",
                "item_price": "19999",
                "item_quantity": "2",
                "item_images": [
                    (io.BytesIO(b"img-a"), "a.png"),
                    (io.BytesIO(b"img-b"), "b.png"),
                ],
            },
            content_type="multipart/form-data",
            follow_redirects=True,
        )

        self.assertEqual(list_response.status_code, 200)
        self.assertIn("listed successfully", list_response.text)

        buyer_username = "buyer_for_supplier_image"
        self.client.post(
            "/register",
            data={
                "role": "buyer",
                "full_name": "Buyer for Supplier Image",
                "username": buyer_username,
                "email": "buyer_for_supplier_image@example.com",
                "phone": "2222222222",
                "address": "Buyer address",
                "password": "Secret123!",
            },
            follow_redirects=True,
        )

        buyer_login = self.client.post(
            "/login",
            data={"login_username": buyer_username, "login_password": "Secret123!"},
            follow_redirects=True,
        )

        self.assertEqual(buyer_login.status_code, 200)
        self.assertIn("products/uploads/", buyer_login.text)

    def test_buyer_can_view_cart(self):
        buyer_user = "cart_buyer"
        self.client.post(
            "/register",
            data={
                "role": "buyer",
                "full_name": "Cart Buyer",
                "username": buyer_user,
                "email": "cart_buyer@example.com",
                "phone": "3333333333",
                "address": "Buyer address",
                "password": "Secret123!",
            },
            follow_redirects=True,
        )

        self.client.post(
            "/login",
            data={"login_username": buyer_user, "login_password": "Secret123!"},
            follow_redirects=True,
        )

        cart_response = self.client.get("/cart", follow_redirects=True)
        self.assertEqual(cart_response.status_code, 200)
        self.assertIn("Your cart", cart_response.text)

    def test_buyer_can_add_product_to_cart_and_buy_now(self):
        buyer_user = "cart_action_buyer"
        self.client.post(
            "/register",
            data={
                "role": "buyer",
                "full_name": "Cart Action Buyer",
                "username": buyer_user,
                "email": "cart_action_buyer@example.com",
                "phone": "4444444444",
                "address": "Buyer address",
                "password": "Secret123!",
            },
            follow_redirects=True,
        )

        self.client.post(
            "/login",
            data={"login_username": buyer_user, "login_password": "Secret123!"},
            follow_redirects=True,
        )

        add_response = self.client.get("/cart/add/0", follow_redirects=True)
        self.assertEqual(add_response.status_code, 200)
        self.assertIn("Product added to your cart", add_response.text)

        buy_response = self.client.get("/buy/1", follow_redirects=True)
        self.assertEqual(buy_response.status_code, 200)
        self.assertIn("Review your order", buy_response.text)
        self.assertIn("Confirm order", buy_response.text)

    def test_buyer_order_placement_deducts_credits(self):
        supplier_user = "order_supplier"
        buyer_user = "order_buyer"

        self.client.post(
            "/register",
            data={
                "role": "supplier",
                "full_name": "Order Supplier",
                "username": supplier_user,
                "email": "order_supplier@example.com",
                "phone": "5555555555",
                "address": "Supplier address",
                "password": "Secret123!",
            },
            follow_redirects=True,
        )

        self.client.post(
            "/login",
            data={"login_username": supplier_user, "login_password": "Secret123!"},
            follow_redirects=True,
        )

        self.client.post(
            "/supplier/list-product",
            data={
                "item_name": "Order Item",
                "item_description": "Test product",
                "item_price": "5000",
                "item_quantity": "10",
                "item_images": [
                    (io.BytesIO(b"img-a"), "a.png"),
                    (io.BytesIO(b"img-b"), "b.png"),
                ],
            },
            content_type="multipart/form-data",
            follow_redirects=True,
        )

        self.client.get("/logout", follow_redirects=True)

        self.client.post(
            "/register",
            data={
                "role": "buyer",
                "full_name": "Order Buyer",
                "username": buyer_user,
                "email": "order_buyer@example.com",
                "phone": "6666666666",
                "address": "Buyer address",
                "password": "Secret123!",
            },
            follow_redirects=True,
        )

        login_response = self.client.post(
            "/login",
            data={"login_username": buyer_user, "login_password": "Secret123!"},
            follow_redirects=True,
        )

        self.assertIn("100000", login_response.text)

        self.client.get("/buy/8", follow_redirects=True)
        checkout_response = self.client.post("/checkout", follow_redirects=True)
        self.assertEqual(checkout_response.status_code, 200)
        self.assertIn("Order placed successfully", checkout_response.text)
        self.assertIn("Expected delivery", checkout_response.text)

        data = app_module.load_database()
        buyer = next(user for user in data["users"] if user["username"] == buyer_user)
        self.assertLess(buyer["credits"], 100000)

    def test_checkout_and_orders_pages_use_no_store_cache(self):
        buyer_user = "cache_buyer"
        self.client.post(
            "/register",
            data={
                "role": "buyer",
                "full_name": "Cache Buyer",
                "username": buyer_user,
                "email": "cache_buyer@example.com",
                "phone": "8888888888",
                "address": "Buyer address",
                "password": "Secret123!",
            },
            follow_redirects=True,
        )

        self.client.post(
            "/login",
            data={"login_username": buyer_user, "login_password": "Secret123!"},
            follow_redirects=True,
        )

        self.client.get("/buy/0", follow_redirects=True)
        checkout_response = self.client.get("/checkout")
        self.assertEqual(checkout_response.status_code, 200)
        self.assertIn("no-store", checkout_response.headers.get("Cache-Control", "").lower())

        orders_response = self.client.get("/orders")
        self.assertEqual(orders_response.status_code, 200)
        self.assertIn("no-store", orders_response.headers.get("Cache-Control", "").lower())

    def test_buyer_can_search_products_and_see_stock_status(self):
        supplier_user = "search_supplier"
        buyer_user = "search_buyer"

        self.client.post(
            "/register",
            data={
                "role": "supplier",
                "full_name": "Search Supplier",
                "username": supplier_user,
                "email": "search_supplier@example.com",
                "phone": "9000000000",
                "address": "Supplier address",
                "password": "Secret123!",
            },
            follow_redirects=True,
        )

        self.client.post(
            "/login",
            data={"login_username": supplier_user, "login_password": "Secret123!"},
            follow_redirects=True,
        )

        self.client.post(
            "/supplier/list-product",
            data={
                "item_name": "Search Item",
                "item_description": "Searchable product",
                "item_price": "2500",
                "item_quantity": "0",
                "item_images": [(io.BytesIO(b"img-a"), "a.png"), (io.BytesIO(b"img-b"), "b.png")],
            },
            content_type="multipart/form-data",
            follow_redirects=True,
        )

        self.client.get("/logout", follow_redirects=True)

        self.client.post(
            "/register",
            data={
                "role": "buyer",
                "full_name": "Search Buyer",
                "username": buyer_user,
                "email": "search_buyer@example.com",
                "phone": "9111111111",
                "address": "Buyer address",
                "password": "Secret123!",
            },
            follow_redirects=True,
        )

        self.client.post(
            "/login",
            data={"login_username": buyer_user, "login_password": "Secret123!"},
            follow_redirects=True,
        )

        search_response = self.client.get("/dashboard?search=Search Item", follow_redirects=True)
        self.assertEqual(search_response.status_code, 200)
        self.assertIn("Search Item", search_response.text)
        self.assertIn("Out of stock", search_response.text)

    def test_buyer_search_matches_keywords_and_typos(self):
        buyer_user = "keyword_buyer"
        self.client.post(
            "/register",
            data={
                "role": "buyer",
                "full_name": "Keyword Buyer",
                "username": buyer_user,
                "email": "keyword_buyer@example.com",
                "phone": "9444444444",
                "address": "Buyer address",
                "password": "Secret123!",
            },
            follow_redirects=True,
        )

        self.client.post(
            "/login",
            data={"login_username": buyer_user, "login_password": "Secret123!"},
            follow_redirects=True,
        )

        search_response = self.client.get("/dashboard?search=mobiles", follow_redirects=True)
        self.assertEqual(search_response.status_code, 200)
        self.assertIn("5G Smartphone", search_response.text)

    def test_order_reduces_supplier_stock_in_database(self):
        supplier_user = "stock_supplier"
        buyer_user = "stock_buyer"

        self.client.post(
            "/register",
            data={
                "role": "supplier",
                "full_name": "Stock Supplier",
                "username": supplier_user,
                "email": "stock_supplier@example.com",
                "phone": "9222222222",
                "address": "Supplier address",
                "password": "Secret123!",
            },
            follow_redirects=True,
        )

        self.client.post(
            "/login",
            data={"login_username": supplier_user, "login_password": "Secret123!"},
            follow_redirects=True,
        )

        self.client.post(
            "/supplier/list-product",
            data={
                "item_name": "Stock Item",
                "item_description": "Stock tracking product",
                "item_price": "5000",
                "item_quantity": "3",
                "item_images": [(io.BytesIO(b"img-a"), "a.png"), (io.BytesIO(b"img-b"), "b.png")],
            },
            content_type="multipart/form-data",
            follow_redirects=True,
        )

        self.client.get("/logout", follow_redirects=True)

        self.client.post(
            "/register",
            data={
                "role": "buyer",
                "full_name": "Stock Buyer",
                "username": buyer_user,
                "email": "stock_buyer@example.com",
                "phone": "9333333333",
                "address": "Buyer address",
                "password": "Secret123!",
            },
            follow_redirects=True,
        )

        self.client.post(
            "/login",
            data={"login_username": buyer_user, "login_password": "Secret123!"},
            follow_redirects=True,
        )

        self.client.get("/buy/8", follow_redirects=True)
        checkout_response = self.client.post("/checkout", follow_redirects=True)
        self.assertEqual(checkout_response.status_code, 200)

        data = app_module.load_database()
        supplier = next(user for user in data["users"] if user["username"] == supplier_user)
        self.assertEqual(int(supplier["item"]["quantity"]), 2)

    def test_invalid_login_shows_error_message(self):
        response = self.client.post(
            "/login",
            data={"login_username": "missing_user", "login_password": "WrongPass!1"},
            follow_redirects=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("Invalid username or password", response.text)

    def test_insufficient_credits_shows_recharge_error(self):
        buyer_user = "low_credits_buyer"
        supplier_user = "low_credits_supplier"

        self.client.post(
            "/register",
            data={
                "role": "supplier",
                "full_name": "Low Credits Supplier",
                "username": supplier_user,
                "email": "low_credits_supplier@example.com",
                "phone": "1010101010",
                "address": "Supplier address",
                "password": "Secret123!",
            },
            follow_redirects=True,
        )

        self.client.post(
            "/register",
            data={
                "role": "buyer",
                "full_name": "Low Credits Buyer",
                "username": buyer_user,
                "email": "low_credits_buyer@example.com",
                "phone": "2020202020",
                "address": "Buyer address",
                "password": "Secret123!",
            },
            follow_redirects=True,
        )

        self.client.post(
            "/login",
            data={"login_username": buyer_user, "login_password": "Secret123!"},
            follow_redirects=True,
        )

        data = app_module.load_database()
        buyer = next(user for user in data["users"] if user["username"] == buyer_user)
        buyer["credits"] = 0
        app_module.save_database(data)

        self.client.get("/buy/0", follow_redirects=True)
        response = self.client.post("/checkout", follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn("You do not have enough credits", response.text)

    def test_recharge_rejects_non_positive_amount(self):
        buyer_user = "invalid_recharge_buyer"
        self.client.post(
            "/register",
            data={
                "role": "buyer",
                "full_name": "Invalid Recharge Buyer",
                "username": buyer_user,
                "email": "invalid_recharge_buyer@example.com",
                "phone": "1212121212",
                "address": "Buyer address",
                "password": "Secret123!",
            },
            follow_redirects=True,
        )

        self.client.post(
            "/login",
            data={"login_username": buyer_user, "login_password": "Secret123!"},
            follow_redirects=True,
        )

        response = self.client.post(
            "/recharge",
            data={"card_number": "4111111111111111", "card_holder": "Invalid Recharge Buyer", "cvv": "123", "amount": "0"},
            follow_redirects=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("positive amount", response.text)

    def test_buyer_can_recharge_wallet(self):
        buyer_user = "recharge_buyer"
        self.client.post(
            "/register",
            data={
                "role": "buyer",
                "full_name": "Recharge Buyer",
                "username": buyer_user,
                "email": "recharge_buyer@example.com",
                "phone": "7777777777",
                "address": "Buyer address",
                "password": "Secret123!",
            },
            follow_redirects=True,
        )

        self.client.post(
            "/login",
            data={"login_username": buyer_user, "login_password": "Secret123!"},
            follow_redirects=True,
        )

        recharge_response = self.client.post(
            "/recharge",
            data={"card_number": "4111111111111111", "card_holder": "Recharge Buyer", "cvv": "123", "amount": "2500"},
            follow_redirects=True,
        )

        self.assertEqual(recharge_response.status_code, 200)
        self.assertIn("Wallet recharged", recharge_response.text)

        data = app_module.load_database()
        buyer = next(user for user in data["users"] if user["username"] == buyer_user)
        self.assertGreaterEqual(buyer["credits"], 100000 + 2500)


if __name__ == "__main__":
    unittest.main()
