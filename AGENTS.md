# AGENTS.md

## Project Overview

DecayRader is an AI-powered customer decay detection platform built for the Google Cloud Rapid Agent Hackathon.

The system identifies early signs of customer disengagement before traditional churn metrics detect problems.

DecayRader combines:

* Behavioral feature engineering
* Isolation Forest anomaly detection
* Rule-based business scoring
* Gemini-powered intervention generation
* MongoDB storage
* Streamlit dashboard visualization

The goal is to help account managers identify at-risk customers early and take corrective action.

---

# Technology Stack

## Backend

* Python 3.11
* Pandas
* NumPy
* Scikit-learn
* PyMongo
* Google Gemini API

## Database

* MongoDB Atlas
* Database name: `DecayRader`

## Frontend

* Streamlit
* Plotly

## Design System

Follow the guidelines in:

* DESIGN.md

UI should resemble modern analytics products:

* Vercel
* Linear
* Stripe Dashboard
* Notion Analytics

Use:

* Dark theme
* Clean spacing
* Minimalist design
* High information density
* Professional B2B SaaS aesthetics

Avoid:

* Bright colors
* Cartoonish styling
* Excessive animations
* Unnecessary gradients
* Marketing-style landing pages

---

# Critical Project Rule

DO NOT create duplicate project structures.

DO NOT create:

* frontend/
* src/
* web/
* dashboard_v2/
* new_dashboard/
* duplicate DecayRader folders

Always work inside the existing structure.

Project root:

```text
DecayRader/
├── agent/
├── dashboard/
├── pipeline/
├── data/
├── evaluation/
├── Scripts/
├── AGENTS.md
├── DESIGN.md
├── requirements.txt
└── README.md
```

---

# Dashboard Structure

All dashboard work must occur inside:

```text
dashboard/
├── app.py
├── utils/
│   └── db.py
├── components/
│   ├── cards.py
│   └── charts.py
└── pages/
    ├── 01_overview.py
    ├── 02_risk_ranking.py
    ├── 03_customer_detail.py
    ├── 04_time_machine.py
    └── 05_agent_actions.py
```

Do not create new dashboard folders.

---

# MongoDB Connection

Database:

```python
DecayRader
```

Connection pattern:

```python
import os
import certifi
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

client = MongoClient(
    os.getenv("MONGODB_URI"),
    tlsCAFile=certifi.where(),
    serverSelectionTimeoutMS=5000
)

db = client["DecayRader"]
```

Always drop MongoDB IDs after loading into DataFrames:

```python
df.drop(columns=["_id"], errors="ignore")
```

---

# MongoDB Collections

## Customers

80 records

Fields:

* customer_id
* company_name
* city
* tier
* account_manager

Tier values:

* Gold
* Silver
* Bronze

---

## Orders

Approximately 3200 records

Fields:

* customer_id
* order_date
* order_value
* product_category

---

## features

80 records

Fields:

* customer_id
* gap_change_pct
* aov_change_pct
* diversity_delta

---

## risk_scores

80 records

Fields:

* customer_id
* risk_score
* risk_label
* aov_change_pct
* gap_change_pct
* diversity_delta
* business_risk_score
* anomaly_risk_score
* is_anomaly

Risk labels:

* Healthy
* Watch
* At Risk
* Critical

Risk ranges:

* Healthy = 0-30
* Watch = 31-50
* At Risk = 51-75
* Critical = 76-100

---

## interventions

Fields:

* customer_id
* company_name
* city
* tier
* account_manager
* risk_score
* risk_label
* decay_summary
* priority_reason
* likely_reason
* primary_action
* secondary_action
* outreach_message
* urgency
* model_used
* status
* approved_at
* follow_up_date
* completed_at
* note

Status values:

* pending
* completed
* cancelled

---

# Dashboard Pages

## 01_overview.py

Business health dashboard.

Show:

* Total Customers
* Critical Customers
* At Risk Customers
* Healthy Customers

Visualizations:

* Risk distribution donut chart
* Top 10 risky customers
* Recent interventions

---

## 02_risk_ranking.py

Customer risk table.

Features:

* Search
* Filtering
* Risk sorting
* Tier filtering

---

## 03_customer_detail.py

Single customer deep dive.

Show:

* Customer profile
* Risk score
* Signal breakdown
* Intervention history

---

## 04_time_machine.py

Flagship demo feature.

Show:

* Risk evolution over time
* Early decay detection
* Historical feature trends

This is the primary hackathon demonstration page.

---

## 05_agent_actions.py

Intervention management.

Tabs:

* Pending
* Completed
* Cancelled

Display:

* Recommended actions
* Follow-up schedule
* Outreach messages
* Model used

---

# Coding Standards

* Use type hints where practical
* Use pandas DataFrames
* Use Plotly for charts
* Handle MongoDB failures gracefully
* Avoid hardcoded values
* Use reusable helper functions
* Keep pages modular

---

---

# Intelligence Reports Module

DecayRader includes an AI-powered Intelligence Reports layer.

Purpose:

Transform raw customer risk signals into executive-level business insights that are immediately understandable by account managers, customer success teams, and hackathon judges.

Intelligence Reports must reuse existing data sources and existing Gemini integrations.

Do not create separate agent architectures for intelligence reports.

Do not create duplicate recommendation workflows.

The Intelligence layer is an analytical extension of existing DecayRader functionality.

---

## Intelligence Report Types

### Tier Intelligence

Analyze customer segments by tier:

* Gold
* Silver
* Bronze

Reports may include:

* Customer count
* Average risk score
* Risk label distribution
* Top risk drivers
* Highest-risk customers
* Executive summary
* Recommended portfolio actions

Use only documented schema fields.

---

### Customer Deep Dive

Generate a detailed business intelligence report for an individual customer.

Reports may include:

* Customer profile
* Risk assessment
* Behavioral signal analysis
* Risk driver analysis
* Business impact assessment
* Retention opportunities
* Executive recommendation

The report should resemble an executive account review rather than a technical diagnostic report.

---

### Portfolio Risk Analysis

Analyze the highest-risk customers across the portfolio.

Reports may include:

* Executive summary
* Risk concentration
* Tier breakdown
* Common behavioral patterns
* Emerging decay trends
* Business impact assessment
* Recommended intervention strategy

Portfolio reports should focus on actionable business insights.

---

## Dashboard Placement

Intelligence Reports should live inside the existing dashboard structure.

Do not create new dashboard applications.

Preferred pages:

* 01_overview.py
* 03_customer_detail.py

Additional pages may be added only when necessary and must remain inside:

dashboard/pages/

---

## Gemini Usage Rules

Gemini should be used to generate:

* Executive summaries
* Business interpretations
* Risk narratives
* Portfolio insights

Gemini should NOT replace:

* Risk scoring
* Feature engineering
* Rule-based calculations
* Anomaly detection

Analytics remain deterministic.

Gemini provides explanation and business context.

---

## Hackathon Design Goal

All intelligence reports should be:

* Executive-friendly
* Business-focused
* Concise
* Actionable

A non-technical judge should be able to understand the report within 30 seconds.

Avoid technical jargon whenever possible.

# Output Rules For Agents

When asked to modify code:

* Edit existing files whenever possible
* Do not create duplicate implementations
* Return complete runnable code
* Do not generate pseudocode
* Do not generate placeholder functions
* Do not invent MongoDB field names
* Use only documented schema fields from this file
