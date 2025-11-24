#!/usr/bin/env python3
"""
CompliCheck POC Backend - FastAPI Application
Modern async API for building plan compliance checking
"""

import os
import json
import uuid
import shutil
import asyncio
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List
from contextlib import asynccontextmanager

from fastapi import FastAPI, File, UploadFile, HTTPException, Form, BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# ============================================================================
# Configuration
# ============================================================================

BASE_DIR = Path(__file__).parent.parent.resolve()
UPLOAD_FOLDER = BASE_DIR / 'uploads'
REPORTS_FOLDER = BASE_DIR / 'reports_web'
COMPLICHECK_SCRIPT = BASE_DIR / 'compliCheckV2.py'
PYTHON_CMD = str(BASE_DIR / '.venv' / 'bin' / 'python3')

UPLOAD_FOLDER.mkdir(exist_ok=True)
REPORTS_FOLDER.mkdir(exist_ok=True)

# In-memory storage (POC - no database)
prechecks: Dict[str, dict] = {}

# ============================================================================
# Pydantic Models
# ============================================================================

class LoginRequest(BaseModel):
    username: str
    password: str

class BasicInfoRequest(BaseModel):
    project_description: str
    address: str
    consent_type: str

class PreCheckResponse(BaseModel):
    success: bool
    precheck_id: Optional[str] = None
    message: Optional[str] = None

class StatusResponse(BaseModel):
    success: bool
    status: str
    results: Optional[dict] = None
    processing_step: Optional[str] = None
    progress: Optional[int] = None

# ============================================================================
# Lifespan Context Manager
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    print("=" * 70)
    print("CompliCheck POC Backend - FastAPI")
    print("=" * 70)
    print(f"Base Directory: {BASE_DIR}")
    print(f"Upload Folder: {UPLOAD_FOLDER}")
    print(f"Reports Folder: {REPORTS_FOLDER}")
    print(f"CompliCheck Script: {COMPLICHECK_SCRIPT}")
    print("=" * 70)
    yield
    print("\nShutting down CompliCheck backend...")

# ============================================================================
# FastAPI App
# ============================================================================

app = FastAPI(
    title="CompliCheck API",
    description="Building Plan Compliance Checking API",
    version="2.0.0",
    lifespan=lifespan
)

# CORS configuration for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],  # Vite default ports
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# Helper Functions
# ============================================================================

def get_precheck(precheck_id: str) -> Optional[dict]:
    """Get precheck from memory"""
    return prechecks.get(precheck_id)

async def run_complicheck(
    pdf_path: str,
    output_dir: str,
    precheck_id: str,
    file_type: str
) -> dict:
    """Run CompliCheck pipeline asynchronously"""
    try:
        cmd = [
            PYTHON_CMD if Path(PYTHON_CMD).exists() else 'python3',
            str(COMPLICHECK_SCRIPT),
            pdf_path,
            '--output-dir', output_dir,
            '--enable-enrichment',
            '--keep-intermediates'
        ]

        # Bedrock KB mode is controlled by USE_BEDROCK_KB environment variable

        # Run subprocess
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        try:
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=300.0  # 5 minutes
            )
        except asyncio.TimeoutError:
            process.kill()
            return {
                'status': 'timeout',
                'error': 'Processing took too long (>5 minutes)'
            }

        if process.returncode == 0:
            # Find generated files - check multiple patterns
            output_path = Path(output_dir)

            # Look for report PDFs
            pdf_files = list(output_path.glob('*CompliCheck_Report.pdf')) or \
                       list(output_path.glob('*_report.pdf'))

            # Look for compliance JSON files
            compliance_files = list(output_path.glob('*compliance.json'))

            # Look for enriched JSON files
            enriched_files = list(output_path.glob('*enriched.json'))

            # Look for component files (fallback if compliance not run)
            component_files = list(output_path.glob('*components.json'))

            result = {
                'status': 'completed',
                'pdf_report': str(pdf_files[0]) if pdf_files else None,
                'compliance_json': str(compliance_files[0]) if compliance_files else None,
                'enriched_json': str(enriched_files[0]) if enriched_files else None,
                'components_json': str(component_files[0]) if component_files else None
            }

            # Parse compliance results
            if compliance_files:
                with open(compliance_files[0]) as f:
                    compliance_data = json.load(f)
                    result['summary'] = compliance_data.get('summary', {})

                    # Parse enrichment data for quality score
                    if enriched_files:
                        with open(enriched_files[0]) as ef:
                            enriched_data = json.load(ef)
                            llm_enrichment = enriched_data.get('llm_enrichment', {})
                            reconciliation = llm_enrichment.get('reconciliation', {})
                            result['quality_score'] = reconciliation.get('quality_score', None)
                            result['confidence_level'] = reconciliation.get('confidence_level', None)

            # If no compliance files, still return review status since we have extracted data
            if not compliance_files and (enriched_files or component_files):
                result['status'] = 'review'  # Needs manual review

            return result
        else:
            return {
                'status': 'failed',
                'error': stderr.decode('utf-8') if stderr else 'Unknown error'
            }

    except Exception as e:
        return {
            'status': 'error',
            'error': str(e)
        }

