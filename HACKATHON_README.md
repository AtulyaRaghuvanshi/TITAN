# 🏆 Hackathon Loan Approval Chatbot

A chat-style loan approval system with **pre-approved instant approval** and **detailed evaluation** paths.

## 🎯 Features

### ✅ Pre-Approved Instant Approval Path
- **No file uploads required**
- Instant approval for pre-approved customers
- PDF sanction letter generated immediately
- Friendly congratulatory messages

### ✅ Detailed Evaluation Path
- Collects employment, income, EMIs, tenure
- KYC document uploads (ID proof, Address proof, Income proof)
- Eligibility evaluation based on policies.json
- Smart amount suggestions if initial request doesn't qualify
- PDF sanction letter for approved loans

## 🚀 Quick Start

### Backend Setup

```bash
cd backend
pip install -r requirements.txt
python main_hackathon.py
```

The API will run on `http://localhost:8000`

### Frontend Setup

The existing frontend (`frontend/`) works with this new backend. Just update the API endpoint if needed.

Or use the API directly:

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello", "context": null}'
```

## 📋 Complete Flow

### 1. Initial Conversation

The chatbot collects:
- **Full name**
- **Mobile number** (10 digits)
- **City**
- **Loan amount** (e.g., ₹3,00,000 or 3 lakh)
- **Purpose** (optional, can skip)

**Example:**
```
User: "Hello"
Bot: "Hello! Welcome to our loan application service. 😊
      To get started, could you please tell me your **full name**?"

User: "Aarav Mehta"
Bot: "Nice to meet you, Aarav Mehta! 👋
      Could you please share your registered mobile number?"

User: "9876543210"
Bot: "Thank you! Mobile number registered: 9876543210
      Which **city** are you located in?"

User: "Mumbai"
Bot: "Great! City noted: Mumbai
      What **loan amount** are you looking for? (e.g., ₹3,00,000 or 3 lakh)"

User: "I need 3 lakh"
Bot: "Perfect! You're looking for ₹3,00,000.
      **Optional:** What is the purpose of this loan? (e.g., Home renovation, Education, etc.)
      Or just type 'skip' to proceed."
```

### 2. Customer Matching

The system tries to match the customer by **name + mobile** in `customers.json`.

- **If matched** → Check for pre-approved offer
- **If not matched** → New customer, go to detailed evaluation

### 3. Pre-Approved Path (Instant Approval)

**If customer has pre-approved offer:**

```
Bot: "🎉 **Congratulations!** 

Our company already trusts you – you're on our **pre-approved list**! 

You are eligible for an instant loan of **₹3,00,000** at **13.5%** interest.

This is an **instant approval** – no documents or waiting required! ⚡

**Do you want to proceed with this instant loan approval?** (Type 'yes' to confirm, or 'no' to decline)"

User: "yes"
Bot: "✅ **Your loan has been approved instantly!** 🎊

**Loan Details:**
- Loan ID: LOAN_0001
- Approved Amount: ₹3,00,000
- Interest Rate: 13.5% p.a.
- Approval Type: Instant Pre-Approved

**Sanction Letter:**
Your sanction letter has been generated and saved at:
`backend/sanctions/SESS_ABC123_sanction_instant.pdf`

Thank you for choosing us! Your loan is ready. 🚀"
```

**Events logged:**
- `session_started`
- `preapproved_instant_approval_confirmed`
- `sanction_letter_generated`

### 4. Detailed Evaluation Path (Not Pre-Approved)

**If customer is NOT pre-approved:**

```
Bot: "We could not find you in our pre-approved list. 

Don't worry, we can still process your loan – we just need a few more details and documents. 😊

Let's start with some basic information:

**What is your employment type?**
- Salaried
- Self-employed  
- Student
- Other

Please type one of the above options."

User: "Salaried"
Bot: "Great! Employment type: Salaried
      **What is your monthly income?** (e.g., ₹50,000)"

User: "85000"
Bot: "Thank you! Monthly income: ₹85,000
      **Do you have any existing EMIs or monthly loan obligations?**
      If yes, please enter the total monthly EMI amount. If no, type '0' or 'none'."

User: "12000"
Bot: "Noted! Existing EMIs: ₹12,000
      **What loan tenure would you prefer?** (in months, e.g., 12, 24, 36, 48, 60)"

User: "36"
Bot: "Perfect! Preferred tenure: 36 months
      **Do you consent to a credit bureau check?** (Type 'yes' or 'no')"

User: "yes"
Bot: "Thank you! Now we need to collect some documents for KYC verification.

      **Please upload your ID proof** (PAN/Aadhaar).
      For this demo, type 'uploaded' after you've uploaded the file."

User: "uploaded"
Bot: "✅ ID proof received!

      **Please upload your address proof** (Aadhaar/Utility bill).
      Type 'uploaded' when done."

