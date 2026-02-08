from typing import Optional, List, Dict, Any
import subprocess
import json
from rich.console import Console

console = Console()

class GCPProvider:
    def __init__(self, project_id: str):
        self.project_id = project_id

    def list_services(self) -> List[Dict[str, Any]]:
        """
        Lists Cloud Run services in the project.
        Uses gcloud CLI for simplicity and auth reuse.
        """
        try:
            cmd = [
                "gcloud", "run", "services", "list",
                "--project", self.project_id,
                "--format=json"
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            services = json.loads(result.stdout)
            return services
        except subprocess.CalledProcessError as e:
            console.print(f"[bold red]❌ Error listing services:[/bold red] {e.stderr}")
            return []

    def get_service_details(self, service_name: str, region: str) -> Dict[str, Any]:
        """
        Gets details of a specific Cloud Run service.
        """
        try:
            cmd = [
                "gcloud", "run", "services", "describe", service_name,
                "--project", self.project_id,
                "--region", region,
                "--format=json"
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return json.loads(result.stdout)
        except subprocess.CalledProcessError as e:
            console.print(f"[bold red]❌ Error describing service:[/bold red] {e.stderr}")
            return {}

    def extract_metadata(self, service_details: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extracts image URL and other metadata from the service details.
        """
        try:
            metadata = service_details.get("metadata", {})
            spec = service_details.get("spec", {})
            template = spec.get("template", {})
            template_spec = template.get("spec", {})
            containers = template_spec.get("containers", [{}])
            container = containers[0]
            
            image = container.get("image", "")
            env_vars = {}
            secrets = {}
            if "env" in container:
                for env in container["env"]:
                    name = env.get("name")
                    value = env.get("value")
                    value_from = env.get("valueFrom")
                    
                    if name:
                        if value:
                            env_vars[name] = value
                        elif value_from and "secretKeyRef" in value_from:
                            # Store secret reference: NAME -> (secret_id, version)
                            ref = value_from["secretKeyRef"]
                            secrets[name] = {
                                "secret": ref.get("name"),
                                "version": ref.get("key", "latest") # In k8s key is key, in Cloud Run logic it maps to version usually or we need to look up.
                                # Actually in Cloud Run: 
                                # - valueFrom: secretKeyRef: {name: "my-secret", key: "latest"}
                                # key here is the version 
                            }

            annotations = metadata.get("annotations", {})
            cloud_sql_instances = annotations.get("run.googleapis.com/cloudsql-instances", "")
            cloud_sql_list = cloud_sql_instances.split(",") if cloud_sql_instances else []
            
            return {
                "image": image,
                "env_vars": env_vars,
                "secrets": secrets,
                "cloud_sql_instances": cloud_sql_list,
                "labels": metadata.get("labels", {})
            }
        except Exception as e:
            console.print(f"[bold red]❌ Error parsing service details:[/bold red] {e}")
            return {}

    def get_commit_sha(self, image_url: str) -> Optional[str]:
        """
        Attempts to find the git commit SHA from the image metadata.
        """
        try:
            # Check if image has a tag that looks like a sha
            if ":" in image_url:
                tag = image_url.split(":")[-1]
                # Heuristic: if tag is 7-40 hex chars, might be a commit sha
                if len(tag) >= 7 and all(c in "0123456789abcdef" for c in tag):
                    return tag

            # If not in tag, try to describe the image
            cmd = [
                "gcloud", "artifacts", "docker", "images", "describe", image_url,
                "--format=json"
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                # Fallback to container registry if artifact registry fails
                cmd = [
                    "gcloud", "container", "images", "describe", image_url,
                    "--format=json"
                ]
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode != 0:
                    console.print(f"[yellow]⚠️ Could not describe image {image_url}[/yellow]")
                    return None
            
            image_data = json.loads(result.stdout)
            
            # Look for VCS ref in labels
            # Common label keys
            validation_keys = [
                "org.opencontainers.image.revision",
                "org.label-schema.vcs-ref",
                "gcb-build-id", # If we have build ID, we might need another call, but let's check config first
            ]
            
            # Check basic config labels
            config = image_data.get("config", {})
            labels = config.get("config", {}).get("labels", {})
            
            for key in validation_keys:
                if key in labels:
                    return labels[key]
            
            # Check build info if available (image_summary.build_details) - specific to GCR/GAR
            # This part is tricky as structure varies. 
            # Simplified flow: assume the tag IS the commit hash for this MVP or close enough.
            
            return None

        except Exception as e:
            console.print(f"[bold red]❌ Error analyzing image:[/bold red] {e}")
            return None