# ============================================================================
# API Endpoints
# ============================================================================

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "app": "CompliCheck API",
        "version": "2.0.0",
        "status": "running"
    }

@app.post("/api/auth/login")
async def login(request: LoginRequest):
    """Mock authentication endpoint"""
    # Accept any non-empty username/password for POC
    if request.username and request.password:
        return {
            "success": True,
            "message": "Login successful",
            "user": request.username,
            "token": "mock-jwt-token"
        }

    raise HTTPException(status_code=401, detail="Invalid credentials")

@app.post("/api/precheck/create", response_model=PreCheckResponse)
async def create_precheck():
    """Create a new pre-check session"""
    precheck_id = str(uuid.uuid4())

    prechecks[precheck_id] = {
        'id': precheck_id,
        'created_at': datetime.now().isoformat(),
        'status': 'created',
        'basic_info': {},
        'files': {},
        'results': {}
    }

    return PreCheckResponse(
        success=True,
        precheck_id=precheck_id,
        message="Pre-check created successfully"
    )

@app.post("/api/precheck/{precheck_id}/basic-info")
async def save_basic_info(precheck_id: str, request: BasicInfoRequest):
    """Save basic information"""
    precheck = get_precheck(precheck_id)
    if not precheck:
        raise HTTPException(status_code=404, detail="Pre-check not found")

    precheck['basic_info'] = {
        'project_description': request.project_description,
        'address': request.address,
        'consent_type': request.consent_type
    }

    return {"success": True, "message": "Basic info saved"}

@app.post("/api/precheck/{precheck_id}/upload")
async def upload_files(
    precheck_id: str,
    site_plan: Optional[UploadFile] = File(None),
    building_plan: Optional[UploadFile] = File(None),
    drainage_plan: Optional[UploadFile] = File(None),
    record_of_title: Optional[UploadFile] = File(None),
    agent_consent: Optional[UploadFile] = File(None)
):
    """Upload documents"""
    precheck = get_precheck(precheck_id)
    if not precheck:
        raise HTTPException(status_code=404, detail="Pre-check not found")

    # Create upload directory
    upload_dir = UPLOAD_FOLDER / precheck_id
    upload_dir.mkdir(exist_ok=True)

    uploaded_files = {}

    # Process each file
    files_map = {
        'site_plan': site_plan,
        'building_plan': building_plan,
        'drainage_plan': drainage_plan,
        'record_of_title': record_of_title,
        'agent_consent': agent_consent
    }

    for file_key, file in files_map.items():
        if file and file.filename:
            # Check file extension
            if not file.filename.lower().endswith('.pdf'):
                raise HTTPException(
                    status_code=400,
                    detail=f"{file_key}: Only PDF files are allowed"
                )

            # Save file
            file_path = upload_dir / f"{file_key}_{file.filename}"
            with open(file_path, "wb") as buffer:
                content = await file.read()
                buffer.write(content)

            uploaded_files[file_key] = str(file_path)

    # Update precheck
    precheck['files'] = uploaded_files
    precheck['status'] = 'files_uploaded'

    return {
        "success": True,
        "uploaded_files": list(uploaded_files.keys()),
        "message": f"Uploaded {len(uploaded_files)} file(s)"
    }

