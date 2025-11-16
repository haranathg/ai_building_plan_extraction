# CompliCheck POC Frontend Setup

## Technology Stack

### Backend
- **Python 3.9+**
- **FastAPI** - Modern async web framework
- **Uvicorn** - ASGI server
- **Pydantic** - Data validation

### Frontend
- **React 18** - UI framework
- **Vite** - Build tool and dev server
- **Tailwind CSS** - Utility-first CSS framework
- **React Router** - Client-side routing
- **Axios** - HTTP client

---

## Project Structure

```
├── backend/
│   ├── main.py              # FastAPI application
│   └── requirements.txt     # Python dependencies
├── frontend/
│   ├── src/
│   │   ├── components/      # React components
│   │   ├── pages/           # Page components
│   │   ├── utils/           # Utility functions
│   │   ├── App.jsx          # Main App component
│   │   └── main.jsx         # Entry point
│   ├── public/              # Static assets
│   ├── package.json         # Node dependencies
│   ├── tailwind.config.js   # Tailwind configuration
│   └── vite.config.js       # Vite configuration
├── uploads/                 # Uploaded PDF files
├── reports_web/             # Generated reports
└── compliCheckV2.py         # Compliance checking script
```

---

## Installation

### 1. Install Backend Dependencies

```bash
# Activate virtual environment
source .venv/bin/activate

# Install FastAPI and dependencies
pip install -r backend/requirements.txt
```

**Backend Dependencies:**
- `fastapi>=0.104.0`
- `uvicorn[standard]>=0.24.0`
- `python-multipart>=0.0.6`
- `pydantic>=2.4.0`
- `python-dotenv>=1.0.0`

### 2. Install Frontend Dependencies

```bash
cd frontend
npm install
```

**Frontend Dependencies:**
- `react@18.3.1`
- `react-dom@18.3.1`
- `react-router-dom@^6.22.0`
- `axios@^1.6.7`
- `tailwindcss@^3.4.1`
- `postcss@^8.4.35`
- `autoprefixer@^10.4.17`

---

## Running the Application

### Terminal 1: Start Backend (FastAPI)

```bash
# From project root
cd backend
python main.py
```

**Backend will run on:** `http://localhost:8000`

**API Documentation:** `http://localhost:8000/docs` (Swagger UI)

### Terminal 2: Start Frontend (React + Vite)

```bash
# From project root
cd frontend
npm run dev
```

**Frontend will run on:** `http://localhost:5173`

---

## API Endpoints

### Authentication
```
POST /api/auth/login
Body: {"username": "test", "password": "test"}
```

### Pre-Check Management
```
POST /api/precheck/create
POST /api/precheck/{id}/basic-info
POST /api/precheck/{id}/upload
POST /api/precheck/{id}/process
GET  /api/precheck/{id}/status
GET  /api/precheck/{id}
GET  /api/precheck/{id}/download/{file_type}
DELETE /api/precheck/{id}
```

### Health Check
```
GET /health
```

---

## Application Flow

### 1. Login Page (`/login`)
- Mock authentication (any username/password)
- Stores session in localStorage
- Redirects to dashboard

### 2. Dashboard (`/dashboard`)
- Three options:
  - **New pre-check** → Create new compliance check
  - Continue save/Draft pre-check (non-functional for POC)
  - Template pre-check application (non-functional for POC)

### 3. Basic Info (`/precheck/new`)
- **Step 1/3**: Basic info
- Form fields:
  - Project description
  - Address
  - Consent type (dropdown)
- Progress stepper shows: Basic info → Documents Upload → Verification
- "Save Draft" and "Next" buttons

### 4. Documents Upload (`/precheck/{id}/upload`)
- **Step 2/3**: Documents Upload
- File upload buttons for:
  - **Site plan** (required) ⭐
  - **Building plan** (optional)
  - Drainage/plumbing plan (stored, not processed)
  - Record of title (stored, not processed)
  - Agent consent (stored, not processed)
- Progress stepper shows: Basic info ✓ → Documents Upload → Verification
- "Save Draft" and "Next" buttons

### 5. Processing
- Shows loading spinner
- Polls `/api/precheck/{id}/status` every 3 seconds
- Updates when status changes from "processing" to "completed"

### 6. Results (`/precheck/{id}/results`)
- **Step 3/3**: Verification
- Two columns:
  - **Completeness**: Form 2 ✓, Site plan ✓, PIM ✓
  - **Compliance**: Form 2 ✓, Site plan (review/pass/fail), PIM (review/pass/fail)
