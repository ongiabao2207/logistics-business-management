import { httpClient } from "../../../services/httpClient";

export const approvalApi = {
  listAssignedTasks(params) {
    return httpClient.get("/approvals/tasks", { params });
  },
  getApprovalDetail(approvalId) {
    return httpClient.get(`/approvals/${approvalId}`);
  },
};
