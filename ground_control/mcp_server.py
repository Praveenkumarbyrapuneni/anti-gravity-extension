from mcp.server.fastmcp import FastMCP
from typing import List, Dict

# Initialize FastMCP
mcp = FastMCP("ground-control")

# This would strictly be populated by the running Ground Control process
# For now we use global state or a file-based context
CONTEXT: Dict = {
    "schema": [],
    "api_defs": []
}

@mcp.resource("ground_control://schema")
def get_schema() -> str:
    """Returns the database schema extracted from the cloud environment."""
    return str(CONTEXT.get("schema", "No schema found."))

@mcp.tool()
def query_schema(table_name: str) -> str:
    """Get details for a specific table."""
    # Mock lookup
    return f"Schema for {table_name}: (Mock data)"

if __name__ == "__main__":
    mcp.run()
