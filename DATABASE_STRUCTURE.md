# 📊 Database Structure Explanation

## ⚠️ Important Note: No Traditional Database

**I did NOT use a traditional database** (like MySQL, PostgreSQL, MongoDB, etc.)

Instead, I used **JSON files** as a simple file-based storage system. This is perfect for a **prototype/demo** because:
- ✅ No database setup required
- ✅ Easy to read and modify
- ✅ Works immediately
- ✅ Perfect for demonstration

---

## 📁 Data Storage Structure

### **Location:** `backend/data/`

All data is stored in JSON files in the `backend/data/` folder.

---

## 📋 Database Tables (JSON Files)

### 1. **customers.json** - Customer Master Data
**Purpose:** Stores all customer information

**Structure:**
```json
[
  {
    "customer_id": "C001",
    "name": "Aarav Mehta",
    "age": 28,
    "city": "Mumbai",
    "monthly_income": 85000,
    "existing_emi": 12000,
    "credit_score": 772,
    "preapproved_limit": 500000,
    "preapproved_interest": 13.5,
    "segment": "salaried"
  },
  ...
]
```

**Fields:**
- `customer_id` - Unique identifier (Primary Key)
- `name` - Customer name
- `age` - Customer age
- `city` - City of residence
- `monthly_income` - Monthly income in ₹
- `existing_emi` - Current EMI obligations
- `credit_score` - Credit score (705-785 range)
- `preapproved_limit` - Pre-approved loan limit
- `preapproved_interest` - Pre-approved interest rate
- `segment` - Customer segment (salaried/student)

**Records:** 12 customers (C001 to C012)

---

### 2. **offers.json** - Loan Offers
**Purpose:** Stores personalized loan offers for each customer

**Structure:**
```json
[
  {
    "customer_id": "C001",
    "max_amount": 500000,
    "tenure_options": [12, 24, 36],
    "base_interest": 13.5,
    "processing_fee_pct": 1.0
  },
  ...
]
```

**Fields:**
- `customer_id` - Foreign Key to customers.json
- `max_amount` - Maximum loan amount
- `tenure_options` - Available tenure options (months)
- `base_interest` - Base interest rate (% p.a.)
- `processing_fee_pct` - Processing fee percentage

**Records:** 12 offers (one per customer)

---

### 3. **kyc.json** - KYC Records
**Purpose:** Stores KYC (Know Your Customer) verification data

**Structure:**
```json
[
  {
    "customer_id": "C001",
    "pan": "ABCDE1234F",
    "aadhaar_masked": "XXXX-XXXX-1234",
    "kyc_status": "COMPLETED",
    "kyc_last_updated": "2024-10-01"
  },
  {
    "customer_id": "C002",
    "pan": "PQRSX5678Z",
    "kyc_status": "PENDING"
  },
  ...
]
```

**Fields:**
- `customer_id` - Foreign Key to customers.json
- `pan` - PAN card number
- `aadhaar_masked` - Masked Aadhaar number
- `kyc_status` - Status: "COMPLETED" or "PENDING"
- `kyc_last_updated` - Last update date (optional)

**Records:** 12 KYC records (one per customer)
**Status Distribution:**
- COMPLETED: 9 customers
- PENDING: 3 customers

---

### 4. **policies.json** - Underwriting Policies
**Purpose:** Stores business rules for loan approval

**Structure:**
```json
[
  {
    "policy_id": "POL001",
    "policy_name": "Credit Score Threshold",
    "min_credit_score_auto_approve": 725,
    "min_credit_score_refer": 650,
    "description": "Minimum credit score requirements"
  },
  {
    "policy_id": "POL002",
    "policy_name": "FOIR Limits",
    "max_foir_auto_approve": 0.5,
    "max_foir_refer": 0.6,
    "description": "Fixed Obligation to Income Ratio limits"
  },
  ...
]
```

**Fields:**
- `policy_id` - Policy identifier
- `policy_name` - Policy name
- Various threshold values
- `description` - Policy description

**Records:** 4 policy rules

---

### 5. **events.json** - Event Log (Generated at Runtime)
**Purpose:** Stores all events from the Event Bus (Data Lake)

**Structure:**
```json
[
  {
    "timestamp": "2025-12-02T10:15:30.123456",
    "customer_id": "C001",
    "event_type": "SALES_UPDATE",
    "payload": {
      "customer_id": "C001",
      "stage": "SALES",
      "loan_amount_requested": 300000,
      "loan_tenure_requested": 36,
      ...
    }
  },
  {
    "timestamp": "2025-12-02T10:16:45.789012",
    "customer_id": "C001",
    "event_type": "VERIFICATION_UPDATE",
    "payload": { ... }
  },
  ...
]
```

