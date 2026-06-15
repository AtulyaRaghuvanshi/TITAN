# Quick Start Guide

## 🚀 Immediate Next Steps

### 1. Test the Application

**Step 1: Start Backend**
```bash
cd backend
pip install -r requirements.txt
python main.py
```
✅ Should see: `Uvicorn running on http://0.0.0.0:8000`

**Step 2: Start Frontend** (in a new terminal)
```bash
cd frontend
npm install
npm run dev
```
✅ Should see: `Local: http://localhost:3000`

**Step 3: Test the Flow**
1. Open `http://localhost:3000` in browser
2. Select customer: **C001 - Aarav Mehta**
3. Send message: `"I need a ₹3,00,000 personal loan for 36 months"`
4. Follow the conversation flow

### 2. Verify Key Features

✅ **Sales Agent**: Should extract amount and tenure, show offer
✅ **Verification Agent**: Should check KYC, ask for salary slip
✅ **Underwriting Agent**: Should calculate EMI/FOIR, make decision
✅ **Sanction Agent**: Should generate PDF (if approved)
✅ **Event Bus**: Check `backend/data/events.json` for event trail

### 3. Test Different Scenarios

**Scenario 1: Approved Loan (C001)**
- Customer: C001 (Credit Score: 772)
- Request: ₹3,00,000 for 36 months
- Expected: APPROVED → Sanction letter generated

**Scenario 2: Referred Loan (C002)**
- Customer: C002 (Credit Score: 710, KYC PENDING)
- Request: ₹2,50,000 for 24 months
- Expected: REFERRED (needs human review)

**Scenario 3: Rejected Loan**
- Try a customer with low credit score or high FOIR
- Expected: REJECTED with reason

## 🔍 Verification Checklist

- [ ] Backend starts without errors
- [ ] Frontend loads and shows customer dropdown
- [ ] Can select a customer
- [ ] Chat interface responds to messages
- [ ] Sales stage completes successfully
- [ ] Verification stage works (KYC + salary slip)
- [ ] Underwriting calculates EMI and FOIR correctly
- [ ] Decision is made (APPROVED/REJECTED/REFERRED)
- [ ] Sanction letter PDF is generated (if approved)
- [ ] Events are logged in `backend/data/events.json`
- [ ] Context panel shows current stage and status

## 🐛 Troubleshooting

**Backend won't start:**
- Check Python version (3.8+)
- Verify all dependencies installed: `pip install -r requirements.txt`
- Check if port 8000 is available

**Frontend won't start:**
- Check Node.js version (16+)
- Run `npm install` again
- Check if port 3000 is available

**Import errors:**
- Make sure you're running `python main.py` from the `backend/` directory
- Check that `__init__.py` files exist in `agents/` and `services/` folders

**CORS errors:**
- Verify backend CORS allows `http://localhost:3000`
- Check browser console for specific error

## 📊 Demo Presentation Tips

1. **Start with Architecture**: Show the diagram and explain each component
2. **Live Demo**: Walk through a complete loan journey
3. **Show Event Trail**: Open `events.json` to demonstrate Data Lake
4. **Show Sanction Letter**: Open generated PDF
5. **Test Edge Cases**: Show different customer scenarios

## 🎯 Next Enhancements (Optional)

- Add authentication/login
- Real file upload (PDF parsing)
- Database instead of JSON files
- Real-time notifications
- Admin dashboard for events
- Integration with real credit bureau APIs
- Multi-language support
- Voice input/output

