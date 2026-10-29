
import { validateCpp } from "../services/validationService.js";

export const validateCode = async (req, res) => {
  try {
    const { code, language } = req.body;

    if (language !== "cpp") {
      return res.status(400).json({
        success: false,
        message: "Only C++ validation is supported"
      });
    }

    const result = await validateCpp(code);
    return res.json(result);
  } catch (error) {
    return res.status(error.status || 500).json({
      success: false,
      message: error.status === 400
        ? error.message
        : "Validation service unavailable"
    });
  }
};
