
import api from "../api/axios.js";

export const validateCode = async (code) => {
  const response = await api.post("/validation/check", {
    code,
    language: "cpp"
  });

  return response.data;
};
