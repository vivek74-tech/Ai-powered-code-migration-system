
import { executeCpp } from "../services/executionService.js";

export const executeCode = async (req, res) => {
    try {
        const { code, stdin = "" } = req.body;

        if (typeof code !== "string" || !code.trim()) {
            return res.status(400).json({
                success: false,
                message: "C++ code is required"
            });
        }

        if (typeof stdin !== "string") {
            return res.status(400).json({
                success: false,
                message: "Input must be a string"
            });
        }

        const result = await executeCpp(code, stdin);

        return res.status(200).json(result);

    } catch (error) {
        return res.status(error.status || 500).json({
            success: false,
            message: error.message || "Code execution failed"
        });
    }
};
