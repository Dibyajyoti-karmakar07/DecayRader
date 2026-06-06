# run this in a quick script or python shell
from pymongo import MongoClient
import certifi, os
from dotenv import load_dotenv

load_dotenv()
client = MongoClient(os.getenv("MONGODB_URI"), tlsCAFile=certifi.where())
db = client["DecayRader"]

# Check actual field names in each collection
print("=== CUSTOMERS ===")
print(db["Customers"].find_one())

print("\n=== RISK SCORES ===")
print(db["risk_scores"].find_one())

print("\n=== FEATURES ===")
print(db["features"].find_one())

# check what tier values actually exist
tiers = db["Customers"].distinct("tier")
print(tiers)