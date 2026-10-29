import axios from "axios";

export const convertPythonToCpp = async (sourceCode) => {
    try {
        const response = await axios.post(
            `${process.env.CONVERTER_URL}/convert`,
            { sourceCode },
            { timeout: 10000 },
        );

        return response.data.convertedCode;
    } catch (error) {
        if (error.response) {
            const detail = error.response.data?.detail;

            const serviceError = new Error(
                typeof detail === "object"
                    ? detail.message
                    : String(detail || "AST conversion failed"),
            );

            serviceError.status = error.response.status;
            serviceError.code = detail?.errorCode || "CONVERSION_ERROR";

            throw serviceError;
        }

        const serviceError = new Error(
            "Converter service unavailable or timed out",
        );
        serviceError.status = 503;
        throw serviceError;
    }
};

export const dualValidateCode = async (sourceCode, stdin = "") => {
    try {
        const response = await axios.post(
            `${process.env.CONVERTER_URL}/dual-validate`,
            { sourceCode, stdin },
            { timeout: 120000, headers: { "X-Converter-Key": process.env.CONVERTER_API_KEY } },
        );

        return response.data;
    } catch (error) {
        if (error.response) {
            const serviceError = new Error(
                error.response.data?.detail?.message ||
                    error.response.data?.detail ||
                    "Dual validation failed",
            );
            serviceError.status = error.response.status;
            throw serviceError;
        }

        const serviceError = new Error(
            "Converter service unavailable or timed out",
        );
        serviceError.status = 503;
        throw serviceError;
    }
};
