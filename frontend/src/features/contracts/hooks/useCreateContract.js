import { useMutation, useQueryClient } from "@tanstack/react-query";

import { contractApi } from "../api/contractApi";

function createIdempotencyKey() {
  if (window.crypto?.randomUUID) {
    return window.crypto.randomUUID();
  }

  return `contract-create-${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

export function useCreateContract() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (payload) => contractApi.createContract(payload, createIdempotencyKey()),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["contracts"] });
    },
  });
}
