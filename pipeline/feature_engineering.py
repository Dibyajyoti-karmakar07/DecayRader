import pandas as pd
# pyrefly: ignore [missing-import]
import numpy as np
from pymongo import MongoClient
from dotenv import load_dotenv
import os

# load the .env file
load_dotenv()

# connect to MongoDB Atlas
client = MongoClient(os.getenv("MONGODB_URI"))

# select the database — must match exactly what's in Atlas
db = client["DecayRader"]

# read Orders collection into a pandas DataFrame
# db["Orders"].find() returns all documents
# list() converts it to a Python list
# pd.DataFrame() converts that list into a table
orders_df = pd.DataFrame(list(db["Orders"].find()))

# read Customers collection into a pandas DataFrame
customers_df = pd.DataFrame(list(db["Customers"].find()))

print(f"Loaded {len(orders_df)} orders")
print(f"Loaded {len(customers_df)} customers")

#Sort orders by customer_id and order_date to ensure correct sequence for feature engineering
# convert order_date from string to datetime
orders_df["order_date"] = pd.to_datetime(orders_df["order_date"])
 
#Calculate days since previous order for each customer
orders_df["days_since_prev_order"] = orders_df.groupby("customer_id")["order_date"].diff().dt.days


#define cutoff date same as decay start date to split data into baseline and recent periods
cutoff_date = pd.Timestamp("2023-10-01")

#baseline orders - first 9 months of data
baseline_df = orders_df[orders_df["order_date"] < cutoff_date]

#recent orders - last 9 months of data
recent_df = orders_df[orders_df["order_date"] >= cutoff_date]


print(f"Baseline period: {len(baseline_df)} orders")
print(f"Recent period: {len(recent_df)} orders")


#Calculate average days between orders for customers in baseline and recent periods
baseline_gap = baseline_df.groupby("customer_id")["days_since_prev_order"].mean()
recent_gap = recent_df.groupby("customer_id")["days_since_prev_order"].mean()


#calclulate % change in order frequency
gap_change_pct =(((recent_gap - baseline_gap) / baseline_gap) * 100).round(2)


print(gap_change_pct.sort_values(ascending=False).head(10))


#Calculate the average amount per customer in baseline and recent periods
baseline_spend = baseline_df.groupby("customer_id")["order_amount"].mean()
recent_spend = recent_df.groupby("customer_id")["order_amount"].mean()

#calculate average order amount per customer
aov_change_pct = ( (recent_spend - baseline_spend) / baseline_spend * 100).round(2)

print(aov_change_pct.sort_values(ascending=True).head(10))


#get unique categories per customer in baseline and recent periods
# average number of products per order in baseline vs recent
baseline_diversity = baseline_df.groupby("customer_id")["products"].apply(
    lambda x: x.apply(len).mean()
)
recent_diversity = recent_df.groupby("customer_id")["products"].apply(
    lambda x: x.apply(len).mean()
)

# diversity delta - negative means fewer products per order
diversity_delta = (recent_diversity - baseline_diversity).round(2)

print(diversity_delta.sort_values().head(10))


#combine all features into a single DataFrame for analysis
features_df = pd.DataFrame({
    "customer_id": gap_change_pct.index,
    "gap_change_pct": gap_change_pct,
    "aov_change_pct": aov_change_pct,
    "diversity_delta": diversity_delta
}).reset_index(drop=True)


print(features_df.head(10))

#Save features to MongDB
features_records = features_df.to_dict("records")
db["features"].drop()  # drop existing collection to avoid duplicates
db["features"].insert_many(features_records)

print(f"Saved {len(features_records)} feature records to MongoDB!")