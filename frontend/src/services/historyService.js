
import api from "../api/axios.js";

export const getConversionHistory = async () => {
  const response = await api.get("/history");
  return response.data;
};

export const getMigrationById = async (id) => {
  const response = await api.get(`/history/${id}`);
  return response.data;
};

export const deleteConversion = async (id) => {
  const response = await api.delete(`/history/${id}`);
  return response.data;
};
