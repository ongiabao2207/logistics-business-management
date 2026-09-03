import { httpClient } from "../../../services/httpClient";

export const identityApi = {
  login(payload) {
    return httpClient.post("/api/v1/auth/login", payload);
  },
  getCurrentUser() {
    return httpClient.get("/api/v1/auth/me");
  },
  listAccounts() {
    return httpClient.get("/api/v1/accounts");
  },
  listRoles() {
    return httpClient.get("/api/v1/roles");
  },
  createAccount(payload) {
    return httpClient.post("/api/v1/accounts", payload);
  },
  getAccount(accountId) {
    return httpClient.get(`/api/v1/accounts/${accountId}`);
  },
  updateAccount(accountId, payload) {
    return httpClient.patch(`/api/v1/accounts/${accountId}`, payload);
  },
  updateAccountStatus(accountId, isActive) {
    return httpClient.patch(`/api/v1/accounts/${accountId}/status`, {
      is_active: isActive,
    });
  },
  updateAccountRole(accountId, roleId) {
    return httpClient.put(`/api/v1/accounts/${accountId}/role`, {
      role_id: roleId,
    });
  },
};
