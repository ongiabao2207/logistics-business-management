import { useQuery } from "@tanstack/react-query";

import { customerApi } from "../api/customerApi";

export function useCustomers(params) {
  return useQuery({
    queryKey: ["customers", params],
    queryFn: () => customerApi.listCustomers(params),
    enabled: false,
  });
}
