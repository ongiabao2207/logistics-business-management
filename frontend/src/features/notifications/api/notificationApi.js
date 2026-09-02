import { httpClient } from "../../../services/httpClient";

export const notificationApi = {
  listNotifications(params) {
    return httpClient.get("/api/v1/notifications", { params });
  },
  markAsRead(notificationId) {
    return httpClient.patch(`/api/v1/notifications/${notificationId}/read`);
  },
};
