import { httpClient } from "../../../services/httpClient";

export const productionApi = {
  checkOverlap(payload) {
    return httpClient.post("/api/v1/production-periods/check-overlap", payload);
  },
  createDraft(payload, actorId) {
    return httpClient.post("/api/v1/production-periods/draft", payload, {
      headers: { "X-User-Id": actorId },
    });
  },
  listProductionPeriods(params) {
    return httpClient.get("/api/v1/production-periods", { params });
  },
  getProductionPeriod(periodId) {
    return httpClient.get(`/api/v1/production-periods/${periodId}`);
  },
  replaceProductionDetails(periodId, payload) {
    return httpClient.put(`/api/v1/production-periods/${periodId}/details`, payload);
  },
  lockProductionPeriod(periodId, actorId) {
    return httpClient.post(
      `/api/v1/production-periods/${periodId}/lock`,
      {},
      { headers: { "X-User-Id": actorId } },
    );
  },
  reviewProductionPeriod(periodId, decision) {
    return httpClient.post(`/api/v1/production-periods/${periodId}/review`, { decision });
  },
};
