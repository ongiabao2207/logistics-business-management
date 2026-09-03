import { useMutation, useQueryClient } from "@tanstack/react-query";

import { setAuthToken } from "../../../services/authToken";
import { identityApi } from "../api/identityApi";

export function useLogin() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: identityApi.login,
    onSuccess: (response) => {
      setAuthToken(response.access_token);
      queryClient.invalidateQueries({ queryKey: ["identity", "current-user"] });
      queryClient.invalidateQueries({ queryKey: ["contracts"] });
    },
  });
}
