import subprocess
import tempfile
from pathlib import Path
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="C++ Validator Service")

class ValidationRequest(BaseModel):
    code: str

@app.get("/health")
def health():
    return {"status": "running"}

@app.post("/validate")
def validate(request: ValidationRequest):
    with tempfile.TemporaryDirectory() as folder:
        path = Path(folder) / "main.cpp"
        path.write_text(request.code, encoding="utf-8")

        try:
            result = subprocess.run(
                ["g++", "-std=c++17", "-fsyntax-only", str(path)],
                capture_output=True,
                text=True,
                timeout=5
            )
            return {
                "success": result.returncode == 0,
                "output": result.stderr[:4000]
            }
        except subprocess.TimeoutExpired:
            return {"success": False, "output": "Compilation timed out"}

@app.post("/execute-cpp")
def execute_cpp(request: ValidationRequest):
    with tempfile.TemporaryDirectory() as folder:
        folder = Path(folder)
        source = folder / "main.cpp"
        executable = folder / "main"
        source.write_text(request.code, encoding="utf-8")

        try:
            compile_result = subprocess.run(
                ["g++", "-std=c++17", str(source), "-o", str(executable)],
                capture_output=True,
                text=True,
                timeout=15
            )

            if compile_result.returncode != 0:
                return {
                    "success": False,
                    "stage": "compilation",
                    "error": compile_result.stderr[:4000]
                }

            result = subprocess.run(
                [str(executable)],
                capture_output=True,
                text=True,
                timeout=5
            )

            return {
                "success": result.returncode == 0,
                "stage": "execution",
                "output": result.stdout[:4000],
                "error": result.stderr[:4000]
            }

        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "stage": "timeout",
                "error": "Execution or compilation timed out"
            }
        except OSError as error:
            return {
                "success": False,
                "stage": "system",
                "error": str(error)
            }


@app.post("/execute-python")
def execute_python(request: ValidationRequest):
    with tempfile.TemporaryDirectory() as folder:
        source = Path(folder) / "source.py"
        source.write_text(request.code, encoding="utf-8")

        try:
            result = subprocess.run(
                ["python3", "-I", "-B", str(source)],
                capture_output=True,
                text=True,
                timeout=5,
                cwd=folder
            )

            return {
                "success": result.returncode == 0,
                "stage": "execution",
                "output": result.stdout[:4000],
                "error": result.stderr[:4000]
            }

        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "stage": "timeout",
                "error": "Python execution timed out"
            }
        except OSError as error:
            return {
                "success": False,
                "stage": "system",
                "error": str(error)
            }
