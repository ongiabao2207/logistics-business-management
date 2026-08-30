import { useQuery } from "@tanstack/react-query";

import { paymentApi } from "../api/paymentApi";

export function usePayments(params) {
  return useQuery({
    queryKey: ["payments", params],
    queryFn: () => paymentApi.listPayments(params),
    enabled: false,
  });
}