@app.post("/api/precheck/{precheck_id}/process")
async def process_precheck(precheck_id: str, background_tasks: BackgroundTasks):
    """Start compliance checking (async background task)"""
    precheck = get_precheck(precheck_id)
    if not precheck:
        raise HTTPException(status_code=404, detail="Pre-check not found")

    files = precheck.get('files', {})
    if not files.get('site_plan'):
        raise HTTPException(
            status_code=400,
            detail="Site plan is required"
        )

    # Update status
    precheck['status'] = 'processing'
    precheck['processing_step'] = 'Preparing documents for analysis...'
    precheck['progress'] = 10

    # Create output directory
    output_dir = REPORTS_FOLDER / precheck_id
    output_dir.mkdir(exist_ok=True)

    # Process in background
    async def process_files():
        results = {}

        try:
            # Process site plan
            precheck['processing_step'] = 'Extracting components from site plan...'
            precheck['progress'] = 25

            site_plan_result = await run_complicheck(
                files['site_plan'],
                str(output_dir),
                precheck_id,
                'site_plan'
            )
            results['site_plan'] = site_plan_result

            precheck['processing_step'] = 'Site plan analysis completed'
            precheck['progress'] = 50

            # Process building plan if uploaded
            if files.get('building_plan'):
                precheck['processing_step'] = 'Extracting components from building plan...'
                precheck['progress'] = 60

                building_plan_result = await run_complicheck(
                    files['building_plan'],
                    str(output_dir),
                    precheck_id,
                    'building_plan'
                )
                results['building_plan'] = building_plan_result

                precheck['processing_step'] = 'Building plan analysis completed'
                precheck['progress'] = 90

            # Update precheck with results
            precheck['results'] = results
            precheck['status'] = 'completed'
            precheck['processing_step'] = 'Complete'
            precheck['progress'] = 100

        except Exception as e:
            precheck['status'] = 'failed'
            precheck['processing_step'] = f'Error: {str(e)}'
            precheck['progress'] = 0

    # Add to background tasks
    background_tasks.add_task(process_files)

    return {
        "success": True,
        "message": "Processing started",
        "status": "processing"
    }

@app.get("/api/precheck/{precheck_id}/status", response_model=StatusResponse)
async def get_status(precheck_id: str):
    """Get pre-check status (for polling)"""
    precheck = get_precheck(precheck_id)
    if not precheck:
        raise HTTPException(status_code=404, detail="Pre-check not found")

    return StatusResponse(
        success=True,
        status=precheck['status'],
        results=precheck.get('results', {}),
        processing_step=precheck.get('processing_step'),
        progress=precheck.get('progress', 0)
    )

@app.get("/api/precheck/{precheck_id}")
async def get_precheck_data(precheck_id: str):
    """Get complete precheck data"""
    precheck = get_precheck(precheck_id)
    if not precheck:
        raise HTTPException(status_code=404, detail="Pre-check not found")

    return {
        "success": True,
        "precheck": precheck
    }

