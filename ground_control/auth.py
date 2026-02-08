import subprocess
import shutil
from rich.console import Console

console = Console()

def check_gcloud_auth() -> bool:
    """
    Checks if gcloud is installed and authenticated.
    """
    if not shutil.which("gcloud"):
        console.print("[bold red]❌ Error:[/bold red] 'gcloud' CLI not found. Please install the Google Cloud SDK.")
        return False

    try:
        # Check if we have active credentials
        result = subprocess.run(
            ["gcloud", "auth", "list", "--filter=status:ACTIVE", "--format=value(account)"],
            capture_output=True,
            text=True,
            check=True
        )
        account = result.stdout.strip()
        if account:
            console.print(f"[bold green]✓[/bold green] Authenticated as: [cyan]{account}[/cyan]")
            return True
        else:
            console.print("[bold yellow]⚠️ Warning:[/bold yellow] No active account found in gcloud. Please run 'gcloud auth login'.")
            return False
    except subprocess.CalledProcessError:
         console.print("[bold red]❌ Error:[/bold red] Failed to check gcloud status.")
         return False
