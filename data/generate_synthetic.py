import random                          #For generating random data for synthetic sales and customer data
import datetime                        #For generating random dates for synthetic sales data
import json                            #For saving generated synthetic data to a JSON file 
import uuid                            #For generating unique customer IDs

#----Step-1 Raw materials-----

#List of 80 fake B2B companies names for synthetic customer data generation
company_names = [
      "Prakash Steel & Fabrication",
    "Sharma Industrial Supplies",
    "Gujarat Pipe Works",
    "Mehta Fasteners Ltd",
    "Rajasthan Valve Industries",
    "Tata Allied Components",
    "Bharat Seal & Gasket Co",
    "Pune Metal Works",
    "Krishna Industrial Traders",
    "Vijay Pipe & Fittings",
    "Agarwal Steel Distributors",
    "Mumbai Flange Corporation",
    "Hyderabad Industrial Supplies",
    "Coimbatore Pipe Works",
    "Delhi Fastener House",
    "Jaipur Metal Industries",
    "Surat Valve & Fitting Co",
    "Nagpur Steel Traders",
    "Kolkata Industrial Corp",
    "Bhopal Pipe & Seal Works",
    "Chandigarh Fasteners Ltd",
    "Indore Metal Distributors",
    "Ludhiana Steel & Pipes",
    "Patna Industrial Supplies",
    "Vadodara Flange Works",
    "Kochi Pipe & Fittings",
    "Vizag Steel Components",
    "Nashik Valve Industries",
    "Amritsar Metal Works",
    "Jodhpur Industrial Traders",
    "Ranchi Fastener Corp",
    "Guwahati Pipe Works",
    "Bhubaneswar Steel Supplies",
    "Mangalore Industrial Co",
    "Mysore Valve & Gasket Ltd",
    "Trichy Pipe Corporation",
    "Madurai Metal Industries",
    "Agra Steel Distributors",
    "Meerut Fastener Works",
    "Kanpur Industrial Supplies",
    "Allahabad Pipe & Fittings",
    "Varanasi Metal Corp",
    "Srinagar Industrial Traders",
    "Dehradun Steel Works",
    "Raipur Pipe & Valve Co",
    "Jabalpur Fasteners Ltd",
    "Gwalior Metal Industries",
    "Ujjain Steel Distributors",
    "Aurangabad Pipe Works",
    "Solapur Industrial Supplies",
    "Kolhapur Valve Corp",
    "Rajkot Flange Industries",
    "Bhavnagar Steel Traders",
    "Jamnagar Pipe & Seal Co",
    "Anand Metal Works",
    "Gandhinagar Industrial Corp",
    "Siliguri Fastener Works",
    "Durgapur Steel Supplies",
    "Asansol Pipe Industries",
    "Howrah Metal Distributors",
    "Tirupur Industrial Traders",
    "Salem Valve & Fitting Co",
    "Erode Steel Works",
    "Vellore Pipe Corporation",
    "Guntur Fasteners Ltd",
    "Kakinada Industrial Supplies",
    "Nellore Metal Corp",
    "Warangal Steel Distributors",
    "Hubli Pipe & Fittings",
    "Belgaum Industrial Works",
    "Shimoga Valve Industries",
    "Tumkur Metal Traders",
    "Thrissur Pipe Works",
    "Kozhikode Industrial Corp",
    "Kollam Fastener Supplies",
    "Ajmer Steel & Fabrication",
    "Bikaner Pipe Works",
    "Udaipur Valve Industries",
    "Kota Industrial Supplies",
    "Aligarh Metal Distributors",]

#possible cities the compnmies can be located in
cities = ["Mumbai", "Delhi", "Kolkata", "Chennai", "Ahmedabad", "Pune", "Hyderabad", "Surat", "Jaipur", "Lucknow"]

#possible customer tiers for synthetic customer data generation
tiers = ["Gold", "Silver", "Bronze"]

#possible account managers for synthetic customer data generation
managers = ["Ravi Kumar", "Suresh Patel", "Anil Sharma", "Vijay Singh", "Rajesh Gupta", "Sunil Mehta", "Amit Joshi", "Pankaj Verma", "Karan Malhotra", "Sanjay Reddy"]

#possible products for synthetic sales data generation
products = ["Steel Pipes", "Valves", "Flanges", "Fasteners", "Gaskets"]

#----Step-2: Build 80 customer profiles----

#empty bucket to hold generated synthetic customer data
customers = []

for i in range(80):
    customer ={
        "customer_id": f"CST-{str(i+1).zfill(3)}",                     #Generates unique customer IDs in the format CST-001, CST-002, ..., CST-080
        "company_name": company_names[i],                              #Assigns a unique company name from the predefined list to each customer
        "city": random.choice(cities),                                 #Assigns a random city from the predefined list to each customer
        "tier": random.choice(tiers),                                  #Assigns a random customer tier from the predefined list to each customer
        "account_manager": random.choice(managers),                    #Assigns a random account manager from the predefined list to each customer
    }

    #Appends the generated customer data to the customers list
    customers.append(customer)

#----Step-3: Save to file----

#opens a file named "customers.json" in write mode and saves the generated synthetic customer data in JSON format with an indentation of 4 spaces for better readability
with open("data/customers.json", "w") as f:
    json.dump(customers, f, indent=4)    
    
                                        #confirm it worked + json.dump takes python data and writes it to a file in JSON format, with indent=4 for pretty printing

start_date = datetime.date(2023, 1, 1)                                     

orders = []


for customer in customers:
    for j in range(40):  # Generate a total of 40 orders for the customers
        order = {
            "order_id": f"ORD-{str(len(orders)+1).zfill(3)}",  # Generate a new unique order ID
            "customer_id": customer["customer_id"],             # Associate the order with the current customer's ID
            "order_date": (start_date + datetime.timedelta(days=random.randint(0, 540))).strftime("%Y-%m-%d"),
            "order_amount": round(random.uniform(1000, 100000), 2),  # Random order amount between 1000 and 100000
            "products": random.sample(products, k=random.randint(2, 4))  # Randomly select 2 to 4 products for the order
        }

        orders.append(order)

with open("data/orders.json", "w") as f:
    json.dump(orders, f, indent=4)  # Save the generated synthetic sales data to a JSON file with pretty printing

print("orders.json created!")    



