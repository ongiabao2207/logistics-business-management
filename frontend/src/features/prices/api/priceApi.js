import { httpClient } from "../../../services/httpClient";

export const priceApi = {
  listServices(params) {
    return httpClient.get("/api/v1/services", { params });
  },
  createService(payload) {
    return httpClient.post("/api/v1/services", payload);
  },
  deactivateService(serviceId) {
    return httpClient.delete(`/api/v1/services/${serviceId}`);
  },
  listPriceLists(params) {
    return httpClient.get("/api/v1/price-lists", { params });
  },
  getPriceList(priceListId) {
    return httpClient.get(`/api/v1/price-lists/${priceListId}`);
  },
  getEffectiveServicePrice(serviceId) {
    return httpClient.get(`/api/v1/price-lists/effective/services/${serviceId}`);
  },
  createPriceList(payload) {
    return httpClient.post("/api/v1/price-lists", payload);
  },
  updatePriceList(priceListId, payload) {
    return httpClient.patch(`/api/v1/price-lists/${priceListId}`, payload);
  },
  deletePriceList(priceListId) {
    return httpClient.delete(`/api/v1/price-lists/${priceListId}`);
  },
  submitPriceList(priceListId) {
    return httpClient.post(`/api/v1/price-lists/${priceListId}/submit`);
  },
  approvePriceList(priceListId) {
    return httpClient.post(`/api/v1/price-lists/${priceListId}/approve`);
  },
  rejectPriceList(priceListId) {
    return httpClient.post(`/api/v1/price-lists/${priceListId}/reject`);
  },
};
