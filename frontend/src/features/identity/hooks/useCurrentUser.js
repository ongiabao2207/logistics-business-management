import { useQuery } from "@tanstack/react-query";

import { identityApi } from "../api/identityApi";

export function useCurrentUser() {
  return useQuery({
    queryKey: ["identity", "current-user"],
    queryFn: identityApi.getCurrentUser,
    enabled: false,
  });
}
