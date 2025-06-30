import os
import json
import time
import uuid
import subprocess
from pathlib import Path
import shutil

class Tool:
    """Base class for all tools"""
    def __init__(self, workspace_dir):
        self.workspace_dir = Path(workspace_dir)
        self.workspace_dir.mkdir(parents=True, exist_ok=True)

class ShellTool(Tool):
    """Safely execute shell commands"""
    def __init__(self, workspace_dir):
        super().__init__(workspace_dir)
        self.allowed_commands = {
            "ls", "cat", "echo", "mkdir", "touch", "rm", "cp", "mv", 
            "npm", "npx", "node", "python", "pip"
        }
    
    def execute(self, command):
        """Execute a shell command safely"""
        cmd_parts = command.split()
        if not cmd_parts:
            return {"error": "Empty command"}
            
        base_cmd = cmd_parts[0]
        
        # Check if command is allowed
        if base_cmd not in self.allowed_commands:
            return {"error": f"Command not allowed: {base_cmd}"}
        
        try:
            result = subprocess.run(
                command,
                shell=True,
                cwd=str(self.workspace_dir),
                capture_output=True,
                text=True,
                timeout=30
            )
            
            return {
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode
            }
        except Exception as e:
            return {"error": str(e)}

class FilesystemTool(Tool):
    """Handle file operations"""
    def create_file(self, filename, content):
        """Create a file with content"""
        try:
            file_path = self.workspace_dir / filename
            file_path.parent.mkdir(parents=True, exist_ok=True)  # Create parent directories if needed
            with open(file_path, 'w') as f:
                f.write(content)
            return {"success": True, "path": str(file_path)}
        except Exception as e:
            return {"error": str(e)}
    
    def read_file(self, filename):
        """Read file content"""
        try:
            file_path = self.workspace_dir / filename
            with open(file_path, 'r') as f:
                content = f.read()
            return {"success": True, "content": content}
        except Exception as e:
            return {"error": str(e)}

class CodeExecutionTool(Tool):
    """Execute code in different languages"""
    def run_python(self, code):
        """Run Python code"""
        try:
            # Create a temporary Python file
            temp_file = self.workspace_dir / f"temp_{uuid.uuid4()}.py"
            with open(temp_file, 'w') as f:
                f.write(code)
            
            # Run the code
            result = subprocess.run(
                ['python3', str(temp_file)],
                cwd=str(self.workspace_dir),
                capture_output=True,
                text=True,
                timeout=30
            )
            
            # Clean up
            temp_file.unlink()
            
            return {
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode
            }
        except Exception as e:
            return {"error": str(e)}
    
    def run_javascript(self, code):
        """Run JavaScript code"""
        try:
            temp_file = self.workspace_dir / f"temp_{uuid.uuid4()}.js"
            with open(temp_file, 'w') as f:
                f.write(code)
            
            result = subprocess.run(
                ['node', str(temp_file)],
                cwd=str(self.workspace_dir),
                capture_output=True,
                text=True,
                timeout=30
            )
            
            temp_file.unlink()
            
            return {
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode
            }
        except Exception as e:
            return {"error": str(e)}

