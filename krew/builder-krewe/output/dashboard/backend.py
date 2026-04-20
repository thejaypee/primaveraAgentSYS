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
    SSH_HOSTS = {
        "100.104.65.53": "don1",
        "100.101.70.84": "don2",
        "100.85.15.80":  "saulynode",
        "100.96.141.26": "wsl",
    }

    def _ssh_hardware(self, host_alias: str) -> Dict[str, Any]:
        cmd = (
            "cpu=$(grep 'model name' /proc/cpuinfo | head -1 | cut -d: -f2 | xargs); "
            "cores=$(nproc); "
            "ram=$(free -m | awk 'NR==2{printf \"%.1fGB\", $2/1024}'); "
            "disk=$(df -h / | awk 'NR==2{print $2}'); "
            "gpu=$(nvidia-smi --query-gpu=name --format=csv,noheader 2>/dev/null | head -1 || echo ''); "
            "echo \"$cpu|$cores|$ram|$disk|$gpu\""
        )
        try:
            out = subprocess.check_output(
                ["ssh", "-o", "ConnectTimeout=3", "-o", "BatchMode=yes", host_alias, cmd],
                text=True, stderr=subprocess.DEVNULL
            ).strip()
            cpu, cores, ram, disk, gpu = out.split("|")
            result = {"cpu": cpu, "cores": int(cores), "ram": ram, "disk": disk}
            if gpu:
                result["gpu"] = gpu
            return result
        except Exception:
            return {}

    def _ping(self, ip: str):
        try:
            out = subprocess.check_output(
                ["ping", "-c", "1", "-W", "1", ip],
                stderr=subprocess.DEVNULL, text=True
            )
            import re
            m = re.search(r"time=([\d.]+)", out)
            return round(float(m.group(1)), 1) if m else 0.0
        except subprocess.CalledProcessError:
            return None

    def get_nodes(self) -> List[Dict[str, Any]]:
        try:
            out = subprocess.check_output(["tailscale", "status", "--json"], text=True)
            data = json.loads(out)
        except Exception:
            return []

        raw = []
        self_node = data.get("Self", {})
        if self_node:
            raw.append({
                "name": self_node.get("HostName", ""),
                "ip": self_node.get("TailscaleIPs", [""])[0],
                "os": self_node.get("OS", ""),
                "self": True,
            })
        for peer in data.get("Peer", {}).values():
            if peer.get("OS") == "iOS":
                continue
            raw.append({
                "name": peer.get("HostName", ""),
                "ip": peer.get("TailscaleIPs", [""])[0],
                "os": peer.get("OS", ""),
                "self": False,
            })

        from concurrent.futures import ThreadPoolExecutor
        def check(node):
            if node["self"]:
                node["latency_ms"] = 0.0
            else:
                node["latency_ms"] = self._ping(node["ip"])
            node["reachable"] = node["latency_ms"] is not None
            alias = self.SSH_HOSTS.get(node["ip"])
            node["hardware"] = self._ssh_hardware(alias) if alias else {}
            return node

        with ThreadPoolExecutor(max_workers=12) as ex:
            nodes = list(ex.map(check, raw))

        nodes.sort(key=lambda n: (not n["reachable"], n.get("latency_ms") or 9999))
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
