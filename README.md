# 🛸 Antigravity Extension (Ground Control)

> "Reversing the polarity of the cloud. Instead of pushing code to the cloud, we pull the cloud's context to the code."

**Ground Control** is a CLI tool designed to eliminate the "setup tax" of local development. It teleports your production environment's context—infrastructure, secrets, and data connections—directly to your local machine, creating an instant, high-fidelity development environment.

---

## 🛠️ Prerequisites

Before entering the wormhole, ensure you have the following installed:

1.  **Google Cloud CLI (`gcloud`)**: Authenticated with `gcloud auth login` and `gcloud auth application-default login`.
2.  **Cloud SQL Auth Proxy**: Required if your services connect to Cloud SQL.
    -   Install: `gcloud components install cloud-sql-proxy` (or download the binary).
    -   Ensure it's in your system `PATH`.
3.  **Docker**: Required if you want to run containerized services locally (though Ground Control primarily manages the *context* for your local process).

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
-   **Traceability**: Analyzes a running Cloud Run service to find the exact Docker image and Git Commit SHA.
    -   *Fallback strategy*: If the commit SHA is missing from the image, it safely falls back to `HEAD` with a warning.
-   **Runtime Synthesis**: Detects your tech stack (Python, Node.js, Go) and automatically generates the correct run commands.

### 2. The Connectivity Layer ("The Wormhole")
-   **Automatic Proxy Injection**: Detects attached resources (like Cloud SQL) and automatically starts secure proxies.
    -   *Smart Port Management*: Automatically resolves port collisions if default ports (e.g., 5432) are in use.
-   **Memory-First Secret Injection**: Fetches secrets from Google Secret Manager directly into the process memory of a spawned shell. **No `.env` files are written to disk by default**.

### 3. MCP (Model Context Protocol) Integration
Ground Control includes a built-in **MCP Server** (`mcp_server.py`) that acts as a bridge for your AI assistant.
-   **Lazy Loading**: Exposes table names first to save context window tokens, allowing the AI to query specific table schemas on demand (`get_table_schema`).

---

## 🚀 Installation & Integration

### 1. Install Libraries
```bash
cd ~/Desktop/antigravity-extension
pip install .
```

### 2. Configure MCP Context
Add this to your MCP configuration file (e.g., `claude_desktop_config.json`):

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

### 3. Add Workflow (Optional)
```bash
cp ground_control_workflow.md ~/.agent/workflows/ground_control.md
```

---

## 🎮 Usage

### Teleport Cloud Context
Run the `pull` command to hydrate your local environment:

```bash
ag pull my-gcp-project
```

**Options:**
-   `--service, -s`: Target a specific Cloud Run service.
-   `--write-env`: **Legacy Mode**. Writes secrets to a `.env` file instead of spawning a secure shell. Useful for tools that strictly require files.

**What happens:**
1.  **Auth & Scan**: Verifies credentials and scans for services.
2.  **Analysis**: Identifies the commit SHA and runtime environment.
3.  **Wormhole Initialization**: Starts background proxies for databases (handling port collisions).
4.  **Launch**: Spawns a new shell instance with all secrets and connections injected.

---

## ❓ Troubleshooting / The Escape Hatch

### Port Collisions
If port 5432 (Postgres) is already in use by a local instance, Ground Control will automatically find the next available port (e.g., 5433) and map the connection there. The injected environment variables (`DB_PORT`, etc.) will reflect this change.

### Metadata Drift
If the deployed image CLI cannot find a commit SHA (often due to "latest" tags in dev), it will warn you and fall back to the `HEAD` of the repository. Be aware that your local code might be slightly ahead of what is running in the cloud.

---

## 🛡️ Security Note
Ground Control uses a **"Memory-First"** security model. Secrets are fetched at runtime and injected into the environment of the child process (your shell). They are never written to disk unless you explicitly use the `--write-env` flag. This significantly reduces the risk of accidental secret leaks in version control.
