# Testing Guide

## Manual Test Cases

### Test Case 1: Complete Approved Loan Journey
**Customer**: C001 (Aarav Mehta)
**Steps**:
1. Select C001 from dropdown
2. Send: "I need a ₹3,00,000 personal loan for 36 months"
3. Verify: System extracts amount and tenure
4. Verify: Offer is displayed with interest rate
5. Send: "yes" to confirm offer
6. Verify: Moves to verification stage
7. Send: "confirm" for KYC
8. Send: "uploaded" for salary slip
9. Verify: Moves to underwriting
10. Verify: Shows EMI, FOIR, and APPROVED decision
11. Verify: Sanction letter PDF is generated
12. Check: `backend/data/events.json` has all events

**Expected Result**: Complete journey from Sales → Verification → Underwriting → Sanction

---

### Test Case 2: Referred Loan (KYC Pending)
**Customer**: C002 (Ritika Singh)
**Steps**:
1. Select C002
2. Send: "I need ₹2,50,000 for 24 months"
3. Confirm offer
4. Verify: KYC status shows PENDING
5. Send: "confirm" to proceed
6. Send: "uploaded" for salary slip
7. Verify: Decision is REFERRED

**Expected Result**: Application referred for human review

---

### Test Case 3: API Endpoints
**Test Offer Mart API**:
```bash
curl http://localhost:8000/offer-mart/offers/C001
```

**Test CRM API**:
```bash
curl http://localhost:8000/crm/kyc/C001
```

**Test Credit Bureau API**:
```bash
curl http://localhost:8000/credit-bureau/score/ABCDE1234F
```

**Test Events API**:
```bash
curl http://localhost:8000/events/C001
```

**Expected Result**: All APIs return valid JSON responses

---

### Test Case 4: Event Bus
**Steps**:
1. Complete a loan journey
2. Check `backend/data/events.json`
3. Verify events are logged with:
   - timestamp
   - customer_id
   - event_type
   - payload

**Expected Events**:
- SALES_UPDATE
- VERIFICATION_UPDATE
- UNDERWRITING_DECISION
- SANCTION_GENERATED

---

### Test Case 5: Sanction Letter Generation
**Steps**:
1. Complete an approved loan journey
2. Check `backend/sanctions/` folder
3. Open the PDF file
4. Verify PDF contains:
   - Customer ID
   - Loan amount
   - Tenure
   - Interest rate
   - EMI

**Expected Result**: Valid PDF file generated

---

## Automated Test Script (Optional)

Create `test_api.py` in backend folder:

```python
import requests
import json

BASE_URL = "http://localhost:8000"

def test_chat_endpoint():
    response = requests.post(
        f"{BASE_URL}/chat",
        json={
            "customer_id": "C001",
            "text": "I need ₹3,00,000 for 36 months",
            "context": None
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "reply" in data
    assert "context" in data
    print("✅ Chat endpoint works")

def test_offer_mart():
    response = requests.get(f"{BASE_URL}/offer-mart/offers/C001")
    assert response.status_code == 200
    print("✅ Offer Mart API works")

if __name__ == "__main__":
    test_chat_endpoint()
    test_offer_mart()
    print("All tests passed!")
```

Run with: `python test_api.py`

