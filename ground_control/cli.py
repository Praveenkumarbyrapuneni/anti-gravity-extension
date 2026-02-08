import typer
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from typing import Optional
import os
import subprocess
import sys
from .auth import check_gcloud_auth
from .providers.gcp import GCPProvider
from .connectivity import ProxyManager, SecretManager

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
    write_env: bool = typer.Option(False, "--write-env", help="Write secrets to .env file instead of injecting into a subshell."),
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
    
    # --- Service Selection ---
    if not service:
        with console.status("[bold green]Scanning for services...[/bold green]"):
            services_data = provider.list_services()
            
        if not services_data:
            console.print("[red]No services found or access denied.[/red]")
            raise typer.Exit(code=1)
            
        service_names = [s.get("metadata", {}).get("name") for s in services_data]
        
        if not service_names:
             console.print("[red]No managed services found.[/red]")
             raise typer.Exit(code=1)
             
        service = Prompt.ask("Select a service to pull", choices=service_names)

    console.print(f"[bold blue]ℹ️[/bold blue]  Targeting service: [yellow]{service}[/yellow]")
    
    # --- Analysis & Metadata ---
    with console.status(f"[bold green]Analyzing {service}...[/bold green]"):
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

    # --- Git Commit SHA ---
    with console.status("[bold green]Tracing git commit...[/bold green]"):
        commit_sha = provider.get_commit_sha(metadata['image'])
        
    if commit_sha:
        console.print(f"[green]✓[/green] Identified commit: [magenta]{commit_sha}[/magenta]")
        # TODO: Clone repo operation here
    else:
        console.print("[bold yellow]⚠️  Could not determine commit SHA from image tags.[/bold yellow]")
        console.print("   [yellow]Falling back to HEAD. Be aware of potential drift![/yellow]")
        commit_sha = "HEAD"

    # --- Runtime Detection ---
    project_path = os.getcwd() # MVP: assumes running in project root
    from .detector import RuntimeSynthesizer
    synthesizer = RuntimeSynthesizer()
    runtime_info = synthesizer.detect(project_path)
    
    console.print(f"[bold blue]ℹ️[/bold blue]  Detected Runtime: [cyan]{runtime_info['language']}[/cyan]")

    # --- Proxy & Connectivity ---
    proxy_manager = ProxyManager()
    active_proxies = {}
    
    if metadata.get('cloud_sql_instances'):
        console.print(f"[bold blue]ℹ️[/bold blue]  Connecting to Cloud SQL instances...")
        try:
            active_proxies = proxy_manager.start_cloud_sql_proxy(metadata['cloud_sql_instances'])
        except Exception as e:
            console.print(f"[red]Proxy Error: {e}[/red]")

    # --- Secrets & Environment ---
    env_updates = {}
    
    # 1. Plain Env Vars
    env_updates.update(metadata.get('env_vars', {}))
    
    # 2. Proxy Ports (Injection)
    # Inject DB_HOST / DB_PORT based on proxy mapping? 
    # For now, just exposing them might be enough, or user app expects specific names.
    # Let's auto-inject recommended vars:
    for instance, port in active_proxies.items():
        # Heuristic: set DB_PORT if only one?
        # Or just let the user know.
        pass

    # 3. Fetch Secrets
    secret_manager = SecretManager(project_id)
    secrets_map = metadata.get('secrets', {})
    
    if secrets_map:
        with console.status(f"[bold green]Fetching {len(secrets_map)} secrets from Secret Manager...[/bold green]"):
            for env_name, secret_info in secrets_map.items():
                secret_id = secret_info['secret']
                version = secret_info['version']
                # Clean up version if strictly 'latest' or numeric.
                # Cloud Run 'key' often effectively means version.
                
                payload = secret_manager.fetch_secret(secret_id, version)
                if payload:
                    env_updates[env_name] = payload
                    console.print(f"[gray]   + Injected {env_name}[/gray]")
                else:
                    console.print(f"[red]   x Failed to fetch {env_name}[/red]")

    # --- Execution Handover ---
    
    if write_env:
        # Write to .env file
        with open(".env", "w") as f:
            for k, v in env_updates.items():
                # Simple escaping
                f.write(f"{k}={v}\n")
        console.print("[bold green]✅ .env file generated.[/bold green]")
        console.print("[yellow]⚠️  Warning: Secrets are now on disk. Delete .env when done.[/yellow]")
        
        # We still keep the proxy running?
        # If we write .env and exit, the proxy (subprocess) will likely die or be orphaned.
        # User requested robustness.
        console.print("[bold red]🛑 proxies will stop when this command exits.[/bold red]")
        console.print(Panel(f"Run:\n[bold white]source .env && {runtime_info['cmd'] or 'your-start-command'}[/bold white]", title="Manual Launch"))
        
        # If we want to keep proxy alive, we must wait.
        if active_proxies:
            Prompt.ask("Press Enter to stop proxies and exit", show_default=False)
            proxy_manager.stop()
            
    else:
        # Memory-First: Spawn Subshell
        console.print("[bold green]✅ Environment ready.[/bold green]")
        console.print(Panel("Spawning shell with injected secrets...\n[bold white]You are entering the Wormhole.[/bold white]", title="🚀 Warp Speed"))
        
        target_env = os.environ.copy()
        target_env.update(env_updates)
        
        # Determine shell
        shell = os.environ.get("SHELL", "/bin/bash")
        
        try:
            # We use subprocess.call to wait for the shell to exit
            subprocess.call([shell], env=target_env)
        except Exception as e:
             console.print(f"[red]Shell error: {e}[/red]")
        finally:
             console.print("\n[bold blue]ℹ️[/bold blue]  Exiting Wormhole. Stopping proxies...")
             proxy_manager.stop()

if __name__ == "__main__":
    app()
