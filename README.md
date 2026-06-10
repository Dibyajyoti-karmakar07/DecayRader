# DecayRader

<p align="center">
  <strong>An AI-powered B2B customer revenue decay detection and intervention platform.</strong>
</p>

## Problem Statement
In B2B SaaS, traditional churn detection methods operate too late. By the time a user cancels their subscription or a telemetry dashboard flags "Zero Logins," the customer has already mentally churned. **DecayRader** detects the subtle behavioral shifts (revenue decay) that precede actual churn and deploys an autonomous AI Copilot to prescribe actionable interventions to Customer Success Managers (CSMs).

## How DecayRader Works
1. **Detection Pipeline**: Ingests telemetry, product usage, and engagement data to calculate real-time Risk Scores and classify customer tiers (Gold, Silver, Bronze).
2. **AI Copilot**: An asynchronous Gemini-powered agent monitors at-risk accounts, processes historical interaction data, and prepares highly specific retention strategies.
3. **Human-in-the-Loop Approval**: CSMs review the AI's diagnosis, approve or modify the suggested action, and save it to the queue for immediate execution.

## Key Features
- **Customer Decay Detection**: ML-driven scoring of subtle engagement drop-offs.
- **Intervention Copilot**: Agentic AI that prescribes precise save plays (e.g., "Schedule QBR," "Send Integration Guide").
- **Customer Deep Dive**: Instant, dense 360° AI reports on any single account's health.
- **Tier Intelligence**: AI-summarized health assessments of entire customer segments (e.g., all Bronze Tier accounts).
- **Portfolio Intelligence**: Executive-level reporting on total business impact and strategic alignment.
- **Time Machine**: Analyze historical risk trends to see exactly when and how accounts decayed.
- **Human-in-the-Loop Approval**: Final say remains with the CSM before actions are dispatched.
- **MongoDB Persistence**: Real-time state management and intervention queuing.

---

## Architecture Overview & Tech Stack
- **Frontend**: Streamlit (with extensive custom CSS for a Vercel/Linear-inspired premium UI)
- **Backend/State**: MongoDB Atlas (persists customer profiles, telemetry, and pending actions)
- **AI Agent**: Google Gemini (via `google-genai`, utilizing structured JSON outputs and model fallbacks)
- **Data Engineering**: Pandas & Scikit-Learn for anomaly detection
- **Visualizations**: Plotly

---

## Installation & Environment Setup

### 1. Prerequisites
- Python 3.11+
- MongoDB Atlas Account (Free tier is sufficient)
- Google AI Studio Account (For Gemini API Key)

### 2. Clone and Install
```bash
git clone https://github.com/your-username/DecayRader.git
cd DecayRader
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Environment Configuration
Create a `.env` file in the root directory and populate it based on the provided `.env.example`:
```bash
cp .env.example .env
```
Populate `.env` with:
- `MONGODB_URI`: Your MongoDB connection string.
- `GEMINI_API_KEY`: Your Gemini API key.

---

## Database Setup & Seed Data

Because DecayRader requires historical data to generate intelligence, you must seed your MongoDB instance before launching the application.

1. Ensure your `.env` file is properly configured with your `MONGODB_URI`.
2. Run the seed script:
```bash
python Scripts/create_benchmark_dataset.py
```
This script will construct realistic mock B2B companies, inject behavioral telemetry, and push them to your database.

---

## Running The Application

Start the Streamlit application from the root directory:
```bash
streamlit run dashboard/app.py
```
The dashboard will be available at `http://localhost:8501`.

---

## Future Improvements
- Native CRM integrations (Salesforce, HubSpot) to automatically execute approved interventions.
- Fine-tuned proprietary local LLMs for enhanced data privacy.
- Streaming WebSockets for fully real-time telemetry updates.

## Contribution Guidelines
1. Fork the repository and create your feature branch (`git checkout -b feature/amazing-feature`).
2. Adhere to the existing design system outlined in `DESIGN.md`.
3. Ensure no global loading spinners leak when using `st.fragment()`.
4. Commit your changes (`git commit -m 'Add amazing feature'`).
5. Push to the branch (`git push origin feature/amazing-feature`).
6. Open a Pull Request.

## License
MIT License. See `LICENSE` for more information.
