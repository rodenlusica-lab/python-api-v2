from flask import Flask, request, jsonify
import random

app = Flask(__name__)

# ==========================
# BASE RESPONSE HANDLER
# ==========================
class ResponseHandler:
    @staticmethod
    def success(data):
        return jsonify({"success": True, **data})

    @staticmethod
    def error(message):
        return jsonify({"success": False, "error": message})


# ==========================
# PRODUCT CLASS
# ==========================
class Product:
    def __init__(self, data):
        self.product_id = data.get("product_id")
        self.name = (data.get("name") or "").strip()
        self.category = (data.get("category") or "").strip()
        self.price = float(data.get("price", 0))
        self.stock = int(data.get("stock", 0))


# ==========================
# PRODUCT MANAGER (LOGIC ONLY)
# ==========================
class ProductManager:

    def generate_product_id(self):
        return f"{random.randint(10,99)}-{random.randint(100,999)}-{random.randint(1000,9999)}"

    def validate_product(self, product):
        if not product.name or not product.category:
            return False, "Missing required fields"
        return True, None


# ==========================
# SALE CLASS
# ==========================
class Sale:
    def __init__(self, data):
        self.product_id = data.get("product_id")
        self.qty = int(data.get("qty", 0))
        self.price = float(data.get("price", 0))


# ==========================
# SALE MANAGER
# ==========================
class SaleManager:

    def process(self, sale):
        if not sale.product_id:
            return False, "Missing product ID", None

        if sale.qty <= 0:
            return False, "Invalid quantity", None

        total = sale.qty * sale.price

        return True, None, {
            "product_id": sale.product_id,
            "qty": sale.qty,
            "price": sale.price,
            "total": total
        }


# ==========================
# CONTROLLER (ROUTES)
# ==========================
class ProductController:

    @staticmethod
    @app.route("/add-product", methods=["POST"])
    def add_product():
        data = request.get_json(silent=True) or {}

        product = Product(data)
        manager = ProductManager()

        valid, error = manager.validate_product(product)
        if not valid:
            return ResponseHandler.error(error)

        product_id = manager.generate_product_id()

        return ResponseHandler.success({
            "product_id": product_id,
            "message": f"Generated ID: {product_id}"
        })

    @staticmethod
    @app.route("/edit-product", methods=["POST"])
    def edit_product():
        data = request.get_json(silent=True) or {}

        if not data.get("product_id"):
            return ResponseHandler.error("Missing ID")

        return ResponseHandler.success({
            "message": "Product validated for update"
        })

    @staticmethod
    @app.route("/delete-product", methods=["POST"])
    def delete_product():
        data = request.get_json(silent=True) or {}

        if not data.get("product_id"):
            return ResponseHandler.error("Missing ID")

        return ResponseHandler.success({
            "message": "Product validated for delete"
        })


class SaleController:

    @staticmethod
    @app.route("/process-sale", methods=["POST"])
    def process_sale():
        data = request.get_json(silent=True) or {}

        sale = Sale(data)
        manager = SaleManager()

        success, error, result = manager.process(sale)

        if not success:
            return ResponseHandler.error(error)

        return ResponseHandler.success(result)


# ==========================
# ROOT (TEST)
# ==========================
@app.route("/")
def home():
    return "API is running (OOP)"

# ==========================
# RUN
# ==========================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)