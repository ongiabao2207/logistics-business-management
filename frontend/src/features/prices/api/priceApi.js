import { httpClient } from "../../../services/httpClient";

export const priceApi = {
  listServices(params) {
    return httpClient.get("/api/v1/services", { params });
  },
  createService(payload) {
    return httpClient.post("/api/v1/services", payload);
  },
  listPriceLists(params) {
    return httpClient.get("/api/v1/price-lists", { params });
  },
  getPriceList(priceListId) {
    return httpClient.get(`/api/v1/price-lists/${priceListId}`);
  },
  createPriceList(payload) {
    return httpClient.post("/api/v1/price-lists", payload);
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
