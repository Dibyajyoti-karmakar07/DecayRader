import json
import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

# Load MongoDB URI from environment variable
Mongodb_URI = os.getenv("MONGODB_URI")

#Connect to MongoDB Atlas
Client = MongoClient(Mongodb_URI)

#Access the specific database and collection
db = Client["DecayRader"]

print("Connected to MongoDB Atlas successfully!")

# Load Customers data from JSON file
with open("data/customers.json", "r") as file:
    customers = json.load(file)

# Load Orders data from JSON file
with open("data/orders.json", "r") as file:
    orders = json.load(file)


# Insert data into MongoDB connection
db["Customers"].insert_many(customers)
db["Orders"].insert_many(orders)


print(f"Inserted {len(customers)} customers!")
print(f"Inserted {len(orders)} orders!")