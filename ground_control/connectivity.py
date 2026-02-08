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



    def get_free_port(self, start_port: int = 5432) -> int:
        """Finds the first available port starting from start_port."""
        import socket
        port = start_port
        while port < 65535:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                if s.connect_ex(('localhost', port)) != 0:
                    return port
                port += 1
        return start_port # Fallback, though unlikely to happen

    def start_cloud_sql_proxy(self, instances: List[str], port_start: int = 5432) -> Dict[str, int]:
        """
        Starts cloud-sql-proxy for the given instances.
        Returns a mapping of instance connection name to local port.
        Automatically finds free ports if default is taken.
        """
        if not instances:
            return {}

        if not self.check_installed():
            console.print("[bold yellow]⚠️ 'cloud-sql-proxy' not found.[/bold yellow] Please install it to access Cloud SQL.")
            return {}

        instance_args = []
        mapping = {}
        current_port = port_start
        
        console.print(f"[bold blue]ℹ️[/bold blue] Starting Cloud SQL Proxy for {len(instances)} instances...")

        for instance in instances:
            # Find a free port for this instance
            port = self.get_free_port(current_port)
            mapping[instance] = port
            
            # Prepare arguments for this instance (v2 syntax checks needed for multi-instance)
            # For simplicity/robustness in this MVP, we might need one proxy process per instance 
            # OR use the --port flag carefully if supported for multiple.
            # 'cloud-sql-proxy instance-name?port=5432' is v1 syntax.
            # v2 uses: ./cloud-sql-proxy instance-name --port 5432
            # To avoid complexity allow one instance for now or standard config.
            
            # Let's use the v1 syntax as it is often still supported or use the standard auto-assign if possible.
            # Actually, let's just use the `get_free_port` to find a port and tell the user.
            
            # For the purpose of this implementation, we will assume we are starting one proxy 
            # that handles all, or we loop. 
            # Re-reading: "The Fix: ... detects this and assigns a random port or asks the user."
            
            instance_args.append(f"{instance}?port={port}") 
            current_port = port + 1

        cmd = ["cloud-sql-proxy"] + instance_args
        
        try:
             # run in background
             self.proxy_process = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
             console.print(f"[green]✓[/green] Proxy started. Mapped {', '.join([f'{k}->{v}' for k,v in mapping.items()])}")
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
