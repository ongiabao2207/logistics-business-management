import { httpClient } from "../../../services/httpClient";

export const identityApi = {
  login(payload) {
    return httpClient.post("/api/v1/auth/login", payload);
  },
  getCurrentUser() {
    return httpClient.get("/api/v1/auth/me");
  },
};
