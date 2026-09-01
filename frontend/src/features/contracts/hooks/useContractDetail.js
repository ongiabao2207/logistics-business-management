import { useQuery } from "@tanstack/react-query";

import { contractApi } from "../api/contractApi";

export function useContractDetail(contractId) {
  return useQuery({
    queryKey: ["contracts", contractId],
    queryFn: () => contractApi.getContract(contractId),
    enabled: Boolean(contractId),
  });
}
