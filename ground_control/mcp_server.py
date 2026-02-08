from mcp.server.fastmcp import FastMCP
from typing import List, Dict
import json

# Initialize FastMCP
mcp = FastMCP("ground-control")

# This would strictly be populated by the running Ground Control process
# For now we use global state or a file-based context
CONTEXT: Dict = {
    "schema": [],
    "api_defs": []
}

@mcp.resource("ground-control://schema")
def get_schema() -> str:
    """Returns the list of tables found in the database (Lazy Loading)."""
    # In a real implementation, this would query metadata for table names only.
    schema_context = CONTEXT.get("schema", [])
    if isinstance(schema_context, list):
        # Assuming schema_context is a list of tables or dicts
        # If it's a list of mock strings or dicts, we just list names
        return "Available Tables:\n" + "\n".join([t.get("name", "unknown") if isinstance(t, dict) else str(t) for t in schema_context])
    return str(schema_context)

@mcp.tool()
def get_table_schema(table_name: str) -> str:
    """
    Get detailed schema definition for a specific table.
    Use this to inspect columns and types when needed.
    """
    # In a real implementation, this would look up the specific table schema
    # from the CONTEXT or query the DB directly.
    all_schemas = CONTEXT.get("schema", [])
    
    # Mock lookup logic
    for table in all_schemas:
        if isinstance(table, dict) and table.get("name") == table_name:
             return f"Schema for {table_name}:\n{json.dumps(table, indent=2)}"
    
    return f"Schema for {table_name}: (Mock data - Table not found or schema not loaded)"

if __name__ == "__main__":
    mcp.run()
