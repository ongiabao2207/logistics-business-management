import { httpClient } from "../../../services/httpClient";

export const contractApi = {
  listContracts() {
    return httpClient.get("/contracts");
  },
  getContract(contractId) {
    return httpClient.get(`/contracts/${contractId}`);
  },
  createContract(payload, idempotencyKey) {
    return httpClient.post("/contracts", payload, {
      headers: { "Idempotency-Key": idempotencyKey },
    });
  },
  updateContract(contractId, payload) {
    return httpClient.patch(`/contracts/${contractId}`, payload);
  },
  updateContractStatus(contractId, payload) {
    return httpClient.patch(`/contracts/${contractId}/status`, payload);
  },
};
