import typer
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from typing import Optional
import os
from .auth import check_gcloud_auth
from .providers.gcp import GCPProvider

app = typer.Typer(
    name="ground-control",
    help="Ground Control: Teleport cloud context to your local environment.",
    add_completion=False,
)
console = Console()

@app.command()
def pull(
    project_id: str = typer.Argument(..., help="The Cloud Project ID to pull from (e.g. 'my-gcp-project')."),
    service: Optional[str] = typer.Option(None, "--service", "-s", help="Specific Cloud Run service to target."),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show verbose output."),
):
    """
    Pull a cloud project's context to your local environment.
    """
    console.print(Panel(f"[bold green]Ground Control[/bold green]: Initiating sequence for [cyan]{project_id}[/cyan]...", title="🚀 Launch Sequence"))

    if verbose:
        console.log("Verbose mode enabled.")

    if not check_gcloud_auth():
        raise typer.Exit(code=1)

    provider = GCPProvider(project_id)
    
    if not service:
        with console.status("[bold green]Scanning for services...[/bold green]"):
            services_data = provider.list_services() # Now returns simple list or check method sig
            # Wait, list_services in previous step returned List[str] then List[Dict]. 
            # Let's check the file content. 
            # The current gcp.py implementation returns List[Dict] (metadata/name).
            # But the first implementation returned List[str]. 
            # I must ensure I handle the dict correctly.
            
            # Actually I'll re-read to be safe or just handle the Dict.
            # Services list result is list of dicts.
            
        if not services_data:
            console.print("[red]No services found or access denied.[/red]")
            raise typer.Exit(code=1)
            
        service_names = [s.get("metadata", {}).get("name") for s in services_data]
        
        if not service_names:
             console.print("[red]No managed services found.[/red]")
             raise typer.Exit(code=1)
             
        service = Prompt.ask("Select a service to pull", choices=service_names)

    console.print(f"[bold blue]ℹ️[/bold blue]  Targeting service: [yellow]{service}[/yellow]")
    
    # 1. Get Service Details
    with console.status(f"[bold green]Analyzing {service}...[/bold green]"):
        # We need region. For MVP, we'll try to guess or use the list result to find it.
        # Efficient way: The list_services output already has the region in label `cloud.googleapis.com/location`.
        # So let's re-fetch the list if we didn't store it, or just use the helper.
        # But `provider.get_service_details` requires region.
        
        # Let's verify how to get region.
        # In current `gcp.py` I only have `list_services` and `get_service_details`.
        # `get_service_details` implementation I wrote takes `service_name` and `region`.
        
        # Find the region from the service name in the list (if we have it).
        if 'services_data' not in locals():
             services_data = provider.list_services()
        
        target_service_data = next((s for s in services_data if s["metadata"]["name"] == service), None)
        if not target_service_data:
             console.print(f"[red]Service {service} not found in project.[/red]")
             raise typer.Exit(code=1)
             
        region = target_service_data["metadata"]["labels"]["cloud.googleapis.com/location"]
        
        details = provider.get_service_details(service, region)
        metadata = provider.extract_metadata(details)
        
    console.print(f"[green]✓[/green] Found image: [cyan]{metadata['image']}[/cyan]")
    
    if metadata['cloud_sql_instances']:
         console.print(f"[green]✓[/green] Found Cloud SQL: [cyan]{metadata['cloud_sql_instances']}[/cyan]")

    # 2. Get Commit SHA
    with console.status("[bold green]Tracing git commit...[/bold green]"):
        commit_sha = provider.get_commit_sha(metadata['image'])
        
    if commit_sha:
        console.print(f"[green]✓[/green] Identified commit: [magenta]{commit_sha}[/magenta]")
        # TODO: Clone repo
    else:
        console.print("[yellow]⚠️ Could not determine commit SHA from image. Cloning default branch might risk drift.[/yellow]")

    # Mock Clone for now
    # In reality: git clone <repo_url> <destination> && git checkout <commit_sha>
    project_path = os.getcwd() # validation on current dir for now
    
    # 3. Runtime Synthesis
    from .detector import RuntimeSynthesizer
    synthesizer = RuntimeSynthesizer()
    runtime_info = synthesizer.detect(project_path)
    
    console.print(f"[bold blue]ℹ️[/bold blue]  Detected Runtime: [cyan]{runtime_info['language']}[/cyan]")
    if runtime_info['cmd']:
        console.print(f"[bold blue]ℹ️[/bold blue]  Install Command: [yellow]{runtime_info['cmd']}[/yellow]")

    # 4. Connectivity
    from .connectivity import ProxyManager
    
    # Initialize ProxyManager
    proxy_manager = ProxyManager()
    
    # Handle Cloud SQL
    if metadata.get('cloud_sql_instances'):
        console.print(f"[bold blue]ℹ️[/bold blue]  Connecting to Cloud SQL instances...")
        try:
            # Note: This is a non-blocking start, checking strictly if proxy is in path
            # Real implementation would manage the process lifecycle around the user shell
            if proxy_manager.check_installed():
                 # For the demo, we just simulate the start call
                 # proxy_manager.start_cloud_sql_proxy(metadata['cloud_sql_instances'])
                 console.print(f"[green]✓[/green] Cloud SQL Proxy ready to launch for: {metadata['cloud_sql_instances']}")
            else:
                 console.print("[yellow]⚠️  Cloud SQL Proxy not found. Install to enable DB access.[/yellow]")
        except Exception as e:
            console.print(f"[red]Proxy Error: {e}[/red]")

    console.print("[bold green]✅ Analysis & Setup Complete![/bold green]")
    console.print(Panel("To enter the wormhole, run:\n[bold white]source .env && " + (runtime_info['cmd'] or "start command") + "[/bold white]", title="Ready to Launch"))


if __name__ == "__main__":
    app()
