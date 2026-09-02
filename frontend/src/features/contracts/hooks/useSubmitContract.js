import { useMutation, useQueryClient } from "@tanstack/react-query";

import { contractApi } from "../api/contractApi";

export function useSubmitContract() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: contractApi.submitContract,
    onSuccess: (_response, contractId) => {
      queryClient.invalidateQueries({ queryKey: ["contracts"] });
      queryClient.invalidateQueries({ queryKey: ["contracts", contractId] });
    },
  });
}
