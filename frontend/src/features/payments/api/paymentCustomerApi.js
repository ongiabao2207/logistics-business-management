import { httpClient } from "../../../services/httpClient.js";

export const paymentCustomerApi = {
  listCustomers() {
    return httpClient.get("/api/v1/customers", {
      params: { offset: 0, limit: 500 },
    });
  },
};