@app.get("/api/precheck/{precheck_id}/report/{file_type}")
async def get_report_json(precheck_id: str, file_type: str):
    """Get JSON report data for display"""
    if file_type not in ['site_plan', 'building_plan']:
        raise HTTPException(status_code=400, detail="Invalid file type")

    precheck = get_precheck(precheck_id)

    # If precheck exists in memory, use its registered file paths
    if precheck:
        results = precheck.get('results', {})
        result = results.get(file_type, {})

        # Get JSON file paths from precheck results
        compliance_json_path = result.get('compliance_json')
        enriched_json_path = result.get('enriched_json')
        components_json_path = result.get('components_json')
        pdf_report_path = result.get('pdf_report')
        report_status = result.get('status', 'unknown')
    else:
        # Fallback to file-based detection for older reports
        report_dir = REPORTS_FOLDER / precheck_id
        if not report_dir.exists():
            raise HTTPException(status_code=404, detail="Pre-check not found")

        # Find files by pattern
        file_prefix = f"{file_type}_*"
        compliance_files = list(report_dir.glob(f"{file_prefix}_compliance.json"))
        enriched_files = list(report_dir.glob(f"{file_prefix}enriched.json"))
        components_files = list(report_dir.glob(f"{file_prefix}_components.json"))
        pdf_files = list(report_dir.glob(f"{file_prefix}*.pdf"))

        compliance_json_path = str(compliance_files[0]) if compliance_files else None
        enriched_json_path = str(enriched_files[0]) if enriched_files else None
        components_json_path = str(components_files[0]) if components_files else None
        pdf_report_path = str(pdf_files[0]) if pdf_files else None
        report_status = 'completed' if compliance_json_path else 'review'

    report_data = {}

    # Try to load compliance JSON
    if compliance_json_path and Path(compliance_json_path).exists():
        try:
            with open(compliance_json_path, 'r') as f:
                report_data['compliance'] = json.load(f)
        except Exception as e:
            print(f"Error loading compliance JSON: {e}")

    # Try to load enriched JSON
    if enriched_json_path and Path(enriched_json_path).exists():
        try:
            with open(enriched_json_path, 'r') as f:
                report_data['enriched'] = json.load(f)
        except Exception as e:
            print(f"Error loading enriched JSON: {e}")

    # Try to load components JSON as fallback
    if components_json_path and Path(components_json_path).exists():
        try:
            with open(components_json_path, 'r') as f:
                report_data['components'] = json.load(f)
        except Exception as e:
            print(f"Error loading components JSON: {e}")

    if not report_data:
        raise HTTPException(status_code=404, detail="Report data not found")

    return {
        "success": True,
        "file_type": file_type,
        "report": report_data,
        "has_pdf": pdf_report_path is not None and Path(pdf_report_path).exists(),
        "status": report_status
    }

@app.get("/api/precheck/{precheck_id}/download/{file_type}")
async def download_report(precheck_id: str, file_type: str):
    """Download compliance report PDF"""
    precheck = get_precheck(precheck_id)
    if not precheck:
        raise HTTPException(status_code=404, detail="Pre-check not found")

    results = precheck.get('results', {})

    if file_type not in ['site_plan', 'building_plan']:
        raise HTTPException(status_code=400, detail="Invalid file type")

    result = results.get(file_type, {})
    report_path = result.get('pdf_report')

    if not report_path or not Path(report_path).exists():
        raise HTTPException(status_code=404, detail="Report not found")

    return FileResponse(
        report_path,
        media_type='application/pdf',
        filename=f"{file_type}_compliance_report.pdf"
    )

@app.delete("/api/precheck/{precheck_id}")
async def delete_precheck(precheck_id: str):
    """Delete pre-check and cleanup files"""
    precheck = get_precheck(precheck_id)
    if not precheck:
        raise HTTPException(status_code=404, detail="Pre-check not found")

    # Cleanup files
    upload_dir = UPLOAD_FOLDER / precheck_id
    if upload_dir.exists():
        shutil.rmtree(upload_dir)

    output_dir = REPORTS_FOLDER / precheck_id
    if output_dir.exists():
        shutil.rmtree(output_dir)

    # Remove from memory
    del prechecks[precheck_id]

    return {"success": True, "message": "Pre-check deleted"}

# ============================================================================
# Health Check
# ============================================================================

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "active_prechecks": len(prechecks)
    }

# ============================================================================
# Run with Uvicorn
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