**Fields:**
- `timestamp` - Event timestamp (ISO format)
- `customer_id` - Customer ID
- `event_type` - Event type (SALES_UPDATE, VERIFICATION_UPDATE, etc.)
- `payload` - Full context/state at time of event

**Records:** Generated dynamically (grows with usage)
**Event Types:**
- `SALES_UPDATE` - Sales stage updates
- `VERIFICATION_UPDATE` - Verification stage updates
- `UNDERWRITING_DECISION` - Underwriting decisions
- `SANCTION_GENERATED` - Sanction letter generation

---

## 🔗 Data Relationships

```
customers.json (1) ──┐
                     ├──→ (1:1) offers.json
                     ├──→ (1:1) kyc.json
                     └──→ (1:Many) events.json
```

**Relationship Rules:**
- Each customer has **exactly 1** offer
- Each customer has **exactly 1** KYC record
- Each customer can have **many** events

---

## 📂 File Storage (Non-JSON)

### **backend/uploads/**
**Purpose:** Stores uploaded salary slips

**Format:** PDF files
**Naming:** `{customer_id}_salary_{date}.pdf`
**Example:** `C001_salary_2025-12-02.pdf`

---

### **backend/sanctions/**
**Purpose:** Stores generated sanction letters

**Format:** PDF files
**Naming:** `{customer_id}_sanction.pdf`
**Example:** `C001_sanction.pdf`

---

## 🔍 How Data is Accessed

### **Service Layer Pattern**

Each service reads from its corresponding JSON file:

1. **OfferMartService** → Reads `offers.json`
2. **CRMService** → Reads `kyc.json`
3. **CreditBureauService** → Reads `customers.json`
4. **EventBus** → Reads/Writes `events.json`

### **Example: Getting Customer Data**

```python
# CreditBureauService loads customers.json on startup
class CreditBureauService:
    def __init__(self):
        with open("backend/data/customers.json", 'r') as f:
            self.customers = json.load(f)
    
    def get_customer_data(self, customer_id):
        # Search in-memory list
        return next((c for c in self.customers 
                    if c["customer_id"] == customer_id), None)
```

---

## 📊 Data Summary

| File | Records | Purpose | Read/Write |
|------|---------|---------|------------|
| `customers.json` | 12 | Customer master data | Read-only |
| `offers.json` | 12 | Loan offers | Read-only |
| `kyc.json` | 12 | KYC records | Read-only |
| `policies.json` | 4 | Business rules | Read-only |
| `events.json` | Dynamic | Event log | Read/Write |
| `uploads/*.pdf` | Dynamic | Salary slips | Write |
| `sanctions/*.pdf` | Dynamic | Sanction letters | Write |

---

## 🔄 Data Flow

```
Application Start
    ↓
Services Load JSON Files into Memory
    ↓
    ├──→ OfferMartService.load_offers()
    ├──→ CRMService.load_kyc()
    ├──→ CreditBureauService.load_customers()
    └──→ EventBus.load_events()
    ↓
Runtime:
    - Services query in-memory data (fast)
    - EventBus writes to events.json (persistent)
    - FileService writes PDFs to disk
```

---

## 💡 Why JSON Files (Not a Database)?

### ✅ **Advantages for Prototype:**
1. **No Setup Required** - Works immediately
2. **Easy to Understand** - Human-readable format
3. **Easy to Modify** - Edit with any text editor
4. **Perfect for Demo** - Show data structure easily
5. **No Dependencies** - No database server needed

### ⚠️ **Limitations:**
1. **Not Scalable** - Can't handle millions of records
2. **No Transactions** - No ACID guarantees
3. **Concurrent Writes** - Could have issues with multiple users
4. **No Query Language** - Manual filtering/searching

### 🔄 **Upgrade Path (If Needed):**
- **SQLite** - Easy upgrade, same file-based approach
- **PostgreSQL** - For production scale
- **MongoDB** - If JSON structure is preferred
- **Redis** - For fast in-memory access

---

## 🎯 Summary

**What I Built:**
- ✅ 4 static JSON files (customers, offers, kyc, policies)
- ✅ 1 dynamic JSON file (events.json - grows over time)
- ✅ File storage for PDFs (uploads, sanctions)

**Total Data:**
- 12 customers
- 12 offers
- 12 KYC records
- 4 policy rules
- Dynamic event log
- Dynamic PDF files

**This is a file-based "database" perfect for prototyping!** 📁

