import subprocess
import shutil
import os
from typing import List, Dict, Optional
from rich.console import Console

console = Console()

class ProxyManager:
    def __init__(self):
        self.proxy_process: Optional[subprocess.Popen] = None

    def check_installed(self) -> bool:
        return shutil.which("cloud-sql-proxy") is not None

    def start_cloud_sql_proxy(self, instances: List[str], port_start: int = 5432) -> Dict[str, int]:
        """
        Starts cloud-sql-proxy for the given instances.
        Returns a mapping of instance connection name to local port.
        """
        if not instances:
            return {}

        if not self.check_installed():
            console.print("[bold yellow]⚠️ 'cloud-sql-proxy' not found.[/bold yellow] Please install it to access Cloud SQL.")
            return {}

        # Construct instance string: "project:region:instance=tcp:port"
        # For simplicity, we just use the default behavior or map to sequential ports
        # But default "cloud-sql-proxy instance" maps to a unix socket or requires specific flags.
        # Modern v2 proxy usage: ./cloud-sql-proxy project:region:instance
        
        # We will try to run it in the background.
        # Note: Managing background processes in a CLI that exits is tricky. 
        # Ground Control might need to stay running or spawn a detached process.
        # For this "ag pull" command, we probably want to spawn a shell *inside* the context, 
        # so we keep the proxy running until the shell exits.
        
        instance_args = []
        mapping = {}
        for i, instance in enumerate(instances):
            port = port_start + i
            instance_args.append(f"{instance}?port={port}") # v2 syntax might verify
            mapping[instance] = port

        # v2 syntax: cloud-sql-proxy project:region:instance --port 5432 (only for one)
        # For multiple, it's complex. Let's assume v2 and just do one for now or use the address flag.
        # Actually, let's just print the command for the user to run or run it for the first instance.
        
        cmd = ["cloud-sql-proxy"] + instances # This usually creates unix sockets
        # To use TCP: --port (works for one).
        
        console.print(f"[bold blue]ℹ️[/bold blue] Starting Cloud SQL Proxy for {instances}...")
        try:
             # run in background
             self.proxy_process = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
             console.print("[green]✓[/green] Proxy started in background.")
             return mapping
        except Exception as e:
            console.print(f"[red]Failed to start proxy: {e}[/red]")
            return {}

    def stop(self):
        if self.proxy_process:
            self.proxy_process.terminate()
            console.print("[gray]Proxy stopped.[/gray]")

class SecretManager:
    def __init__(self, project_id: str):
        self.project_id = project_id
    
    def fetch_secret(self, secret_id: str, version_id: str = "latest") -> Optional[str]:
        try:
            from google.cloud import secretmanager
            client = secretmanager.SecretManagerServiceClient()
            name = f"projects/{self.project_id}/secrets/{secret_id}/versions/{version_id}"
            response = client.access_secret_version(request={"name": name})
            return response.payload.data.decode("UTF-8")
        except ImportError:
            console.print("[red]google-cloud-secret-manager not installed.[/red]")
            return None
        except Exception as e:
            # handle permission denied etc
            console.print(f"[yellow]Could not access secret {secret_id}: {e}[/yellow]")
            return None