class XdotTool(Tool):
    """Visualization using xdot"""
    def create_graph(self, graph_def, output_file):
        """Create a graph from DOT definition"""
        try:
            # Create a temporary DOT file
            dot_file = self.workspace_dir / f"temp_{uuid.uuid4()}.dot"
            with open(dot_file, 'w') as f:
                f.write(graph_def)
            
            # Generate PNG using dot
            output_path = self.workspace_dir / output_file
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            result = subprocess.run(
                ['dot', '-Tpng', str(dot_file), '-o', str(output_path)],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            # Clean up
            dot_file.unlink()
            
            if result.returncode != 0:
                return {"error": result.stderr}
            
            return {"success": True, "path": str(output_path)}
        except Exception as e:
            return {"error": str(e)}

class ContextManager:
    """Simple context management"""
    def __init__(self, context_dir):
        self.context_dir = Path(context_dir)
        self.context_dir.mkdir(parents=True, exist_ok=True)
        self.current_context = []
        self._load_recent_context()
    
    def add(self, message, source="user"):
        """Add an entry to context"""
        entry = {
            "time": time.time(),
            "source": source,
            "message": message
        }
        
        self.current_context.append(entry)
        
        # Save to disk for persistence
        day_folder = time.strftime("%Y-%m-%d")
        save_dir = self.context_dir / day_folder
        save_dir.mkdir(exist_ok=True)
        
        with open(save_dir / f"{int(entry['time'])}.json", 'w') as f:
            json.dump(entry, f)
    
    def get_recent(self, count=10):
        """Get recent context entries"""
        return self.current_context[-count:]
    
    def _load_recent_context(self):
        """Load recent context from disk"""
        try:
            # Get the most recent day folder
            day_folders = sorted(self.context_dir.glob("*"), reverse=True)
            if not day_folders:
                return
                
            recent_folder = day_folders[0]
            
            # Load files from the recent folder
            context_files = sorted(recent_folder.glob("*.json"))
            for file_path in context_files[-50:]:  # Load last 50 entries
                try:
                    with open(file_path, 'r') as f:
                        entry = json.load(f)
                        self.current_context.append(entry)
                except:
                    pass
        except Exception:
            # If anything goes wrong, just start with empty context
            pass

class CodingAgent:
    """Main agent class that coordinates tools"""
    def __init__(self):
        # FIXED PATHS FOR CODESPACES
        self.workspace_dir = Path("/workspaces/CodingAgent/agent/workspace")
        self.outputs_dir = Path("/workspaces/CodingAgent/agent/outputs")
        self.context_dir = Path("/workspaces/CodingAgent/agent/context")
        
        # Create directories
        self.workspace_dir.mkdir(parents=True, exist_ok=True)
        self.outputs_dir.mkdir(parents=True, exist_ok=True)
        self.context_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize tools
        self.shell = ShellTool(self.workspace_dir)
        self.filesystem = FilesystemTool(self.workspace_dir)
        self.code_execution = CodeExecutionTool(self.workspace_dir)
        self.xdot = XdotTool(self.workspace_dir)
        
        # Initialize context manager
        self.context = ContextManager(self.context_dir)
    
    def execute_task(self, task_description):
        """Execute a coding task"""
        try:
            # Generate task ID
            task_id = str(uuid.uuid4())
            task_dir = self.workspace_dir / task_id
            task_dir.mkdir()
            
            # Add task to context
            self.context.add(f"New task: {task_description}", "system")
            
            # Make task-specific implementations here
            # For this example, let's implement a simple React todo app if that's requested
            if "todo" in task_description.lower() and "react" in task_description.lower():
                return self._implement_react_todo_app(task_id, task_dir, task_description)
            else:
                # Generic implementation for other tasks
                return self._implement_generic_task(task_id, task_dir, task_description)
            
        except Exception as e:
            self.context.add(f"Task failed: {str(e)}", "system")
            return {
                "status": "failed",
                "error": str(e)
            }
    
    def _implement_generic_task(self, task_id, task_dir, task_description):
        """Implement a generic task"""
        # Create README file
        self.filesystem.create_file(f"{task_id}/README.md", f"# Task\n\n{task_description}\n\n## Implementation\n\nThis is a basic implementation based on your requirements.")
        
        # Create sample Python script
        sample_code = f'''
# Generated for task: {task_description}
print("Hello, I am the coding agent!")
print("Working on: {task_description}")

# Simple implementation
def main():
    print("Implementation goes here")
    
if __name__ == "__main__":
    main()
'''
        self.filesystem.create_file(f"{task_id}/main.py", sample_code)
        
        # Run the code
        result = self.code_execution.run_python(sample_code)
        self.filesystem.create_file(f"{task_id}/output.txt", result.get("stdout", "No output"))
        
        # Create a sample visualization
        graph_def = '''
digraph G {
    rankdir=LR;
    Task -> "Analysis" -> "Implementation" -> "Testing" -> "Output";
}
'''
        self.xdot.create_graph(graph_def, f"{task_id}/workflow.png")
        
        # Prepare output
        output_path = self.outputs_dir / task_id
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Copy all files from task directory to output
        for item in task_dir.glob("**/*"):
            if item.is_file():
                relative_path = item.relative_to(task_dir)
                target_path = output_path / relative_path
                target_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(item, target_path)
        
        self.context.add(f"Task completed: {task_description}", "system")
        
        return {
            "task_id": task_id,
            "status": "completed",
            "output_dir": str(output_path)
        }
    
    def _implement_react_todo_app(self, task_id, task_dir, task_description):
        """Implement a React todo app"""
        # Create package.json
        package_json = '''{
  "name": "react-todo-app",
  "version": "1.0.0",
  "description": "Simple React Todo App",
  "main": "index.js",
  "scripts": {
    "start": "react-scripts start",
    "build": "react-scripts build"
  },
  "dependencies": {
    "react": "^17.0.2",
    "react-dom": "^17.0.2",
    "react-scripts": "4.0.3"
  },
  "browserslist": {
    "production": [
      ">0.2%",
      "not dead",
      "not op_mini all"
    ],
    "development": [
      "last 1 chrome version",
      "last 1 firefox version",
      "last 1 safari version"
    ]
  }
}'''
        self.filesystem.create_file(f"{task_id}/package.json", package_json)
        
        # Create public/index.html
        index_html = '''<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>React Todo App</title>
  </head>
  <body>
    <div id="root"></div>
  </body>
</html>'''
        self.filesystem.create_file(f"{task_id}/public/index.html", index_html)
        
        # Create src/index.js
        index_js = '''import React from 'react';
import ReactDOM from 'react-dom';
import App from './App';
import './styles.css';

ReactDOM.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
  document.getElementById('root')
);'''
        self.filesystem.create_file(f"{task_id}/src/index.js", index_js)
        
        # Create src/App.js
        app_js = '''import React, { useState } from 'react';

function App() {
  const [todos, setTodos] = useState([]);
  const [input, setInput] = useState('');

  const addTodo = () => {
    if (input.trim() === '') return;
    setTodos([...todos, { id: Date.now(), text: input, completed: false }]);
    setInput('');
  };

  const toggleTodo = (id) => {
    setTodos(
      todos.map((todo) =>
        todo.id === id ? { ...todo, completed: !todo.completed } : todo
      )
    );
  };

  const deleteTodo = (id) => {
    setTodos(todos.filter((todo) => todo.id !== id));
  };

  return (
    <div className="app">
      <h1>Todo App</h1>
      <div className="add-todo">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Add a todo"
          onKeyPress={(e) => e.key === 'Enter' && addTodo()}
        />
        <button onClick={addTodo}>Add</button>
      </div>
      <ul className="todo-list">
        {todos.map((todo) => (
          <li key={todo.id} className={todo.completed ? 'completed' : ''}>
            <span onClick={() => toggleTodo(todo.id)}>{todo.text}</span>
            <button onClick={() => deleteTodo(todo.id)}>Delete</button>
          </li>
        ))}
      </ul>
      <div className="info">
        <p>{todos.filter((todo) => !todo.completed).length} tasks left</p>
      </div>
    </div>
  );
}

export default App;'''
        self.filesystem.create_file(f"{task_id}/src/App.js", app_js)
        
        # Create src/styles.css
        styles_css = '''body {
  font-family: 'Arial', sans-serif;
  margin: 0;
  padding: 0;
  background-color: #f5f5f5;
}

.app {
  max-width: 500px;
  margin: 2rem auto;
  padding: 1rem;
  background-color: white;
  box-shadow: 0 0 10px rgba(0,0,0,0.1);
  border-radius: 5px;
}

h1 {
  text-align: center;
  color: #333;
}

.add-todo {
  display: flex;
  margin-bottom: 1rem;
}

input {
  flex: 1;
  padding: 0.5rem;
  font-size: 1rem;
  border: 1px solid #ddd;
  border-radius: 4px 0 0 4px;
}

button {
  padding: 0.5rem 1rem;
  background-color: #4caf50;
  color: white;
  border: none;
  cursor: pointer;
  font-size: 1rem;
}

.add-todo button {
  border-radius: 0 4px 4px 0;
}

.todo-list {
  list-style-type: none;
  padding: 0;
}

.todo-list li {
  display: flex;
  justify-content: space-between;
  padding: 0.5rem;
  margin-bottom: 0.5rem;
  background-color: #f9f9f9;
  border-radius: 4px;
}

.todo-list li.completed span {
  text-decoration: line-through;
  color: #888;
}

.todo-list span {
  cursor: pointer;
  flex: 1;
}

.todo-list button {
  background-color: #f44336;
  padding: 0.25rem 0.5rem;
  font-size: 0.8rem;
  border-radius: 4px;
}

.info {
  text-align: center;
  color: #666;
  font-size: 0.9rem;
}'''
        self.filesystem.create_file(f"{task_id}/src/styles.css", styles_css)
        
        # Create README.md
        readme_md = f'''# React Todo App

This is a simple React todo application created in response to the task:
"{task_description}"

## Features

- Add new todos
- Mark todos as complete/incomplete
- Delete todos
- Counter of remaining tasks

## How to Run

1. Navigate to this directory
2. Install dependencies: `npm install`
3. Start development server: `npm start`
4. Open browser at http://localhost:3000

## Project Structure

- `public/index.html` - Main HTML page
- `src/index.js` - Entry point of the React app
- `src/App.js` - Main component with todo functionality
- `src/styles.css` - Styling for the application
'''
        self.filesystem.create_file(f"{task_id}/README.md", readme_md)
        
        # Create architecture visualization
        graph_def = '''
digraph TodoApp {
    rankdir=LR;
    node [shape=box, style=filled, fillcolor=lightblue];
    
    User -> "App Component" -> "Todo List";
    "App Component" -> "Add Todo";
    "Todo List" -> "Todo Item";
    "Todo Item" -> "Toggle Complete";
    "Todo Item" -> "Delete Todo";
}
'''
        self.xdot.create_graph(graph_def, f"{task_id}/architecture.png")
        
        # Prepare output
        output_path = self.outputs_dir / task_id
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Copy all files from task directory to output
        for item in task_dir.glob("**/*"):
            if item.is_file():
                relative_path = item.relative_to(task_dir)
                target_path = output_path / relative_path
                target_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(item, target_path)
        
        self.context.add(f"Task completed: React todo app implementation", "system")
        
        return {
            "task_id": task_id,
            "status": "completed",
            "output_dir": str(output_path)
        }