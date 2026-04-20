import json
import os
import subprocess
from pathlib import Path
from typing import List, Dict, Any

from fastapi import FastAPI
from fastapi.responses import FileResponse
import psutil
import docker

DASHBOARD_DIR = Path(__file__).parent


class DockerService:
    def __init__(self):
        try:
            self.client = docker.from_env()
            self.client.ping()
        except docker.errors.DockerException:
            self.client = None

    def get_running_containers(self) -> List[Dict[str, Any]]:
        if not self.client:
            return []
        try:
            return [
                {
                    "id": c.short_id,
                    "name": c.name,
                    "image": c.image.tags[0] if c.image.tags else "unknown",
                    "status": c.status,
                    "ports": dict(c.ports),
                }
                for c in self.client.containers.list()
            ]
        except Exception:
            return []


class NetworkService:
    def get_all_interfaces(self) -> List[Dict[str, Any]]:
        result = []
        for name, addresses in psutil.net_if_addrs().items():
            entry = {"interface": name, "addresses": []}
            for addr in addresses:
                import socket
                if addr.family == socket.AF_INET:
                    entry["addresses"].append({"ip": addr.address, "netmask": addr.netmask})
                elif addr.family == psutil.AF_LINK:
                    entry["addresses"].append({"mac": addr.address})
            result.append(entry)
        return result


class HiveService:
    def get_nodes(self) -> List[Dict[str, Any]]:
        try:
            out = subprocess.check_output(["tailscale", "status", "--json"], text=True)
            data = json.loads(out)
        except Exception:
            return []

        nodes = []
        self_node = data.get("Self", {})
        if self_node:
            nodes.append({
                "name": self_node.get("HostName", ""),
                "ip": self_node.get("TailscaleIPs", [""])[0],
                "os": self_node.get("OS", ""),
                "online": self_node.get("Online", False),
                "active": self_node.get("Active", False),
                "self": True,
            })

        for peer in data.get("Peer", {}).values():
            nodes.append({
                "name": peer.get("HostName", ""),
                "ip": peer.get("TailscaleIPs", [""])[0],
                "os": peer.get("OS", ""),
                "online": peer.get("Online", False),
                "active": peer.get("Active", False),
                "self": False,
            })

        nodes.sort(key=lambda n: (not n["online"], not n["active"], n["name"]))
        return nodes


class HardwareService:
    def get_gpu_utilization(self) -> Dict[str, Any]:
        import subprocess
        try:
            out = subprocess.check_output(
                ["nvidia-smi", "--query-gpu=name,utilization.gpu,memory.used,memory.total",
                 "--format=csv,noheader,nounits"],
                text=True
            ).strip()
            name, util, mem_used, mem_total = [x.strip() for x in out.split(",")]
            return {
                "gpu_model": name,
                "gpu_utilization_percent": float(util),
                "memory_used_mb": float(mem_used),
                "memory_total_mb": float(mem_total),
            }
        except Exception:
            return {"error": "nvidia-smi unavailable"}


app = FastAPI(title="Krewe Dashboard API", version="1.0.0")

docker_svc = DockerService()
network_svc = NetworkService()
hardware_svc = HardwareService()
hive_svc = HiveService()


@app.get("/")
async def root():
    return FileResponse(DASHBOARD_DIR / "index.html")


@app.get("/health")
async def health_check():
    return {"status": "ok"}


@app.get("/system/docker/containers")
async def get_docker_context():
    return {"containers": docker_svc.get_running_containers()}


@app.get("/system/network")
async def get_network_context():
    return {"interfaces": network_svc.get_all_interfaces()}


@app.get("/system/hardware/gpu")
async def get_gpu_context():
    return {"metrics": hardware_svc.get_gpu_utilization()}


@app.get("/hive/nodes")
async def get_hive_nodes():
    return {"nodes": hive_svc.get_nodes()}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
