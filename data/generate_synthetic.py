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

#15 customers chosen to have decay patterns planted   
decaying_customers = [
    "CST-042",  # Prakash Steel - hero demo customer
    "CST-007", "CST-015", "CST-021", "CST-033",
    "CST-048", "CST-055", "CST-062", "CST-068",
    "CST-011", "CST-024", "CST-037", "CST-051",
    "CST-071", "CST-078"
]

#Month 9 cutoff - decay starts after this day 
decay_start = datetime.date(2023, 10, 1)


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

#--step-4: Generate synthetic sales data---


for customer in customers:
    for j in range(40):  # Generate a total of 40 orders for the customers

        #generate order date first so we can check if it's before/after decay start
        order_date = start_date + datetime.timedelta(days=random.randint(0, 540))  

        #check if this customer is decaying AND order is after Month 9
        if customer["customer_id"] in decaying_customers and order_date >= decay_start:
           #decayed behaviour -less frequent,less spend, fewer products
           amount = round(random.uniform(1000, 40000), 2)
           order_products = random.sample(products, k=random.randint(1, 2))# Randomly select 1 to 2 products for decaying customers

        else:
              #normal behaviour - more frequent, higher spend, more products
              amount = round(random.uniform(1000, 100000), 2)
              order_products = random.sample(products, k=random.randint(3, 5))  # Randomly select 3 to 5 products for normal customers


        order = {
            "order_id": f"ORD-{str(len(orders)+1).zfill(5)}",
            "customer_id": customer["customer_id"],
            "order_date": order_date.strftime("%Y-%m-%d"),
            "order_amount": amount,
            "products": order_products
        }

        orders.append(order)

with open("data/orders.json", "w") as f:
    json.dump(orders, f, indent=4)  # Save the generated synthetic sales data to a JSON file with pretty printing

print("orders.json created!")    




