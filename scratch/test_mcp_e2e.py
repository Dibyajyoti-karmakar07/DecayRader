import sys
import os
import logging

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')

from agent.mcp_agent import run_mcp_agent_sync
from agent.intelligence_prompts import build_intelligence_prompt, INTELLIGENCE_SYSTEM_PROMPT

customer_id = "CST-042"
prompt = build_intelligence_prompt(customer_id)
full_prompt = f"{INTELLIGENCE_SYSTEM_PROMPT}\n\n{prompt}"

print(f"Starting E2E Test for {customer_id}...")
response = run_mcp_agent_sync(full_prompt)

print("\n--- FINAL GEMINI RESPONSE ---")
print(response)
