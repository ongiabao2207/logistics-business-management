import axios from "axios";

import { clearAuthToken, getAuthToken } from "./authToken";

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
    // A token can expire while the user is working, or become invalid after
    // Identity Service rotates its development signing key.  Clear it here so
    // protected screens immediately return to the login page instead of
    // continuing to submit unusable credentials.
    if (error.response?.status === 401 && getAuthToken()) {
      clearAuthToken();
      window.dispatchEvent(new Event("logistics:unauthenticated"));
    }

    const detail = error.response?.data?.detail;
    const message = typeof detail === "string" ? detail : error.message;

    return Promise.reject({
      status: error.response?.status,
      message,
      originalError: error,
    });
  },
);
