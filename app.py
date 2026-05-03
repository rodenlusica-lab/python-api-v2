from flask import Flask, request, jsonify
import psycopg2
from psycopg2.extras import RealDictCursor
import random
import os

app = Flask(__name__)



def get_db():
    return psycopg2.connect(
        host=os.getenv("PGHOST"),
        database=os.getenv("PGDATABASE"),
        user=os.getenv("PGUSER"),
        password=os.getenv("PGPASSWORD"),
        port=os.getenv("PGPORT")
    )
# ==========================
# PRODUCT CLASS (ONE ONLY)
# ==========================
class Product:
    def __init__(self, product_id=None, name=None, category=None, price=None, stock=None):
        self.product_id = product_id
        self.name = name.strip() if name else ""
        self.category = category.strip() if category else ""
        self.price = float(price) if price is not None else 0
        self.stock = int(stock) if stock is not None else 0

# ==========================
# PRODUCT MANAGER (ONE ONLY)
# ==========================
class ProductManager:

    def __init__(self):
        self.db = get_db()
        self.cursor = self.db.cursor()

    def generate_product_id(self):
        while True:
            product_id = f"{random.randint(10,99)}-{random.randint(100,999)}-{random.randint(1000,9999)}"
            self.cursor.execute("SELECT Product_ID FROM products WHERE Product_ID=%s", (product_id,))
            if self.cursor.fetchone() is None:
                return product_id

    # ADD
    def add_product(self, product):
        product_id = self.generate_product_id()

        self.cursor.execute("""
            INSERT INTO products
            (Product_ID, Product_Name, Category, Stock_Quantity, Unit_Price, Date_Received)
            VALUES (%s,%s,%s,%s,%s,NOW())
        """, (product_id, product.name, product.category, product.stock, product.price))

        self.cursor.execute("""
            INSERT INTO activity_logs (action, product_name, details, created_at)
            VALUES (%s,%s,%s,NOW())
        """, ("ADD", product.name, f"Added product (ID: {product_id})"))

        self.db.commit()
        return product_id

    # DELETE
    def delete_product(self, product):
        self.cursor.execute("SELECT * FROM products WHERE Product_ID=%s", (product.product_id,))
        old = self.cursor.fetchone()

        if not old:
            return False, "Product not found"

        name = old["Product_Name"]

        self.cursor.execute("DELETE FROM products WHERE Product_ID=%s", (product.product_id,))

        self.cursor.execute("""
            INSERT INTO activity_logs (action, product_name, details, created_at)
            VALUES (%s,%s,%s,NOW())
        """, ("DELETE", name, f"Deleted product (ID: {product.product_id})"))

        self.db.commit()
        return True, name

    # UPDATE
    def update_product(self, product):
        self.cursor.execute("SELECT * FROM products WHERE Product_ID=%s", (product.product_id,))
        old = self.cursor.fetchone()

        if not old:
            return False, "Product not found"

        self.cursor.execute("""
            UPDATE products
            SET Product_Name=%s, Stock_Quantity=%s, Unit_Price=%s
            WHERE Product_ID=%s
        """, (product.name, product.stock, product.price, product.product_id))

        self.cursor.execute("""
            INSERT INTO activity_logs (action, product_name, details, created_at)
            VALUES (%s,%s,%s,NOW())
        """, ("UPDATE", product.name, "Product updated"))

        self.db.commit()
        return True, product.name

    def close(self):
        self.cursor.close()
        self.db.close()



# ==========================
# SALE CLASS
# ==========================
class Sale:
    def __init__(self, product_id, qty):
        self.product_id = product_id
        self.qty = int(qty) if qty is not None else 0

# ==========================
# SALE MANAGER
# ==========================
class SaleManager:

    def __init__(self):
        self.db = get_db()
        self.cursor = self.db.cursor(dictionary=True)

    def process_sale(self, sale):

        if not sale.product_id or sale.qty <= 0:
            return False, "Invalid input", None

        self.cursor.execute("SELECT * FROM products WHERE Product_ID=%s", (sale.product_id,))
        product = self.cursor.fetchone()

        if not product:
            return False, "Product not found", None

        current_stock = int(product["Stock_Quantity"])
        price = float(product["Unit_Price"])
        name = product["Product_Name"]

        if current_stock < sale.qty:
            return False, "Not enough stock", None

        new_stock = current_stock - sale.qty
        total = price * sale.qty

        self.cursor.execute(
            "UPDATE products SET Stock_Quantity=%s WHERE Product_ID=%s",
            (new_stock, sale.product_id)
        )

        self.cursor.execute(
            "INSERT INTO sales_records (product_name, quantity, total_price, sale_date) VALUES (%s,%s,%s,NOW())",
            (name, sale.qty, total)
        )

        self.cursor.execute(
            "INSERT INTO activity_logs (action, product_name, details, created_at) VALUES (%s,%s,%s,NOW())",
            ("SALE", name, f"Sold {sale.qty} pcs (₱{total})")
        )

        self.db.commit()

        return True, None, {
            "product": name,
            "price": price,
            "qty": sale.qty,
            "total": total,
            "remaining_stock": new_stock
        }

    def close(self):
        self.cursor.close()
        self.db.close()
# ==========================
# ADD ROUTE
# ==========================
@app.route("/add-product", methods=["POST"])
def add_product():
    manager = ProductManager()
    try:
        data = request.json

        product = Product(
            name=data.get("name"),
            category=data.get("category"),
            price=data.get("price"),
            stock=data.get("stock")
        )

        product_id = manager.add_product(product)

        return jsonify({
    "success": True,
    "message": f"✅ Product '{product.name}' added successfully (ID: {product_id})",
    "product_id": product_id
})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)})
    finally:
        manager.close()

# ==========================
# DELETE ROUTE
# ==========================
@app.route("/delete-product", methods=["POST"])
def delete_product():
    manager = ProductManager()
    try:
        data = request.json

        product = Product(product_id=data.get("product_id"))

        success, result = manager.delete_product(product)

        if not success:
            return jsonify({"success": False, "error": result})

        return jsonify({
            "success": True,
            "message": f"Deleted: {result}"
        })

    except Exception as e:
        return jsonify({"success": False, "error": str(e)})
    finally:
        manager.close()

# ==========================
# EDIT ROUTE
# ==========================
@app.route("/edit-product", methods=["POST"])
def edit_product():
    manager = ProductManager()
    try:
        data = request.json

        product = Product(
            product_id=data.get("product_id"),
            name=data.get("name"),
            price=data.get("price"),
            stock=data.get("stock")
        )

        success, result = manager.update_product(product)

        if not success:
            return jsonify({"success": False, "error": result})

        return jsonify({
            "success": True,
            "message": f"Updated: {result}"
        })

    except Exception as e:
        return jsonify({"success": False, "error": str(e)})
    finally:
        manager.close()

@app.route("/process-sale", methods=["POST"])
def process_sale():
    manager = SaleManager()
    try:
        data = request.json

        sale = Sale(
            data.get("product_id"),
            data.get("qty")
        )

        success, error, result = manager.process_sale(sale)

        if not success:
            return jsonify({"success": False, "error": error})

        return jsonify({
            "success": True,
            **result
        })

    except Exception as e:
        return jsonify({"success": False, "error": str(e)})
    finally:
        manager.close()

# ==========================
# RUN
# ==========================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000, debug=True)

@app.route("/", methods=["GET"])
def home():
    return "API is running!"
