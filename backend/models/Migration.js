import mongoose from "mongoose";

const migrationSchema = new mongoose.Schema(
    {
        sourceCode: {
            type: String,
            required: true,
        },

        convertedCode: {
            type: String,
            required: true,
        },

        sourceLanguage: {
            type: String,
            required: true,
            default: "python",
        },

        targetLanguage: {
            type: String,
            required: true,
            default: "cpp",
        },

        method: {
            type: String,
            enum: [
                "ast-based",
                "ai-assisted",
                "dual-validated",
                "ollama-fallback",
            ],
            required: true,
        },

        validationStatus: {
            type: String,
            enum: ["not-checked", "passed", "failed"],
            default: "not-checked",
        },
    },
    { timestamps: true },
);

const Migration = mongoose.model("Migration", migrationSchema);

export default Migration;
