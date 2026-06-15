# ✅ Pre-Approval System Explanation

## Yes! All Customers Are Pre-Approved

**Both `customers.json` and `offers.json` contain data for PRE-APPROVED customers only.**

---

## 🎯 What is Pre-Approval?

**Pre-approval** means the NBFC has already:
1. ✅ Checked the customer's credit history
2. ✅ Verified their income
3. ✅ Decided: "This customer is eligible for a loan"
4. ✅ Set a maximum loan limit (pre-approved limit)
5. ✅ Set an interest rate (pre-approved interest rate)

**So when the customer applies, they're not starting from scratch - they already have an approved offer waiting!**

---

## 📊 How Pre-Approval Works in This System

### **Step 1: Pre-Approval Data (customers.json)**

Each customer has pre-approval information:

```json
{
  "customer_id": "C001",
  "name": "Aarav Mehta",
  "credit_score": 772,
  "monthly_income": 85000,
  "preapproved_limit": 500000,      ← Maximum loan they can get
  "preapproved_interest": 13.5,     ← Interest rate for them
  ...
}
```

**Meaning:**
- Customer C001 is **pre-approved** for up to ₹5,00,000
- At an interest rate of **13.5%** p.a.
- This was decided **before** they applied (maybe based on their credit score, income, etc.)

---

### **Step 2: Offers Based on Pre-Approval (offers.json)**

The offers match the pre-approved limits:

```json
{
  "customer_id": "C001",
  "max_amount": 500000,              ← Matches preapproved_limit
  "base_interest": 13.5,             ← Matches preapproved_interest
  "tenure_options": [12, 24, 36],
  "processing_fee_pct": 1.0
}
```

**Relationship:**
- `offers.json` → `max_amount` = `customers.json` → `preapproved_limit`
- `offers.json` → `base_interest` = `customers.json` → `preapproved_interest`

---

## 🔄 The Pre-Approval Flow

```
┌─────────────────────────────────────────┐
│  BEFORE: Customer is Pre-Approved      │
│  (This happened earlier)             │
└─────────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────┐
│  customers.json                        │
│  - preapproved_limit: ₹5,00,000        │
│  - preapproved_interest: 13.5%          │
└─────────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────┐
│  offers.json                           │
│  - max_amount: ₹5,00,000               │
│  - base_interest: 13.5%                 │
└─────────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────┐
│  Customer Applies: "I need ₹3,00,000"   │
└─────────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────┐
│  Sales Agent Checks:                   │
│  - Requested: ₹3,00,000                │
│  - Pre-approved limit: ₹5,00,000 ✅     │
│  - Within limit? YES!                  │
└─────────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────┐
│  System Shows Offer:                   │
│  "You're pre-approved! Here's your      │
│   offer: ₹3,00,000 at 13.5%"           │
└─────────────────────────────────────────┘
```

---

## 📋 Examples from the Data

### **Example 1: C001 - Aarav Mehta**
```json
customers.json:
  "preapproved_limit": 500000,
  "preapproved_interest": 13.5

offers.json:
  "max_amount": 500000,        ← Same!
  "base_interest": 13.5        ← Same!
```

**Meaning:** C001 is pre-approved for up to ₹5 lakh at 13.5% interest.

---

### **Example 2: C002 - Ritika Singh**
```json
customers.json:
  "preapproved_limit": 300000,
  "preapproved_interest": 14.25

offers.json:
  "max_amount": 300000,        ← Same!
  "base_interest": 14.25       ← Same!
```

**Meaning:** C002 is pre-approved for up to ₹3 lakh at 14.25% interest.

---

### **Example 3: C003 - Vikram Reddy**
```json
customers.json:
  "preapproved_limit": 800000,
  "preapproved_interest": 12.75

offers.json:
  "max_amount": 800000,        ← Same!
  "base_interest": 12.75       ← Same!
```

**Meaning:** C003 is pre-approved for up to ₹8 lakh at 12.75% interest (better rate because higher credit score).

---

## 🎯 Why Pre-Approval?

### **Real-World Scenario:**
1. NBFC runs credit checks on potential customers
2. Identifies customers with good credit scores
3. Pre-approves them for loans (sends SMS/email: "You're pre-approved for ₹5 lakh!")
4. When customer applies, they already know they're eligible

### **In This Prototype:**
- All 12 customers are **already pre-approved**
- They have **pre-approved limits** (₹3 lakh to ₹10 lakh)
- They have **pre-approved interest rates** (12.5% to 14.5%)
- When they apply, the system checks: "Is their request within the pre-approved limit?"

---

## ✅ Verification in Code

### **Offer Mart Service Checks Pre-Approval:**

```python
# In offer_mart_service.py
def get_offer_by_amount(self, customer_id, requested_amount):
    offers = self.get_offers(customer_id)
    
    # Filter offers that are within the requested amount
    valid_offers = [o for o in offers 
                   if o.get("max_amount", 0) >= requested_amount]
    
    # max_amount comes from preapproved_limit!
    # So we're checking: requested <= preapproved_limit
```

**This ensures:** Customer can only get offers up to their pre-approved limit.

---

## 📊 Pre-Approval Limits Summary

| Customer | Pre-Approved Limit | Interest Rate | Credit Score |
|----------|-------------------|---------------|--------------|
| C001 | ₹5,00,000 | 13.5% | 772 |
| C002 | ₹3,00,000 | 14.25% | 710 |
| C003 | ₹8,00,000 | 12.75% | 785 |
| C004 | ₹6,00,000 | 13.0% | 745 |
| C005 | ₹10,00,000 | 12.5% | 750 |
| ... | ... | ... | ... |

**Pattern:** Higher credit score → Higher pre-approved limit + Lower interest rate

---

## 🎯 Summary

**Yes, both files are for pre-approved customers:**

1. ✅ **customers.json** contains:
   - Pre-approved limits (`preapproved_limit`)
   - Pre-approved interest rates (`preapproved_interest`)

2. ✅ **offers.json** contains:
   - Offers based on pre-approved limits (`max_amount`)
   - Interest rates matching pre-approved rates (`base_interest`)

3. ✅ **All 12 customers** are pre-approved
   - They have different limits based on credit scores
   - They have different interest rates based on risk

4. ✅ **When customer applies:**
   - System checks if requested amount ≤ pre-approved limit
   - If yes → Shows offer
   - If no → Would reject (but in this prototype, all requests are within limits)

**This matches your requirement: "All customers are already pre-approved"** ✅

