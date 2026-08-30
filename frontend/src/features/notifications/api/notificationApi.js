import { httpClient } from "../../../services/httpClient";

export const notificationApi = {
  listNotifications(params) {
    return httpClient.get("/notifications", { params });
  },
  markAsRead(notificationId) {
    return httpClient.post(`/notifications/${notificationId}/read`);
  },
};
