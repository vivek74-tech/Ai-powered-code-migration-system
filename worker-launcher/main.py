import docker
import tempfile
from pathlib import Path
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

app = FastAPI(title="Local Worker Launcher")
client = docker.from_env()

class ExecuteRequest(BaseModel):
    language: str
    code: str = Field(min_length=1, max_length=10000)

@app.get("/health")
def health():
    return {"status": "running"}

@app.post("/execute")
def execute(request: ExecuteRequest):
    if request.language not in ("python", "cpp"):
        raise HTTPException(status_code=400, detail="Unsupported language")

    with tempfile.TemporaryDirectory() as folder:
        source = Path(folder) / (
            "source.py" if request.language == "python" else "main.cpp"
        )
        source.write_text(request.code, encoding="utf-8")

        if request.language == "python":
            command = ["python3", "-I", "-B", "/sandbox/source.py"]
        else:
            command = [
                "sh", "-c",
                "g++ -std=c++17 /sandbox/main.cpp -o /tmp/main || exit 42; /tmp/main"
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
                tmpfs={"/tmp": "rw,exec,nosuid,nodev,size=32m"},
                cap_drop=["ALL"],
                security_opt=["no-new-privileges"],
                volumes={
                    str(source.resolve()): {
                        "bind": "/sandbox/" + source.name,
                        "mode": "ro"
                    }
                },
                user="65534:65534",
            )

            result = container.wait(timeout=25)
            output = container.logs(stdout=True, stderr=False).decode(
                "utf-8", errors="replace"
            )[:4000]
            error = container.logs(stdout=False, stderr=True).decode(
                "utf-8", errors="replace"
            )[:4000]

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

        except Exception as exc:
            raise HTTPException(status_code=500, detail=str(exc))
        finally:
            if container:
                try:
                    container.remove(force=True)
                except docker.errors.DockerException:
                    pass