- Progress stepper shows: Basic info ✓ → Documents Upload ✓ → Verification
- Download buttons for compliance reports

---

## Figma Design Implementation

### Color Scheme
```css
--colab-navy: #003d5c    /* Primary buttons, header */
--colab-teal: #2b8a8e    /* Secondary buttons */
--colab-orange: #ff6b35  /* Accents */
--colab-blue: #2563eb    /* Links, progress stepper */
```

### Components to Build

#### 1. Login Form
- Centered card with logo
- Username and password fields
- "Log in" button
- "Forgot password?" link
- "Create account" link

#### 2. Dashboard
- Header with Colab logo and user icon
- Centered card with three button options

#### 3. Progress Stepper
- Three steps: Basic info, Documents Upload, Verification
- States: completed (✓), active (number), pending (gray)
- Blue line between steps

#### 4. Form Card
- White card with shadow
- Form fields with labels
- Dropdown for consent type
- Gray "Save Draft" + Blue "Next" buttons at bottom

#### 5. File Upload Buttons
- Teal "Choose file" buttons
- Show filename after upload
- Upload icon (cloud with arrow)

#### 6. Results Checklist
- Two columns: Completeness and Compliance
- Checkmarks for completed items
- Status indicators (✓, ⚠️, ✗)
- "Remove/Upload" buttons for documents

---

## Frontend Component Structure

```
src/
├── components/
│   ├── Layout/
│   │   ├── Header.jsx           # Colab logo + user menu
│   │   └── Footer.jsx           # (optional)
│   ├── Stepper/
│   │   └── ProgressStepper.jsx  # 3-step progress indicator
│   ├── Forms/
│   │   ├── LoginForm.jsx
│   │   ├── BasicInfoForm.jsx
│   │   └── FileUpload.jsx
│   └── Results/
│       ├── CompletionessColumn.jsx
│       └── ComplianceColumn.jsx
├── pages/
│   ├── Login.jsx
│   ├── Dashboard.jsx
│   ├── BasicInfo.jsx
│   ├── Upload.jsx
│   └── Results.jsx
├── utils/
│   ├── api.js                   # Axios instance + API calls
│   └── auth.js                  # Auth helpers
├── App.jsx                      # Router setup
└── main.jsx                     # Entry point
```

---

## Backend Processing Flow

### When User Clicks "Next" on Upload Page:

1. **Upload Files** (`POST /api/precheck/{id}/upload`)
   - Save files to `uploads/{precheck_id}/`
   - Return success response

2. **Process Files** (`POST /api/precheck/{id}/process`)
   - Run CompliCheck pipeline in background:
     ```python
     subprocess.run([
         "python3", "compliCheckV2.py",
         "uploads/{id}/site_plan.pdf",
         "--output-dir", "reports_web/{id}",
         "--enable-enrichment"
     ])
     ```
   - Update status to "processing"
   - Return immediately (async)

3. **Poll Status** (`GET /api/precheck/{id}/status`)
   - Frontend polls every 3 seconds
   - Returns current status: "processing" or "completed"

4. **Get Results** (`GET /api/precheck/{id}`)
   - Parse generated compliance JSON
   - Return structured data:
     ```json
     {
       "site_plan": {
         "status": "completed",
         "quality_score": 0.75,
         "summary": {
           "total_evaluations": 11,
           "passed": 0,
           "review": 6,
           "failed": 0
         }
       }
     }
     ```

5. **Download Report** (`GET /api/precheck/{id}/download/site_plan`)
   - Return PDF file as attachment

---

## Data Flow Example

### Complete User Journey:

```
1. User opens http://localhost:5173
   ↓
2. Login page → Enter "test" / "test"
   ↓
3. Dashboard → Click "New pre-check"
   ↓
4. POST /api/precheck/create
   Returns: {"precheck_id": "abc-123"}
   ↓
5. Basic Info form → Fill out:
   - Project: "House Renovation"
   - Address: "10 North Point, Lot 2"
   - Consent: "Building consent only"
   → Click "Next"
   ↓
6. POST /api/precheck/abc-123/basic-info
   ↓
7. Upload page → Upload site_plan.pdf
   → Click "Next"
   ↓
8. POST /api/precheck/abc-123/upload
   FormData: {site_plan: File}
   ↓
9. POST /api/precheck/abc-123/process
   Backend runs: compliCheckV2.py in background
   ↓
10. Frontend polls GET /api/precheck/abc-123/status every 3s
    Status: "processing" → "completed" (90-120s)
    ↓
11. Results page shows:
    - Completeness: Form 2 ✓, Site plan ✓
    - Compliance: Site plan ⚠️ (6 items need review)
    - Quality score: 0.75/1.0
    ↓
12. User clicks "Download Report"
    GET /api/precheck/abc-123/download/site_plan
    → Downloads: site_plan_compliance_report.pdf
```

