"""
FastAPI serverless function for Vercel deployment.
"""

from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import JSONResponse
from pipeline import ShortlistingPipeline
import os
import tempfile
import shutil
from typing import Optional

app = FastAPI()

# Initialize pipeline (will connect to MongoDB if configured)
pipeline = ShortlistingPipeline(use_mongodb=True)


@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "Smart Shortlisting Engine API",
        "version": "1.0.0"
    }


@app.post("/shortlist")
async def shortlist_candidates(
    jd: UploadFile = File(..., description="Job Description PDF"),
    resumes: UploadFile = File(..., description="Resumes ZIP file or single PDF"),
    keyword_weight: Optional[float] = Form(0.5, description="Keyword matching weight"),
    semantic_weight: Optional[float] = Form(0.5, description="Semantic matching weight")
):
    """
    Run shortlisting pipeline on uploaded JD and resumes.
    
    Args:
        jd: Job Description PDF file
        resumes: Resumes (ZIP file containing multiple PDFs or single PDF)
        keyword_weight: Weight for keyword matching (default: 0.5)
        semantic_weight: Weight for semantic matching (default: 0.5)
    
    Returns:
        JSON response with rankings and top 3 explanations
    """
    # Create temporary directory for file processing
    temp_dir = tempfile.mkdtemp()
    
    try:
        # Validate file types
        if not jd.filename.lower().endswith('.pdf'):
            raise HTTPException(status_code=400, detail="JD must be a PDF file")
        
        if not resumes.filename.lower().endswith(('.pdf', '.zip')):
            raise HTTPException(status_code=400, detail="Resumes must be PDF or ZIP file")
        
        # Save JD
        jd_path = os.path.join(temp_dir, "jd.pdf")
        with open(jd_path, "wb") as f:
            f.write(await jd.read())
        
        # Save resumes
        if resumes.filename.lower().endswith('.zip'):
            # Handle ZIP file
            import zipfile
            resume_zip_path = os.path.join(temp_dir, "resumes.zip")
            with open(resume_zip_path, "wb") as f:
                f.write(await resumes.read())
            
            # Extract ZIP
            resume_folder = os.path.join(temp_dir, "resumes")
            os.makedirs(resume_folder, exist_ok=True)
            
            with zipfile.ZipFile(resume_zip_path, 'r') as zip_ref:
                zip_ref.extractall(resume_folder)
        else:
            # Handle single PDF
            resume_folder = os.path.join(temp_dir, "resumes")
            os.makedirs(resume_folder, exist_ok=True)
            
            resume_path = os.path.join(resume_folder, resumes.filename)
            with open(resume_path, "wb") as f:
                f.write(await resumes.read())
        
        # Update weights if provided
        if keyword_weight or semantic_weight:
            import config
            config.KEYWORD_WEIGHT = keyword_weight
            config.SEMANTIC_WEIGHT = semantic_weight
        
        # Run pipeline
        output = pipeline.run(jd_path, resume_folder, os.path.join(temp_dir, "output.json"))
        
        return JSONResponse(content=output)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    finally:
        # Clean up temporary directory
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)


@app.get("/health")
async def health_check():
    """Detailed health check."""
    mongodb_status = "connected" if pipeline.db and pipeline.db.client else "disabled"
    
    return {
        "status": "healthy",
        "mongodb": mongodb_status,
        "pipeline": "ready"
    }
