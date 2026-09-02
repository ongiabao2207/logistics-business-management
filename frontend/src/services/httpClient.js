import axios from "axios";

import { getAuthToken } from "./authToken";

export const httpClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? "",
  headers: {
    "Content-Type": "application/json",
  },
});

httpClient.interceptors.request.use((config) => {
  const token = getAuthToken();

  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }

  return config;
});

httpClient.interceptors.response.use(
  (response) => response.data,
  (error) => {
    const detail = error.response?.data?.detail;
    const message = typeof detail === "string" ? detail : error.message;

    return Promise.reject({
      status: error.response?.status,
      message,
      originalError: error,
    });
  },
);