---

## Testing the Application

### Quick Test (No Frontend)

```bash
# Start backend
cd backend
python main.py

# In another terminal, test API
curl -X POST http://localhost:8000/api/precheck/create
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"test","password":"test"}'
```

### Full Test (With Frontend)

1. Start backend: `cd backend && python main.py`
2. Start frontend: `cd frontend && npm run dev`
3. Open `http://localhost:5173`
4. Login with any credentials
5. Create new pre-check
6. Fill basic info
7. Upload `data/10-North-Point_REV-A_Lot-2.pdf` as site plan
8. Click Next → Wait for processing
9. View results and download report

---

## Environment Variables

Create `.env` file in project root:

```bash
# LLM API Keys (for enrichment)
OPENAI_API_KEY=sk-...
# OR
ANTHROPIC_API_KEY=sk-ant-...

# Neo4j (for compliance checking)
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password

# Pinecone (for vector search)
PINECONE_API_KEY=your_key
PINECONE_ENVIRONMENT=us-west1-gcp
PINECONE_INDEX_NAME=building-codes
```

---

## Troubleshooting

### Backend Issues

**Error: "ModuleNotFoundError: No module named 'fastapi'"**
```bash
pip install -r backend/requirements.txt
```

**Error: "Port 8000 already in use"**
```bash
# Kill existing process
lsof -ti:8000 | xargs kill -9

# Or change port in backend/main.py
uvicorn.run("main:app", host="0.0.0.0", port=8001)
```

**Error: "CompliCheck script not found"**
```bash
# Check path in backend/main.py
COMPLICHECK_SCRIPT = BASE_DIR / 'compliCheckV2.py'
```

### Frontend Issues

**Error: "npm: command not found"**
```bash
# Install Node.js
brew install node
```

**Error: "Tailwind classes not working"**
```bash
# Restart dev server
npm run dev
```

**Error: "CORS policy blocked"**
- Check backend CORS settings in `main.py`
- Ensure frontend URL is in `allow_origins`

### CompliCheck Pipeline Issues

**Error: "OPENAI_API_KEY not found"**
- Add to `.env` file in project root
- Restart backend

**Error: "Neo4j connection failed"**
- Start Neo4j: `neo4j start`
- Check credentials in `.env`

---

## Production Deployment

### Backend (FastAPI)

```bash
# Install production ASGI server
pip install gunicorn

# Run with Gunicorn
gunicorn backend.main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000
```

### Frontend (React)

```bash
# Build for production
cd frontend
npm run build

# Serve with static server
npm install -g serve
serve -s dist -p 3000
```

### Docker (Optional)

```dockerfile
# Dockerfile for backend
FROM python:3.9-slim
WORKDIR /app
COPY backend/requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## Next Steps (After POC)

1. **Real Authentication**
   - JWT tokens
   - User registration
   - Password reset

2. **Database Integration**
   - PostgreSQL for pre-checks
   - Store user data, files, results

3. **File Storage**
   - AWS S3 or Google Cloud Storage
   - CDN for reports

4. **WebSocket for Real-time Updates**
   - Live progress updates during processing
   - No polling needed

5. **Email Notifications**
   - Send report when ready
   - Error notifications

6. **Admin Dashboard**
   - View all pre-checks
   - User management
   - System monitoring

---

## Development Tips

### Hot Reload

Both backend and frontend support hot reload:
- **Backend**: Change `main.py` → Auto-reloads
- **Frontend**: Change `.jsx` files → Auto-reloads browser

### API Documentation

FastAPI provides automatic API docs:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

### Debugging

**Backend:**
```python
import pdb; pdb.set_trace()  # Breakpoint
```

**Frontend:**
```javascript
console.log('Debug:', variable);
debugger;  // Breakpoint in browser DevTools
```

---

## Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [React Documentation](https://react.dev/)
- [Tailwind CSS Documentation](https://tailwindcss.com/docs)
- [Vite Documentation](https://vitejs.dev/guide/)
- [Axios Documentation](https://axios-http.com/docs/intro)

---

**Setup Complete!** 🎉

You now have a modern FastAPI + React 18 + Tailwind CSS frontend for CompliCheck.

**Next:** Start building React components based on Figma designs!
