import { useQuery } from "@tanstack/react-query";

import { priceApi } from "../api/priceApi";

export function usePriceLists(params) {
  return useQuery({
    queryKey: ["prices", "price-lists", params],
    queryFn: () => priceApi.listPriceLists(params),
    enabled: true,
  });
}
