import { useQuery } from "@tanstack/react-query";

import { paymentProductionApi } from "../api/paymentProductionApi.js";

export function usePaymentProductionPeriods() {
  return useQuery({
    queryKey: ["payments", "locked-production-periods"],
    queryFn: paymentProductionApi.listLockedPeriods,
  });
}
