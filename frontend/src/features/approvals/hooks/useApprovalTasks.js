import { useQuery } from "@tanstack/react-query";

import { approvalApi } from "../api/approvalApi";

export function useApprovalTasks(params) {
  return useQuery({
    queryKey: ["approvals", "tasks", params],
    queryFn: () => approvalApi.listAssignedTasks(params),
    enabled: false,
  });
}
