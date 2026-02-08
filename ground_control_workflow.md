---
description: Pull cloud context using Ground Control
---

# Ground Control: Smart Pull

This workflow allows you to pull a cloud project's context (infrastructure, secrets, database connections) directly into your local environment using the Ground Control extension.

**Usage:**
`/ground-control <project-id>`

**Steps:**

1.  **Install/Verify Ground Control**
    Ensure the `ground-control` CLI is available.
    ```bash
    # Only needed once
    # pip install ~/Desktop/antigravity-extension
    ag --version
    ```
    // turbo

2.  **Pull Cloud Context**
    Run the smart pull sequence.
    ```bash
    ag pull ${1:project_id}
    ```

3.  **Start Context Server (Optional)**
    If you want the AI to be aware of the DB schema, ensure the MCP server is running.
    ```bash
    # This usually runs in a background terminal
    # python -m ground_control.mcp_server
    echo "Ensure MCP server is running for schema awareness."
    ```
