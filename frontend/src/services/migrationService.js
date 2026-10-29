
import api from "../api/axios.js";

export const convertCode = async (data) => {
  const response = await api.post("/migration/convert", data);
  return response.data;
};
