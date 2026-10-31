import threading
import requests.exceptions
import docker
import tempfile
from pathlib import Path
from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel, Field
import os
import secrets

app = FastAPI(title="Local Worker Launcher")
client = docker.from_env()

execution_slots = threading.BoundedSemaphore(2)
SHARED_VOLUME = "worker-shared-data"


class ExecuteRequest(BaseModel):
    language: str
    code: str = Field(min_length=1, max_length=10000)
    stdin: str = Field(default="", max_length=10000)


@app.get("/health")
def health():
    return {"status": "running"}


@app.post("/execute")
def execute(
    request: ExecuteRequest,
    x_worker_key: str | None = Header(default=None)
):
    expected_key = os.getenv("WORKER_API_KEY")

    if (
        not expected_key
        or not x_worker_key
        or not secrets.compare_digest(x_worker_key, expected_key)
    ):
        raise HTTPException(status_code=401, detail="Unauthorized")

    if request.language not in ("python", "cpp"):
        raise HTTPException(status_code=400, detail="Unsupported language")

    if not execution_slots.acquire(blocking=False):
        raise HTTPException(status_code=429, detail="Worker busy")

    try:
        return run_sandbox(request)
    finally:
        execution_slots.release()


def run_sandbox(request: ExecuteRequest):
    with tempfile.TemporaryDirectory(dir="/shared") as folder:

        source = Path(folder) / (
            "source.py" if request.language == "python" else "main.cpp"
        )

        source.write_text(request.code, encoding="utf-8")

        stdin_file = Path(folder) / "stdin.txt"
        stdin_file.write_bytes(request.stdin.encode("utf-8"))

        # Allow sandbox user to read files
        os.chmod(folder, 0o755)
        os.chmod(source, 0o644)
        os.chmod(stdin_file, 0o644)

        sandbox_folder = f"/shared/{Path(folder).name}"

        if request.language == "python":
            command = [
                "sh", "-c",
                f"python3 -I -B {sandbox_folder}/source.py < {sandbox_folder}/stdin.txt"
            ]
        else:
            command = [
                "sh", "-c",
                f"g++ -std=c++17 {sandbox_folder}/main.cpp -o /tmp/main || exit 42; /tmp/main < {sandbox_folder}/stdin.txt"
            ]

        container = None

        try:
            container = client.containers.run(
                "code-execution-worker:latest",
                command=command,
                detach=True,
                network_disabled=True,
                mem_limit="256m",
                nano_cpus=1000000000,
                pids_limit=32,
                read_only=True,
                tmpfs={
                    "/tmp": "rw,exec,nosuid,nodev,size=32m"
                },
                cap_drop=["ALL"],
                security_opt=["no-new-privileges"],
                volumes={
                    SHARED_VOLUME: {
                        "bind": "/shared",
                        "mode": "ro"
                    }
                },
                user="65534:65534",
            )

            try:
                result = container.wait(timeout=25)
            except requests.exceptions.ReadTimeout:
                container.kill()
                raise HTTPException(
                    status_code=408,
                    detail="Execution exceeded 25 seconds"
                )

            output = container.logs(
                stdout=True, stderr=False
            ).decode("utf-8", errors="replace")[:4000]

            error = container.logs(
                stdout=False, stderr=True
            ).decode("utf-8", errors="replace")[:4000]

            exit_code = result["StatusCode"]

            stage = "execution"

            if request.language == "cpp" and exit_code == 42:
                stage = "compilation"

            return {
                "success": exit_code == 0,
                "stage": stage,
                "output": output,
                "error": error
            }

        except HTTPException:
            raise

        except Exception as e:
            print("Worker error:", str(e))
            raise HTTPException(
                status_code=500,
                detail="Worker execution failed"
            )

        finally:
            if container:
                try:
                    container.remove(force=True)
                except docker.errors.DockerException:
                    pass

