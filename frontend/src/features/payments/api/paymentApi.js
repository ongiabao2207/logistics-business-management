import { httpClient } from "../../../services/httpClient";

export const paymentApi = {
  previewPayment(payload) {
    return httpClient.post("/api/v1/payments/preview", payload);
  },
  createPayment(payload) {
    return httpClient.post("/api/v1/payments", payload);
  },
  listPayments(params) {
    return httpClient.get("/api/v1/payments", { params });
  },
  getPayment(paymentId) {
    return httpClient.get(`/api/v1/payments/${paymentId}`);
  },
  updatePayment(paymentId, payload) {
    return httpClient.patch(`/api/v1/payments/${paymentId}`, payload);
  },
  submitPayment(paymentId) {
    return httpClient.post(`/api/v1/payments/${paymentId}/submit`);
  },
  createAdjustment(paymentId, payload) {
    return httpClient.post(`/api/v1/payments/${paymentId}/adjustments`, payload);
  },
};
