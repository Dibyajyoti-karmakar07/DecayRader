import json
import os
from pathlib import Path

import certifi
from dotenv import load_dotenv
from pymongo import MongoClient


# =========================================================
# LOAD ENV VARIABLES
# =========================================================

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI")

if not MONGODB_URI:
    raise ValueError("MONGODB_URI not found in .env file")


# =========================================================
# CONNECT TO MONGODB ATLAS
# =========================================================

print("Connecting to MongoDB Atlas...")

client = MongoClient(
    MONGODB_URI,
    tlsCAFile=certifi.where(),
    serverSelectionTimeoutMS=5000
)

try:
    client.admin.command("ping")
    print("Connected to MongoDB Atlas successfully!")

except Exception as e:
    print("MongoDB connection failed!")
    print(e)
    exit()


# =========================================================
# ACCESS DATABASE
# =========================================================

db = client["DecayRader"]

print(f"Using database: {db.name}")


# =========================================================
# CREATE ABSOLUTE PATHS
# =========================================================

BASE_DIR = Path(__file__).resolve().parent.parent

customers_path = BASE_DIR / "data" / "customers.json"
orders_path = BASE_DIR / "data" / "orders.json"

print(f"Customers path: {customers_path}")
print(f"Orders path: {orders_path}")


# =========================================================
# CHECK FILE EXISTENCE
# =========================================================

if not customers_path.exists():
    raise FileNotFoundError(
        f"customers.json not found at:\n{customers_path}"
    )

if not orders_path.exists():
    raise FileNotFoundError(
        f"orders.json not found at:\n{orders_path}"
    )


# =========================================================
# LOAD CUSTOMERS DATA
# =========================================================

print("Loading customers.json...")

with open(customers_path, "r", encoding="utf-8") as file:
    customers = json.load(file)

print(f"Loaded {len(customers)} customers")


# =========================================================
# LOAD ORDERS DATA
# =========================================================

print("Loading orders.json...")

with open(orders_path, "r", encoding="utf-8") as file:
    orders = json.load(file)

print(f"Loaded {len(orders)} orders")


# =========================================================
# RESET COLLECTIONS (DEV MODE)
# =========================================================

print("Dropping old collections...")

db["Customers"].drop()
db["Orders"].drop()


# =========================================================
# INSERT CUSTOMERS
# =========================================================

print("Inserting customers into MongoDB...")

if len(customers) > 0:
    db["Customers"].insert_many(customers)

print(f"Inserted {len(customers)} customers!")


# =========================================================
# INSERT ORDERS
# =========================================================

print("Inserting orders into MongoDB...")

if len(orders) > 0:
    db["Orders"].insert_many(orders)

print(f"Inserted {len(orders)} orders!")


# =========================================================
# VERIFY INSERTION
# =========================================================

customers_count = db["Customers"].count_documents({})
orders_count = db["Orders"].count_documents({})

print("\nVerification:")

print(f"Customers in DB: {customers_count}")
print(f"Orders in DB: {orders_count}")


# =========================================================
# DONE
# =========================================================

print("\nMongoDB data loading completed successfully!")