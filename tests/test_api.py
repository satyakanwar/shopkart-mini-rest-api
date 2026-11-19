import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.main import create_app

def setup_client():
    app = create_app()
    app.config["TESTING"] = True
    return app.test_client()

def test_health():
    response = setup_client().get("/health")
    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}

def test_products_requires_category():
    assert setup_client().get("/api/products").status_code == 400

def test_products_by_category():
    response = setup_client().get("/api/products?category=Electronics")
    assert response.status_code == 200
    assert len(response.get_json()) > 0
    assert all("name" in item and "price" in item for item in response.get_json())

def test_search_requires_two_characters():
    assert setup_client().get("/api/products/search?q=a").status_code == 400

def test_search_is_case_insensitive():
    response = setup_client().get("/api/products/search?q=SAMsung")
    assert response.status_code == 200
    assert any("samsung" in item["name"].lower() for item in response.get_json())

def test_customer_orders():
    response = setup_client().get("/api/orders/CUST-001")
    assert response.status_code == 200
    assert all(set(item) == {"id", "orderDate", "status", "total"} for item in response.get_json())

def test_bad_sku():
    assert setup_client().get("/api/products/../../etc/passwd/image").status_code in (400, 404)

def test_vendor_upload_validation():
    response = setup_client().post("/api/vendor/upload-url",
        json={"vendorId": "../bad", "fileName": "invoice.pdf"})
    assert response.status_code == 400
