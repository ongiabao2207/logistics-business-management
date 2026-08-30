import { httpClient } from "../../../services/httpClient";

export const paymentApi = {
  previewPayment(payload) {
    return httpClient.post("/payments/preview", payload);
  },
  createPayment(payload) {
    return httpClient.post("/payments", payload);
  },
  listPayments(params) {
    return httpClient.get("/payments", { params });
  },
  getPayment(paymentId) {
    return httpClient.get(`/payments/${paymentId}`);
  },
  updatePayment(paymentId, payload) {
    return httpClient.patch(`/payments/${paymentId}`, payload);
  },
  submitPayment(paymentId) {
    return httpClient.post(`/payments/${paymentId}/submit`);
  },
  createAdjustment(paymentId, payload) {
    return httpClient.post(`/payments/${paymentId}/adjustments`, payload);
  },
};