User: "uploaded"
Bot: "✅ Address proof received!

      **Please upload your income proof** (Latest salary slip or 3-month bank statement).
      Type 'uploaded' when done."

User: "uploaded"
Bot: "✅ All documents received! Thank you.

      Now let me evaluate your eligibility based on our policies..."

[System evaluates eligibility using policies.json]

Bot: "✅ **Good news!** Based on your details and documents, your loan is **approved**! 🎉

**Loan Details:**
- Loan ID: LOAN_0002
- Approved Amount: ₹3,00,000
- Interest Rate: 14.0% p.a.
- Tenure: 36 months
- EMI: ₹10,234.56
- Approval Type: After Evaluation

**Sanction Letter:**
Your sanction letter has been generated: `backend/sanctions/SESS_XYZ789_sanction_evaluated.pdf`

Thank you for choosing us! 🚀"
```

**Events logged:**
- `session_started`
- `employment_details_collected`
- `income_details_collected`
- `kyc_documents_uploaded`
- `eligibility_evaluated`
- `loan_approved_after_evaluation`
- `sanction_letter_generated`

### 5. Rejection / Amount Suggestion

If eligibility check fails but a lower amount would work:

```
Bot: "We cannot approve ₹5,00,000, but we can offer **₹3,50,000** based on your profile.

**Would you like to proceed with ₹3,50,000?** (Type 'yes' to accept, 'no' to decline)"
```

If no amount qualifies:

```
Bot: "We're sorry, but we are unable to approve a loan at this moment based on our current policies.

**Reason:** Credit score 600 is below minimum requirement of 720

Please feel free to reach out to us again in the future. 😊"
```

## 📊 Data Files

### `customers.json`
- 12 customers with mobile numbers
- Pre-approved limits and interest rates
- Credit scores

### `offers.json`
- Pre-approved offers matching customers
- Max amount, interest rate, tenure options

### `policies.json`
- Eligibility rules:
  - Minimum credit score: 720
  - Max EMI to income ratio: 0.5 (50%)
  - Minimum monthly income: ₹30,000
  - Maximum tenure: 60 months

### `kyc.json` (dynamic)
- KYC document uploads
- Document types: ID_PROOF, ADDRESS_PROOF, INCOME_PROOF

### `loans.json` (dynamic)
- Approved loans
- Loan ID, customer details, approval type

### `events.json` (dynamic)
- Complete event trail
- All user interactions and system decisions

## 🔧 API Endpoints

### `POST /chat`
Main chat endpoint

**Request:**
```json
{
  "text": "User message",
  "context": null  // or previous context
}
```

**Response:**
```json
{
  "reply": "Bot response",
  "context": {
    "stage": "INITIAL",
    "customer_name": "Aarav Mehta",
    ...
  }
}
```

### `GET /customers/{customer_id}`
Get customer details

### `GET /offers/{customer_id}`
Get pre-approved offer

### `GET /loans/{session_id}`
Get loan by session ID

### `GET /events/{session_id}`
Get events for a session

## 🎯 Testing Scenarios

### Scenario 1: Pre-Approved Customer (Instant Approval)
1. Name: "Aarav Mehta"
2. Mobile: "9876543210"
3. City: "Mumbai"
4. Amount: "3 lakh"
5. Purpose: "skip"
6. Confirm: "yes"

**Expected:** Instant approval, PDF generated

### Scenario 2: New Customer (Detailed Evaluation)
1. Name: "John Doe"
2. Mobile: "9999999999"
3. City: "Delhi"
4. Amount: "2 lakh"
5. Employment: "Salaried"
6. Income: "50000"
7. EMIs: "0"
8. Tenure: "36"
9. Consent: "yes"
10. Upload all 3 documents: "uploaded" (3 times)

**Expected:** Evaluation, approval/rejection based on policies

### Scenario 3: Amount Suggestion
1. Use new customer with low income
2. Request high amount (e.g., ₹10,00,000)
3. System suggests lower amount

**Expected:** Amount suggestion, user can accept/decline

## 📝 Key Functions

- `findCustomer(name, mobile)` - Match customer in database
- `findPreapprovedOffer(customer_id)` - Check for pre-approved offer
- `logEvent(event_type, payload)` - Log events to events.json
- `evaluateEligibility(...)` - Evaluate based on policies.json
- `generateSanctionLetterPdf(...)` - Generate PDF sanction letter

## 🎨 Demo Tips

1. **Start with pre-approved customer** to show instant approval
2. **Show new customer flow** to demonstrate detailed evaluation
3. **Open events.json** to show complete event trail
4. **Show generated PDFs** in sanctions/ folder
5. **Demonstrate amount suggestion** for edge cases

## 🚀 Ready for Hackathon!

The system is fully functional and ready to demo. All flows are implemented with friendly, conversational messages perfect for a hackathon presentation! 🎉

