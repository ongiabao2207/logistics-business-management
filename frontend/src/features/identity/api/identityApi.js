import { httpClient } from "../../../services/httpClient";

export const identityApi = {
  login(payload) {
    return httpClient.post("/identity/login", payload);
  },
  getCurrentUser() {
    return httpClient.get("/identity/me");
  },
};
