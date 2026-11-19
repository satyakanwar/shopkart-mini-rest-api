import json
import re
from pathlib import Path
from flask import Blueprint, jsonify, redirect, request, send_from_directory
from . import config
from .services import container, blob_service, create_sas_url

api = Blueprint("api", __name__)
CATEGORY_FOLDER = {
    "ELEC": "electronics", "FASH": "fashion", "HOME": "home-kitchen",
    "BOOK": "books", "GROC": "grocery",
}
PRODUCT_FIELDS = ("id", "name", "brand", "price", "rating", "stock")

def local_products():
    return json.loads((config.ROOT / "data" / "products.json").read_text(encoding="utf-8"))

def local_orders():
    return json.loads((config.ROOT / "data" / "orders.json").read_text(encoding="utf-8"))

def azure_enabled():
    return config.azure_configured()

@api.get("/health")
def health():
    return jsonify(status="ok")

@api.get("/api/products")
def list_products():
    category = (request.args.get("category") or "").strip()
    if not category:
        return jsonify(error="category query parameter is required"), 400
    if azure_enabled():
        query = ("SELECT c.id, c.name, c.brand, c.price, c.rating, c.stock "
                 "FROM c WHERE c.category = @category ORDER BY c.price")
        rows = container("products").query_items(
            query=query,
            parameters=[{"name": "@category", "value": category}],
            partition_key=category,
        )
        return jsonify(list(rows))
    rows = [p for p in local_products() if p.get("category", "").lower() == category.lower()]
    rows.sort(key=lambda p: p.get("price", 0))
    return jsonify([{field: p.get(field) for field in PRODUCT_FIELDS} for p in rows])

@api.get("/api/products/search")
def search_products():
    q = (request.args.get("q") or "").strip().lower()
    if len(q) < 2:
        return jsonify(error="search query must contain at least 2 characters"), 400
    if azure_enabled():
        query = ("SELECT TOP 20 c.id, c.name, c.category, c.price FROM c "
                 "WHERE CONTAINS(LOWER(c.name), @q)")
        rows = container("products").query_items(
            query=query,
            parameters=[{"name": "@q", "value": q}],
            enable_cross_partition_query=True,
        )
        return jsonify(list(rows))
    matches = [p for p in local_products() if q in p.get("name", "").lower()]
    matches.sort(key=lambda p: p.get("name", "").lower())
    return jsonify([{"id": p.get("id"), "name": p.get("name"),
                     "category": p.get("category"), "price": p.get("price")}
                    for p in matches[:20]])

@api.get("/api/orders/<customer_id>")
def customer_orders(customer_id):
    if azure_enabled():
        query = ("SELECT c.id, c.orderDate, c.status, c.total FROM c "
                 "ORDER BY c.orderDate DESC")
        rows = container("orders").query_items(query=query, partition_key=customer_id)
        return jsonify(list(rows))
    rows = [o for o in local_orders() if o.get("customerId") == customer_id]
    rows.sort(key=lambda o: o.get("orderDate", ""), reverse=True)
    return jsonify([{"id": o.get("id"), "orderDate": o.get("orderDate"),
                     "status": o.get("status"), "total": o.get("total")} for o in rows])

@api.get("/api/products/<sku>/image")
def product_image(sku):
    # if not re.fullmatch(r"[A-Z]{4}-\\d{4}", sku):
    if not re.fullmatch(r"[A-Z]{4}-\d{4}", sku):
        return jsonify(error="invalid SKU; expected format ABCD-1234"), 400
    folder = CATEGORY_FOLDER.get(sku[:4], "misc")
    blob_name = f"{folder}/{sku}.png"
    if azure_enabled():
        blob = blob_service().get_blob_client("product-images", blob_name)
        if not blob.exists():
            return jsonify(error="product image not found"), 404
        url = create_sas_url("product-images", blob_name, BlobSasPermissions(read=True), 10)
        return redirect(url, code=302)

    image_name = f"{sku}.png"
    image_dir = config.ROOT / "assets" / "product_images"
    if not (image_dir / image_name).is_file():
        return jsonify(error="product image not found"), 404
    # Local development serves the sample image directly; Azure mode uses a short-lived read SAS.
    return send_from_directory(image_dir, image_name)

@api.post("/api/vendor/upload-url")
def vendor_upload_url():
    body = request.get_json(silent=True) or {}
    file_name = body.get("fileName", "")
    vendor_id = body.get("vendorId", "")
    # safe_file = re.fullmatch(r"[A-Za-z0-9._-]{1,80}\\.(pdf|png|jpg|jpeg)", file_name, re.IGNORECASE)
    safe_file = re.fullmatch(r"[A-Za-z0-9._-]{1,80}\.(pdf|png|jpg|jpeg)", file_name, re.IGNORECASE)
    safe_vendor = re.fullmatch(r"[a-z0-9-]{2,40}", vendor_id)
    if not safe_file or not safe_vendor:
        return jsonify(error="invalid fileName or vendorId"), 400
    if not azure_enabled():
        return jsonify(error="Azure Blob Storage is not configured; set STORAGE_CONNECTION_STRING to enable SAS uploads"), 503
    blob_name = f"{vendor_id}/{file_name}"
    url = create_sas_url("vendor-uploads", blob_name,
                         BlobSasPermissions(create=True, write=True), 10)
    return jsonify(uploadUrl=url, method="PUT",
                   headers={"x-ms-blob-type": "BlockBlob"}, expiresInMinutes=10)
