# Multi-Agent Loan Approval System

Simple, isolated LangGraph demo for automated loan approval.

It adds a 5-agent flow without changing the old backend:

1. `ProfileAgent` checks age and income.
2. `CreditAgent` checks credit score thresholds.
3. `DocumentVerificationAgent` runs 3-stage verification: identity, income proof, fraud flag.
4. `UnderwritingAgent` calculates EMI and FOIR.
5. `SanctionAgent` generates a sanction letter for approved loans.

The graph has 6 nodes: profile, credit, documents, underwriting, decision router, and sanction.

FastAPI exposes the flow, and `langchain_helper.py` uses LangChain prompt formatting for the decision summary when LangChain is installed. If it is missing, the same summary is produced with plain Python.

## Run

```bash
cd langgraph_loan_system
pip install -r requirements.txt
copy .env.mock .env
python app.py
```

API runs at:

```text
http://localhost:8010
```

## Test

Open:

```text
GET /demo/customers
```

Then send one customer payload to:

```text
POST /loan/decide
```

Example:

```bash
curl -X POST http://localhost:8010/loan/decide \
  -H "Content-Type: application/json" \
  -d @sample_request.json
```

## Fallback Logic

If `langgraph` or `langchain` is not installed, the app does not fail. It uses the same agents in a plain deterministic Python fallback pipeline. The old backend remains untouched and can continue running as before.
