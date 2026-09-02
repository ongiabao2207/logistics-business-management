import { useQuery } from "@tanstack/react-query";

import { contractApi } from "../api/contractApi";

export function useContracts() {
  return useQuery({
    queryKey: ["contracts"],
    queryFn: contractApi.listContracts,
  });
}
