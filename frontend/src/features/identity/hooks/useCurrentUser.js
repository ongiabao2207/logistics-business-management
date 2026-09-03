import { useQuery } from "@tanstack/react-query";

import { getAuthToken } from "../../../services/authToken";
import { identityApi } from "../api/identityApi";

export function useCurrentUser() {
  return useQuery({
    queryKey: ["identity", "current-user"],
    queryFn: identityApi.getCurrentUser,
    enabled: Boolean(getAuthToken()),
  });
}
