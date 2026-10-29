
import { dualValidateCode } from "../services/conversionService.js";
import { convertWithAI } from "../services/aiService.js";
import Migration from "../models/Migration.js";

export const migrateCode = async (req, res) => {
  try {
    const {
      sourceCode,
      sourceLanguage,
      targetLanguage,
      stdin = ""
    } = req.body;

    if (
      typeof sourceCode !== "string" ||
      !sourceCode.trim() ||
      sourceCode.length > 10000
    ) {
      return res.status(400).json({
        success: false,
        message: "Valid source code is required (max 10000 characters)"
      });
    }

    if (
      sourceLanguage !== "python" ||
      targetLanguage !== "cpp"
    ) {
      return res.status(400).json({
        success: false,
        message: "Only Python to C++ is supported"
      });
    }

    if (typeof stdin !== "string" || stdin.length > 4000) {
      return res.status(400).json({
        success: false,
        message: "Custom input must be a string (max 4000 characters)"
      });
    }

    const validation = await dualValidateCode(sourceCode, stdin);

    if (!validation.validated) {
      return res.status(422).json({
        success: false,
        message: validation.error || "Triple validation failed",
        validated: false,
        failedConverter: validation.failedConverter,
        pythonOutput: validation.pythonOutput,
        astOutput: validation.astOutput,
        ollamaOutput: validation.ollamaOutput
      });
    }

    const result = {
      convertedCode: validation.convertedCode,
      method: validation.method || "ast-based"
    };

  const migration = await Migration.create({
      sourceCode,
      convertedCode: result.convertedCode,
      sourceLanguage,
      targetLanguage,
      method: result.method
    });

    return res.status(201).json({
      success: true,
      message: "Code converted and saved successfully",
      migrationId: migration._id,
      convertedCode: result.convertedCode,
      method: result.method,
      validated: true,
      pythonOutput: validation.pythonOutput,
      astOutput: validation.astOutput,
      ollamaOutput: validation.ollamaOutput,
      ollamaCode: validation.ollamaCode
    });

  } catch (error) {
    console.error("Migration error:", error.message);

    return res.status(error.status || 500).json({
      success: false,
      message: error.message || "Conversion or database operation failed"
    });
  }
};
