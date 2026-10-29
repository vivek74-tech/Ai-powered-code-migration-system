
import axios from "axios";

export const convertWithAI = async (pythonCode) => {
  const response = await axios.post(
    `${process.env.OLLAMA_URL || "http://localhost:11434"}/api/generate`,
    {
      model: "qwen2.5-coder:1.5b",
      prompt: `
Convert the following Python code to C++17.

Rules:
- Return only valid C++ code.
- Include necessary headers.
- Preserve the original logic.
- Do not include Markdown explanations.

Python code:
${pythonCode}
`,
      stream: false
    },
    {
      timeout: 120000
    }
  );

  return response.data.response.trim();
};
