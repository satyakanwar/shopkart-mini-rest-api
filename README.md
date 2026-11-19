# ShopKart Mini REST API

A small Flask REST API for the ShopKart e-commerce case study. It exposes six endpoints and demonstrates Cosmos DB partition-key queries, parameterised search, input validation, and short-lived Azure Blob SAS URLs.

## 1. Features

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/health` | Health check |
| GET | `/api/products?category=Electronics` | List category products (single Cosmos partition) |
| GET | `/api/products/search?q=shoe` | Case-insensitive product search (max 20) |
| GET | `/api/orders/CUST-001` | Orders belonging to one customer |
| GET | `/api/products/ELEC-1001/image` | Product image (Azure: 10-minute read SAS redirect) |
| POST | `/api/vendor/upload-url` | Generate a 10-minute write-only SAS URL |

## 2. Run locally (no Azure account required for the basic API)

Python 3.10+ is recommended. Open a terminal in this repository:

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
python run.py
```

On macOS/Linux, activate with `source .venv/bin/activate` and copy the env file with `cp .env.example .env`.

Local mode reads the bundled `data/products.json` and `data/orders.json`. Product image requests serve the included sample PNG files directly. Vendor SAS upload links require Azure configuration and return HTTP 503 when Azure is not configured.

## 3. Try the endpoints

```text
http://127.0.0.1:5000/health
http://127.0.0.1:5000/api/products?category=Electronics
http://127.0.0.1:5000/api/products/search?q=shoe
http://127.0.0.1:5000/api/orders/CUST-001
http://127.0.0.1:5000/api/products/ELEC-1001/image
```

POST upload URL using Postman:

- Method: `POST`
- URL: `http://127.0.0.1:5000/api/vendor/upload-url`
- Body → raw → JSON:

```json
{
  "vendorId": "technova",
  "fileName": "invoice.pdf"
}
```

## 4. Connect Azure services

Fill `.env` with the values from your Azure Cosmos DB account and Storage Account:

```env
COSMOS_ENDPOINT=https://YOUR-ACCOUNT.documents.azure.com:443/
COSMOS_KEY=YOUR_COSMOS_PRIMARY_KEY
COSMOS_DATABASE=shopkart
STORAGE_CONNECTION_STRING=YOUR_STORAGE_CONNECTION_STRING
```

Ensure Cosmos DB has containers named `products` and `orders`, with partition keys `/category` and `/customerId` respectively. Product documents need fields such as `id`, `name`, `category`, `brand`, `price`, `rating`, and `stock`. Order documents need `id`, `customerId`, `orderDate`, `status`, and `total`.

Create Blob containers named `product-images` and `vendor-uploads`. Product images should be stored under category folders, for example `product-images/electronics/ELEC-1001.png`. The API creates:
- Read-only SAS for a product image, expiring in 10 minutes.
- Create/write-only SAS for one vendor blob, expiring in 10 minutes.

A vendor client uploads directly to Blob Storage using HTTP PUT and header `x-ms-blob-type: BlockBlob`. Do not send the Storage account key to a frontend or commit `.env` to GitHub.

## 5. Run tests

```powershell
pytest -q
```

## 6. Push as your own GitHub repository

Create an empty repository on GitHub, for example `shopkart-mini-rest-api`, then run:

```powershell
git init
git add .
git commit -m "Build ShopKart mini REST API"
git branch -M main
git remote add origin https://github.com/YOUR-USERNAME/shopkart-mini-rest-api.git
git push -u origin main
```

Do not upload `.env`, `.venv`, or Azure credentials.
