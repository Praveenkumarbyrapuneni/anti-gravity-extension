# 🛸 Antigravity Extension (Ground Control)

> "Reversing the polarity of the cloud. Instead of pushing code to the cloud, we pull the cloud's context to the code."

**Ground Control** is a CLI tool designed to eliminate the "setup tax" of local development. It teleports your production environment's context—infrastructure, secrets, and data connections—directly to your local machine, creating an instant, high-fidelity development environment.

---

## 🧠 Core Philosophy

Most developers waste days setting up `.env` files, installing dependencies, and configuring database proxies to match production. Ground Control automates this by:
1.  **Reverse-Engineering Infrastructure**: inferring local config from live Cloud Run/Lambda resources.
2.  **Secure Tunneling**: establishing "wormholes" (proxies) to live data without mocking.
3.  **Context Injection**: feeding live schema and API definitions to your AI assistant via MCP.

---

## ✨ Features

### 1. The "Smart Pull" (`ag pull`)
Unlike a simple `git clone`, Ground Control performs a **Stateful Clone**:
-   **Traceability**: Analyzes a running Cloud Run service to find the exact Docker image and Git Commit SHA currently deployed.
-   **Runtime Synthesis**: Detects your tech stack (Python, Node.js, Go) and automatically generates the correct install/run commands.

### 2. The Connectivity Layer ("The Wormhole")
-   **Automatic Proxy Injection**: Detects attached resources (like Cloud SQL) and silently starts secure background proxies (`cloud-sql-proxy`) to map them to localhost.
-   **Secret Injection**: Fetches secrets from Google Secret Manager directly into process memory. **No `.env` files are written to disk**, enhancing security.

### 3. MCP (Model Context Protocol) Integration
Ground Control includes a built-in **MCP Server** (`mcp_server.py`).
-   It exposes the live database schema and API definitions to your AI coding assistant.
-   When you ask the AI to "write a query", it knows your *actual* table names and types.

---

## 🚀 Installation & Integration with Antigravity App

### 1. Install Libraries
First, install the package into your system Python or the environment used by your AI agent:

```bash
cd ~/Desktop/antigravity-extension
pip install .
```

### 2. Configure MCP Context
To give your Antigravity (AI) Assistant access to the live cloud context (schemas, APIs), add this to your MCP configuration file (e.g., `claude_desktop_config.json` or equivalent):

```json
{
  "mcpServers": {
    "ground-control": {
      "command": "python3",
      "args": ["-m", "ground_control.mcp_server"]
    }
  }
}
```
*Once configured, the AI will automatically have access to the `ground_control://schema` resource.*

### 3. Add Workflow (Optional)
To run Ground Control commands directly from the chat interface, copy the workflow file:

```bash
cp ground_control_workflow.md ~/.agent/workflows/ground_control.md
```
Now you can type `/ground-control <project-id>` directly in the chat to spin up a new environment!

---

## 🎮 Usage (Manual CLI)

### 1. Teleport Cloud Context
Run the `pull` command to hydrate your local environment from a cloud project:

```bash
# Syntax: ag pull <project-id>
ag pull my-gcp-project
```

**What happens:**
1.  **Auth Check**: Verifies your `gcloud` credentials.
2.  **Service Scan**: Lists available Cloud Run services and asks you to select one.
3.  **Analysis**: Finds the Docker image and Git Commit SHA.
4.  **Connectivity**: Starts `cloud-sql-proxy` for any attached databases.
5.  **Handover**: Generates the commands to start your app with all secrets injected.

---

## 🏗️ Architecture

-   **`cli.py`**: The main entry point using `Typer`. Handles the user interaction flow.
-   **`providers/gcp.py`**: The "Sensor" layer. Wraps `gcloud` and GCP APIs to reverse-engineer the cloud state (Service -> Image -> Commit).
-   **`detector.py`**: The "Synthesizer". Scans local files (`requirements.txt`, `package.json`) to determine how to run the project.
-   **`connectivity.py`**: The "Wormhole". Manages background processes for proxies and secret retrieval.
-   **`mcp_server.py`**: The AI interface. Implements the Model Context Protocol to share discovered context.

---

## 🛡️ Security Note
Ground Control is designed with a "Memory-First" security model. Secrets are fetched at runtime and injected into the environment of the child process. They are never written to `.env` files or persistent storage, reducing the risk of accidental leaks.
