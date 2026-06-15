# TITAN NBFC Prototype

AI-Powered Loan Application Journey System

## Project Structure

```
titan-nbfc-prototype/
  backend/
    main.py                    # FastAPI application
    data/
      customers.json          # Synthetic customer data (12 customers)
      offers.json             # Loan offers per customer
      kyc.json                # KYC records
      policies.json           # Underwriting policies
      events.json             # Event bus data (generated at runtime)
    agents/
      master_engine.py        # Master AI orchestrator
      sales_agent.py          # Sales agent
      verification_agent.py   # Verification agent
      underwriting_agent.py   # Underwriting agent
      sanction_agent.py       # Sanction letter generator
    services/
      offer_mart_service.py   # Mock Offer Mart server
      crm_service.py          # Mock CRM server
      credit_bureau_service.py # Mock Credit Bureau API
      file_service.py         # File upload service
      event_bus.py            # Event bus / Data plane
    sanctions/                # Generated sanction letters (PDFs)
    uploads/                  # Uploaded salary slips
  frontend/
    src/
      App.jsx                 # Main React component
      api.js                  # API client
      App.css                 # Styles
      main.jsx                # React entry point
    index.html
    vite.config.js
    package.json
```

## Features

- **AI Sales Agent**: Handles loan amount, tenure, and offer selection
- **AI Verification Agent**: Manages KYC verification and salary slip upload
- **AI Underwriting Agent**: Performs credit checks, EMI calculation, and FOIR analysis
- **AI Sanction Agent**: Generates PDF sanction letters
- **Master Engine**: Orchestrates the entire loan journey workflow
- **Event Bus**: Tracks all events for data lake / analytics
- **Mock Services**: Simulates external systems (Offer Mart, CRM, Credit Bureau)

## Setup Instructions

### Backend Setup

1. Navigate to backend directory:
```bash
cd backend
```

2. Create a virtual environment (recommended):
```bash
python -m venv venv
# On Windows:
venv\Scripts\activate
# On Linux/Mac:
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run the backend server:
```bash
python main.py
```

The backend will run on `http://localhost:8000`

### Frontend Setup

1. Navigate to frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Run the development server:
```bash
npm run dev
```

The frontend will run on `http://localhost:3000`

## Usage

1. Start both backend and frontend servers
2. Open `http://localhost:3000` in your browser
3. Select a customer from the dropdown (e.g., C001 - Aarav Mehta)
4. Start a conversation:
   - Try: "I need a ₹3,00,000 personal loan for 36 months"
   - Follow the prompts to complete the loan journey

## Demo Flow

1. **Sales Stage**: 
   - User requests loan amount and tenure
   - System fetches offers from Offer Mart
   - User confirms offer

2. **Verification Stage**:
   - System checks KYC status
   - User confirms KYC details
   - User uploads salary slip (type "uploaded" for demo)

3. **Underwriting Stage**:
   - System fetches credit score from Credit Bureau
   - Calculates EMI and FOIR
   - Makes approval decision (APPROVED/REJECTED/REFERRED)

4. **Sanction Stage** (if approved):
   - Generates PDF sanction letter
   - Provides download link

## API Endpoints

- `POST /chat` - Main chat endpoint for loan journey
- `GET /offer-mart/offers/{customer_id}` - Get offers for customer
- `GET /crm/kyc/{customer_id}` - Get KYC status
- `GET /credit-bureau/score/{pan}` - Get credit score by PAN
- `POST /files/upload-salary-slip` - Upload salary slip
- `GET /events/{customer_id}` - Get events for customer
- `GET /events` - Get all events

## Synthetic Data

The system includes 12 synthetic customers with:
- Customer details (name, age, city, income)
- Credit scores (ranging from 705 to 785)
- Pre-approved loan limits
- KYC status (some completed, some pending)
- Personalized offers

## Architecture

- **Green Boxes (Agents)**: Implemented as Python classes with `handle()` methods
- **Yellow Boxes (Data Plane)**: Event bus that publishes events to `events.json`
- **Purple Boxes (Integrations)**: Mock services simulating external systems

## Notes

- This is a prototype for demonstration purposes
- File uploads are simulated (type "uploaded" to proceed)
- All external integrations are mocked
- Events are stored in JSON format (can be upgraded to Kafka/SQLite)
- Sanction letters are generated as PDFs using FPDF

## License

This is a prototype project for EY TITAN team demonstration.

