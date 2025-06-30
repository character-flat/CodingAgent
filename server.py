from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pathlib import Path
import uvicorn
import shutil
import time
import uuid
import subprocess
from agent import CodingAgent

# Initialize FastAPI app
app = FastAPI(title="Coding Agent API")

# Add CORS middleware for client access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Set up directories - FIXED PATH FOR CODESPACES
JOBS_DIR = Path("/workspaces/CodingAgent/jobs")
JOBS_DIR.mkdir(exist_ok=True, parents=True)

# Store jobs in memory
jobs = {}

class TaskRequest(BaseModel):
    task: str

@app.get("/")
async def root():
    return {"message": "Coding Agent API is running!"}

@app.post("/schedule")
async def schedule_task(task_request: TaskRequest, background_tasks: BackgroundTasks):
    # Generate job ID
    job_id = str(uuid.uuid4())
    
    # Create job directory
    job_dir = JOBS_DIR / job_id
    job_dir.mkdir(exist_ok=True)
    
    # Store task info
    with open(job_dir / "task.txt", "w") as f:
        f.write(task_request.task)
    
    # Initialize job status
    jobs[job_id] = {
        "id": job_id,
        "task": task_request.task,
        "status": "scheduled",
        "created_at": time.time()
    }
    
    # Execute task in background
    background_tasks.add_task(process_task, job_id, task_request.task)
    
    return {"job_id": job_id, "status": "scheduled"}

@app.get("/status/{job_id}")
async def get_job_status(job_id: str):
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = jobs[job_id]
    
    response = {
        "job_id": job_id,
        "status": job["status"]
    }
    
    if job["status"] == "completed":
        response["download_url"] = f"/download/{job_id}"
    
    if "error" in job:
        response["error"] = job["error"]
    
    return JSONResponse(content=response)

@app.get("/download/{job_id}")
async def download_results(job_id: str):
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = jobs[job_id]
    if job["status"] != "completed":
        raise HTTPException(status_code=400, detail="Job not yet completed")
    
    output_dir = JOBS_DIR / job_id / "output"
    if not output_dir.exists():
        raise HTTPException(status_code=404, detail="Output not found")
    
    # Create zip archive
    zip_path = JOBS_DIR / job_id / "results.zip"
    if not zip_path.exists():
        shutil.make_archive(
            str(zip_path).replace('.zip', ''),
            'zip',
            str(output_dir)
        )
    
    return FileResponse(
        path=zip_path,
        filename=f"task_{job_id}_results.zip",
        media_type="application/zip"
    )

@app.get("/jobs")
async def list_jobs():
    return {"jobs": list(jobs.values())}

async def process_task(job_id: str, task: str):
    """Process a task using the CodingAgent"""
    try:
        # Update job status
        jobs[job_id]["status"] = "running"
        
        # Initialize agent and execute task
        agent = CodingAgent()
        result = agent.execute_task(task)
        
        # Handle success
        if result.get("status") == "completed":
            # Copy output to job directory
            output_src = Path(result["output_dir"])
            output_dst = JOBS_DIR / job_id / "output"
            output_dst.mkdir(exist_ok=True)
            
            # Copy contents
            for item in output_src.glob("**/*"):
                if item.is_file():
                    rel_path = item.relative_to(output_src)
                    dst_path = output_dst / rel_path
                    dst_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(item, dst_path)
            
            # Update job status
            jobs[job_id]["status"] = "completed"
            jobs[job_id]["completed_at"] = time.time()
        else:
            # Handle failure
            jobs[job_id]["status"] = "failed"
            jobs[job_id]["error"] = result.get("error", "Unknown error")
    
    except Exception as e:
        # Update job status with error
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["error"] = str(e)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)