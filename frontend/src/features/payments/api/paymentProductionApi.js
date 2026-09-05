import { httpClient } from "../../../services/httpClient.js";

export const paymentProductionApi = {
  async listLockedPeriods() {
    const periods = await httpClient.get("/api/v1/production-periods");

    // Production đã giới hạn ROLE_ACCOUNTANT chỉ thấy kỳ LOCKED. Vẫn lọc lại
    // tại Payment UI để không bao giờ hiển thị nhầm kỳ còn ở trạng thái DRAFT.
    return periods.filter((period) => period.status === "LOCKED");
  },
};
