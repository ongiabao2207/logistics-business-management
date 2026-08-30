import { useQuery } from "@tanstack/react-query";

import { notificationApi } from "../api/notificationApi";

export function useNotifications(params) {
  return useQuery({
    queryKey: ["notifications", params],
    queryFn: () => notificationApi.listNotifications(params),
    enabled: false,
  });
}
