import os
import sys

_project_root = os.path.dirname(os.path.abspath(__file__))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from agent.intelligence_client import (
    generate_customer_intelligence,
    generate_tier_analysis,
    generate_portfolio_analysis
)
from utils.db import connect_to_mongo
from agent.agent_runner import load_data, get_risky_customers
from agent.gemini_client import setup_gemini_client
from utils.agent_worker import create_worker_state, start_worker

def verify():
    print("1. Connecting to DB...")
    db = connect_to_mongo()
    
    print("2. Verifying Deep Dive...")
    cust = db["Customers"].find_one()
    if cust:
        cid = cust["customer_id"]
        res = generate_customer_intelligence(cid)
        assert res is not None, "Deep Dive failed to generate"
        print("   ✅ Deep Dive passed")
        
    print("3. Verifying Tier Intelligence...")
    res = generate_tier_analysis("Gold")
    assert res is not None, "Tier Intelligence failed to generate"
    print("   ✅ Tier Intelligence passed")
    
    print("4. Verifying Portfolio Intelligence...")
    res = generate_portfolio_analysis()
    assert res is not None, "Portfolio Intelligence failed to generate"
    print("   ✅ Portfolio Intelligence passed")
    
    print("5. Verifying Intervention Agent...")
    combined = load_data(db)
    risky = get_risky_customers(combined)
    customers = [r.to_dict() for _, r in risky.iterrows()][:1] # Just test one
    
    gemini = setup_gemini_client()
    state = create_worker_state(customers, 1)
    
    # Run synchronously for test
    from agent.agent_runner import process_single_customer
    for i, c in enumerate(state["customers"]):
        rec = process_single_customer(gemini, c)
        assert rec is not None, "Intervention Agent failed"
    print("   ✅ Intervention Agent passed")
    
    print("ALL VERIFICATIONS PASSED")

if __name__ == "__main__":
    verify()
