import { useQuery } from "@tanstack/react-query";

import { priceApi } from "../../prices/api/priceApi";

export function useContractServiceCatalog() {
  return useQuery({
    queryKey: ["contracts", "service-catalog"],
    queryFn: () => priceApi.listServices({ limit: 500 }),
  });
}

export function useEffectiveServicePrice(serviceId) {
  return useQuery({
    queryKey: ["contracts", "effective-service-price", serviceId],
    queryFn: () => priceApi.getEffectiveServicePrice(serviceId),
    enabled: Boolean(serviceId),
    retry: false,
  });
}
