# CompliCheck POC - Quick Start Guide

## ✅ Setup Complete!

Your FastAPI + React 18 + Tailwind CSS stack is ready to go!

---

## Start the Application (2 Terminals)

### Terminal 1: Backend (FastAPI)
```bash
cd backend
python main.py
```
**Runs on:** http://localhost:8000
**API Docs:** http://localhost:8000/docs

### Terminal 2: Frontend (React + Vite)
```bash
cd frontend
npm run dev
```
**Runs on:** http://localhost:5173

---

## Next Steps: Build React Components

Based on the Figma mockups, here are the components to build:

### 1. Login Page (`src/pages/Login.jsx`)
- Mock authentication
- Colab branding
- Username/Password fields

### 2. Dashboard (`src/pages/Dashboard.jsx`)
- Header with logo
- Three button options

### 3. Basic Info Form (`src/pages/BasicInfo.jsx`)
- Progress stepper (Step 1/3)
- Project description
- Address
- Consent type dropdown

### 4. Upload Page (`src/pages/Upload.jsx`)
- Progress stepper (Step 2/3)
- File upload buttons
- Site plan (required)
- Building plan (optional)

### 5. Results Page (`src/pages/Results.jsx`)
- Progress stepper (Step 3/3)
- Completeness column
- Compliance column
- Download report buttons

---

## Component Structure

```
src/
├── components/
│   ├── Layout/
│   │   └── Header.jsx          # Colab logo + user menu
│   ├── Stepper/
│   │   └── ProgressStepper.jsx # 3-step progress
│   ├── Forms/
│   │   ├── LoginForm.jsx
│   │   ├── BasicInfoForm.jsx
│   │   └── FileUpload.jsx
│   └── Results/
│       ├── CompletenessColumn.jsx
│       └── ComplianceColumn.jsx
├── pages/
│   ├── Login.jsx
│   ├── Dashboard.jsx
│   ├── BasicInfo.jsx
│   ├── Upload.jsx
│   └── Results.jsx
├── utils/
│   ├── api.js                  # Axios API calls
│   └── auth.js                 # Auth helpers
├── App.jsx                     # Router setup
└── main.jsx                    # Entry point
```

---

## API Integration

All API endpoints are ready in the backend:

```javascript
// Example API calls (use axios)
import axios from 'axios';

const API_URL = 'http://localhost:8000';

// Login
await axios.post(`${API_URL}/api/auth/login`, {
  username: 'test',
  password: 'test'
});

// Create pre-check
const response = await axios.post(`${API_URL}/api/precheck/create`);
const precheckId = response.data.precheck_id;

// Upload files
const formData = new FormData();
formData.append('site_plan', file);
await axios.post(`${API_URL}/api/precheck/${precheckId}/upload`, formData);

// Start processing
await axios.post(`${API_URL}/api/precheck/${precheckId}/process`);

// Poll status
const status = await axios.get(`${API_URL}/api/precheck/${precheckId}/status`);

// Download report
window.open(`${API_URL}/api/precheck/${precheckId}/download/site_plan`);
```

---

## Tailwind Classes (Colab Branding)

### Colors
```jsx
<button className="bg-colab-navy text-white">Primary</button>
<button className="bg-colab-teal text-white">Secondary</button>
<div className="text-colab-blue">Link</div>
```

### Pre-built Classes
```jsx
<button className="btn-primary">Primary Button</button>
<button className="btn-secondary">Secondary Button</button>
<input className="input-field" />
<div className="card">Card Content</div>
```

---

## Testing the Flow

1. Start backend and frontend
2. Open http://localhost:5173
3. Login with any credentials
4. Click "New pre-check"
5. Fill basic info → Next
6. Upload `data/10-North-Point_REV-A_Lot-2.pdf` → Next
7. Wait for processing (~90-120s)
8. View results and download report

---

## Project Status

✅ **DONE:**
- FastAPI backend with async file processing
- React 18 frontend scaffolding
- Tailwind CSS configuration
- API endpoints for full workflow
- Integration with compliCheckV2.py pipeline

⏳ **TODO:**
- Build React components from Figma designs
- Implement routing (React Router)
- Add loading states and error handling
- Style with Tailwind to match Figma
- Test end-to-end flow

---

## Files Created

### Backend
- `backend/main.py` - FastAPI application (400+ lines)
- `backend/requirements.txt` - Python dependencies

### Frontend
- `frontend/` - React 18 project (Vite scaffold)
- `frontend/tailwind.config.js` - Tailwind configuration
- `frontend/src/index.css` - Tailwind directives + custom classes

### Documentation
- `FRONTEND_SETUP.md` - Complete setup guide
- `QUICKSTART_FRONTEND.md` - This file

---

## Need Help?

- **Backend API Docs:** http://localhost:8000/docs
- **FastAPI Docs:** https://fastapi.tiangolo.com/
- **React Docs:** https://react.dev/
- **Tailwind Docs:** https://tailwindcss.com/docs

---

**Ready to code!** 🚀

Start by building the Login page, then work through the flow step by step.
