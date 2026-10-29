
import { spawn } from "node:child_process";
import { randomUUID } from "node:crypto";
import fs from "node:fs/promises";
import os from "node:os";
import path from "node:path";

export const validateCpp = async (code) => {
  if (typeof code !== "string" || !code.trim()) {
    const error = new Error("C++ code is required");
    error.status = 400;
    throw error;
  }

  if (Buffer.byteLength(code, "utf8") > 20000) {
    const error = new Error("Maximum code size is 20 KB");
    error.status = 400;
    throw error;
  }

  const dir = await fs.mkdtemp(
    path.join(os.tmpdir(), "cpp-validation-")
  );

  const file = path.join(dir, `${randomUUID()}.cpp`);

  try {
    await fs.writeFile(file, code, { mode: 0o644 });

    return await new Promise((resolve, reject) => {
      const args = [
        "run", "--rm",
        "--network", "none",
        "--cpus", "0.5",
        "--memory", "256m",
        "--memory-swap", "256m",
        "--pids-limit", "64",
        "--read-only",
        "--cap-drop", "ALL",
        "--security-opt", "no-new-privileges",
        "--user", "10001:10001",
        "--mount",
        `type=bind,src=${file},dst=/workspace/input.cpp,readonly`,
        "code-migration-validator",
        "g++", "-std=c++17", "-fsyntax-only",
        "-fmax-errors=5", "/workspace/input.cpp"
      ];

      const child = spawn("docker", args, {
        stdio: ["ignore", "pipe", "pipe"]
      });

      let diagnostics = "";
      let timedOut = false;

      const collect = (chunk) => {
        diagnostics += chunk.toString().slice(
          0, Math.max(0, 12000 - diagnostics.length)
        );
      };

      child.stdout.on("data", collect);
      child.stderr.on("data", collect);

      const timer = setTimeout(() => {
        timedOut = true;
        child.kill("SIGKILL");
      }, 10000);

      child.on("error", (error) => {
        clearTimeout(timer);
        reject(error);
      });

      child.on("close", (exitCode) => {
        clearTimeout(timer);

        resolve({
          success: exitCode === 0 && !timedOut,
          status: timedOut
            ? "timeout"
            : exitCode === 0
              ? "passed"
              : "failed",
          message: timedOut
            ? "Compiler timed out"
            : exitCode === 0
              ? "C++ syntax check passed"
              : "C++ syntax check failed",
          errors: diagnostics
        });
      });
    });
  } finally {
    await fs.rm(dir, { recursive: true, force: true });
  }
};
