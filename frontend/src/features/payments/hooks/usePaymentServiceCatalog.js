import { useQuery } from "@tanstack/react-query";

import { priceApi } from "../../prices/api/priceApi.js";

export function usePaymentServiceCatalog() {
  return useQuery({
    queryKey: ["payments", "price-services"],
    queryFn: () => priceApi.listServices({ offset: 0, limit: 500 }),
    staleTime: 5 * 60 * 1000,
  });
}
