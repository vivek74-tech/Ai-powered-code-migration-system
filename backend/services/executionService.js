
import axios from "axios";

export const executeCpp = async (code, stdin = "") => {
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

    if (typeof stdin !== "string" || stdin.length > 10000) {
        const error = new Error("Invalid stdin or input is too large");
        error.status = 400;
        throw error;
    }

    try {
        const response = await axios.post(
            process.env.WORKER_URL,
            {
                language: "cpp",
                code,
                stdin
            },
            {
                headers: {
                    "X-Worker-Key": process.env.WORKER_API_KEY
                },
                timeout: 35000
            }
        );

        return response.data;

    } catch (error) {
        if (error.response) {
            const serviceError = new Error(
                error.response.data?.detail || "C++ execution failed"
            );

            serviceError.status = error.response.status;
            throw serviceError;
        }

        if (error.code === "ECONNABORTED") {
            const timeoutError = new Error("Execution request timed out");
            timeoutError.status = 504;
            throw timeoutError;
        }

        const serviceError = new Error("Worker service unavailable");
        serviceError.status = 503;
        throw serviceError;
    }
};
