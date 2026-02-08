import os
from rich.console import Console
from typing import Dict, Optional, Any

console = Console()

class RuntimeSynthesizer:
    def detect(self, path: str) -> Dict[str, Any]:
        """
        Detects the runtime stack of the project at the given path.
        """
        info: Dict[str, Any] = {
            "language": "unknown",
            "dependency_file": None,
            "cmd": None
        }
        
        # Check for Python
        if os.path.exists(os.path.join(path, "requirements.txt")):
            info["language"] = "python"
            info["dependency_file"] = "requirements.txt"
            info["cmd"] = "pip install -r requirements.txt"
        elif os.path.exists(os.path.join(path, "pyproject.toml")):
             info["language"] = "python"
             info["dependency_file"] = "pyproject.toml"
             info["cmd"] = "poetry install" # assumption
        
        # Check for Node
        elif os.path.exists(os.path.join(path, "package.json")):
            info["language"] = "node"
            info["dependency_file"] = "package.json"
            info["cmd"] = "npm install"

        # Check for Go
        elif os.path.exists(os.path.join(path, "go.mod")):
            info["language"] = "go"
            info["dependency_file"] = "go.mod"
            info["cmd"] = "go mod download"
            
        return info

    def generate_docker_compose(self, info: Dict[str, str], services: Optional[Dict] = None) -> str:
        """
        Generates a docker-compose.yml content based on detection.
        """
        # Simple template for v1
        return f"""version: '3.8'
services:
  app:
    build: .
    ports:
      - "8080:8080"
    environment:
      - PORT=8080
"""
