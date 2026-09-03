import { useMutation, useQueryClient } from "@tanstack/react-query";

import { contractApi } from "../api/contractApi";

export function useUpdateContract(contractId) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (payload) => contractApi.updateContract(contractId, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["contracts"] });
      queryClient.invalidateQueries({ queryKey: ["contracts", contractId] });
    },
  });
}
