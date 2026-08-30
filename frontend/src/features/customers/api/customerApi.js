import { httpClient } from "../../../services/httpClient";

export const customerApi = {
  listCustomers(params) {
    return httpClient.get("/customers", { params });
  },
  getCustomer(customerId) {
    return httpClient.get(`/customers/${customerId}`);
  },
};
