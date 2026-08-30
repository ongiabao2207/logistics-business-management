import { useQuery } from "@tanstack/react-query";

import { productionApi } from "../api/productionApi";

export function useProductionPeriods(params) {
  return useQuery({
    queryKey: ["production", "periods", params],
    queryFn: () => productionApi.listProductionPeriods(params),
    enabled: false,
  });
}
