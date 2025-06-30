# CodingAgent - A Basic Sandbox & Orchestration Layer

## Overview

This project implements a simple coding agent capable of handling Python tasks with shell file operations, basic context management, and VNC/noVNC-based GUI access. It also includes an orchestration layer to schedule jobs and retrieve their statuses.

## Key Components

1. **Agent**  
   - Located in [agent.py](./agent.py).  
   - Provides Shell, Filesystem, Code Execution, and xdot capabilities.  
   - Handles context management (including storing/retrieving context files in the /agent/context folder).

2. **Orchestration Layer**  
   - Provided by a FastAPI server ([server.py](./server.py)).  
   - Endpoints:  
     - `POST /schedule` → Accepts a task description, enqueues it, and returns a job ID.  
     - `GET /status/{job_id}` → Retrieves the status of a submitted job and, when complete, provides a download link to the output.

3. **Container Setup**  
   - Dockerfile sets up Xvfb, VNC, noVNC, Node.js, and Python environment.  
   - Scripts to start services, server, and Jupyter notebooks:  
     - [start-services.sh](./start-services.sh) – Launches Xvfb, VNC/noVNC, and desktop.  
     - [start-server.sh](./start-server.sh) – Launches FastAPI server.  
     - [start-jupyter.sh](./start-jupyter.sh) – Launches Jupyter.  

## Getting Started

1. **Build the Docker Image**  
   ```bash
   docker build -t coding-agent .
   ```

2. **Run the Container**  
   ```bash
   docker run -p 5901:5901 -p 6080:6080 -p 8000:8000 -p 8888:8888 --name agent-container coding-agent
   ```
   - Ports exposed (adjust as needed):  
     - 5901 → VNC  
     - 6080 → noVNC HTTP endpoint  
     - 8000 → FastAPI server (orchestration)  
     - 8888 → Jupyter environment  

3. **Access the noVNC Interface**  
   - Visit http://localhost:6080/vnc.html in your browser to see a remote desktop session.

4. **Using the Orchestration Endpoints**  
   - Schedule a job:  
     ```bash
     curl -X POST -H "Content-Type: application/json" \
        -d '{"task": "Build me a todo app in React"}' \
        http://localhost:8000/schedule
     ```
     This returns a JSON object with a "job_id".  
   - Check status:  
     ```bash
     curl http://localhost:8000/status/<job_id>
     ```
     When the job completes, the response includes a "download_url" to retrieve the generated files.

5. **Running Jupyter**  
   - If desired, visit http://localhost:8888 to open the Jupyter environment (no token by default).  
   - The agent’s code, including [agent.py](./agent.py), can be explored or tested in notebooks.

## Project Structure

- `agent.py` – Main code for the CodingAgent (tools, context, etc.)  
- `server.py` – Orchestration server (FastAPI) with `/schedule` and `/status/:id`  
- `requirements.txt` – Python dependencies  
- `start-*.sh` – Various scripts for starting noVNC, Jupyter, and FastAPI  
- `Dockerfile` – Defines container build steps  

## Notes and Considerations

- The project is meant to be a basic demonstration. For production environments, you’d further harden the Docker isolation, e.g., using Firecracker VMs or other sandboxing approaches as mentioned in the assignment.  
- Context management is file-based, stored in `/agent/context`. The agent can load older entries and prune them as necessary.  
- Horizontal scaling (Kubernetes, Nomad, etc.) can be extended by running multiple instances of this container and routing job scheduling accordingly.
