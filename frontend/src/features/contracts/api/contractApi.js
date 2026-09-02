import { httpClient } from "../../../services/httpClient";

export const contractApi = {
  listContracts() {
    return httpClient.get("/api/v1/contracts");
  },
  getContract(contractId) {
    return httpClient.get(`/api/v1/contracts/${contractId}`);
  },
  createContract(payload, idempotencyKey) {
    return httpClient.post("/api/v1/contracts", payload, {
      headers: { "Idempotency-Key": idempotencyKey },
    });
  },
  updateContract(contractId, payload) {
    return httpClient.patch(`/api/v1/contracts/${contractId}`, payload);
  },
  updateContractStatus(contractId, payload) {
    return httpClient.patch(`/api/v1/contracts/${contractId}/status`, payload);
  },
  submitContract(contractId) {
    return httpClient.patch(`/api/v1/contracts/${contractId}/status`, {
      status: "SUBMITTED",
    });
  },
};
