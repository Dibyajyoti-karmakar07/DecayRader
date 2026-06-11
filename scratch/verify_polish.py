import sys
import os

sys.path.insert(0, os.path.abspath('dashboard'))

try:
    import dashboard.pages.01_overview
except SyntaxError:
    pass
except Exception as e:
    print("01_overview failed:", e)

try:
    import dashboard.pages.02_risk_ranking
except SyntaxError:
    pass
except Exception as e:
    print("02_risk_ranking failed:", e)

try:
    import dashboard.pages.03_customer_detail
except SyntaxError:
    pass
except Exception as e:
    print("03_customer_detail failed:", e)

try:
    import dashboard.pages.04_time_machine
except SyntaxError:
    pass
except Exception as e:
    print("04_time_machine failed:", e)

try:
    import dashboard.pages.05_agent_actions
except SyntaxError:
    pass
except Exception as e:
    print("05_agent_actions failed:", e)

try:
    import dashboard.pages.agent_console
except SyntaxError:
    pass
except Exception as e:
    print("agent_console failed:", e)

print("Imports completed.")
