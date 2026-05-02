'''
from flask import Flask, request, jsonify
import mysql.connector
import random

app = Flask(__name__)

def get_db():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="cloud_system"
    )

# ==========================
# PRODUCT CLASS
# ==========================
class Product:
    def __init__(self, name, category, price, stock):
        self.name = name.strip() if name else ""
        self.category = category.strip() if category else ""
        self.price = float(price)
        self.stock = int(stock)

# ==========================
# PRODUCT MANAGER
# ==========================
class ProductManager:

    def generate_product_id(self):
        return f"{random.randint(10,99)}-{random.randint(100,999)}-{random.randint(1000,9999)}"

    def add_product(self, product):
        db = get_db()
        cursor = db.cursor()

        try:
            # 🔥 ensure unique ID
            while True:
                product_id = self.generate_product_id()
                cursor.execute("SELECT Product_ID FROM products WHERE Product_ID = %s", (product_id,))
                if cursor.fetchone() is None:
                    break

            # 🔥 INSERT WITH ID
            cursor.execute("""
                INSERT INTO products
                (Product_ID, Product_Name, Category, Stock_Quantity, Unit_Price, Date_Received)
                VALUES (%s, %s, %s, %s, %s, NOW())
            """, (product_id, product.name, product.category, product.stock, product.price))

            db.commit()
            return product_id

        except Exception as e:
            db.rollback()
            print("ERROR:", e)
            return None

        finally:
            cursor.close()
            db.close()

# ==========================
# LOGGER
# ==========================
class Logger:
    def log(self, action, name, details):
        db = get_db()
        cursor = db.cursor()

        cursor.execute("""
            INSERT INTO activity_logs (action, product_name, details, created_at)
            VALUES (%s, %s, %s, NOW())
        """, (action, name, details))

        db.commit()
        cursor.close()
        db.close()

# ==========================
# API ROUTE
# ==========================
@app.route("/add-product", methods=["POST"])
def add_product():
    data = request.json

    # 🔥 basic validation
    if not data.get("name") or not data.get("category"):
        return jsonify({"success": False, "error": "Missing fields"})

    product = Product(
        data.get("name"),
        data.get("category"),
        data.get("price"),
        data.get("stock")
    )

    manager = ProductManager()
    product_id = manager.add_product(product)

    if not product_id:
        return jsonify({"success": False, "error": "Insert failed"})

    Logger().log("ADD", product.name, f"New product added (ID: {product_id})")

    return jsonify({
        "success": True,
        "product_id": product_id
    })

# ==========================
# RUN SERVER
# ==========================
if __name__ == "__main__":
    app.run(port=10000, debug=True)
    '''