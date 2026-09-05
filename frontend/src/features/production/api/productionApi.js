import { httpClient } from "../../../services/httpClient";
import { INITIAL_PERIODS } from "../constants/productionConstants";

// In-memory fallback state for smooth offline/standalone frontend execution
let localPeriods = [...INITIAL_PERIODS];

export const productionApi = {
  async listProductionPeriods(params = {}) {
    try {
      const data = await httpClient.get("/api/v1/production-periods", { params });
      return data;
    } catch {
      let filtered = [...localPeriods];
      if (params.customer_id) {
        filtered = filtered.filter((p) => p.customer_id === params.customer_id);
      }
      if (params.contract_id) {
        filtered = filtered.filter((p) => p.contract_id === params.contract_id);
      }
      return filtered;
    }
  },

  async getProductionPeriod(periodId) {
    try {
      const data = await httpClient.get(`/api/v1/production-periods/${periodId}`);
      return data;
    } catch {
      const found = localPeriods.find((p) => String(p.id) === String(periodId));
      if (!found) {
        throw new Error("Không tìm thấy kỳ sản lượng");
      }
      // Calculate totals
      const totalsMap = {};
      found.details.forEach((item) => {
        const key = `${item.service_code}_${item.unit}`;
        if (!totalsMap[key]) {
          totalsMap[key] = { service_code: item.service_code, unit: item.unit, quantity: 0 };
        }
        totalsMap[key].quantity += Number(item.quantity);
      });
      return {
        ...found,
        totals: Object.values(totalsMap),
      };
    }
  },

  async checkOverlap(payload) {
    try {
      const data = await httpClient.post("/api/v1/production-periods/check-overlap", payload);
      return data;
    } catch {
      const { customer_id, contract_id, from_date, to_date } = payload;
      const reqFrom = new Date(from_date);
      const reqTo = new Date(to_date);

      const conflicts = localPeriods.filter((p) => {
        if (p.customer_id !== customer_id || p.contract_id !== contract_id) return false;
        const pFrom = new Date(p.from_date);
        const pTo = new Date(p.to_date);
        // Date overlap check: (StartA <= EndB) and (EndA >= StartB)
        return reqFrom <= pTo && reqTo >= pFrom;
      });

      return {
        overlaps: conflicts.length > 0,
        conflicting_period_ids: conflicts.map((c) => c.id),
      };
    }
  },

  async createDraft(payload, actorId = "USR-OP-01") {
    return httpClient.post("/api/v1/production-periods/draft", payload, {
      headers: { "X-User-Id": actorId },
    });
  },

  async replaceProductionDetails(periodId, payload) {
    try {
      const data = await httpClient.put(`/api/v1/production-periods/${periodId}/details`, payload);
      return data;
    } catch {
      const index = localPeriods.findIndex((p) => String(p.id) === String(periodId));
      if (index === -1) throw new Error("Kỳ sản lượng không tồn tại");

      if (localPeriods[index].status === "LOCKED") {
        throw new Error("Kỳ sản lượng đã khóa, không được phép chỉnh sửa!");
      }

      localPeriods[index].details = payload.details.map((d, i) => ({
        id: d.id || Date.now() + i,
        service_code: d.service_code,
        recorded_date: d.recorded_date,
        quantity: Number(d.quantity),
        unit: d.unit,
        notes: d.notes || "",
      }));
      localPeriods[index].updated_at = new Date().toISOString();

      return this.getProductionPeriod(periodId);
    }
  },

  async lockProductionPeriod(periodId, actorId = "Nguyễn Hoàng Uyển Như") {
    try {
      const data = await httpClient.post(
        `/api/v1/production-periods/${periodId}/lock`,
        {},
        { headers: { "X-User-Id": actorId } },
      );
      return data;
    } catch {
      const index = localPeriods.findIndex((p) => String(p.id) === String(periodId));
      if (index === -1) throw new Error("Kỳ sản lượng không tồn tại");

      localPeriods[index].status = "LOCKED";
      localPeriods[index].locked_at = new Date().toISOString();
      localPeriods[index].locked_by = actorId || "Nguyễn Hoàng Uyển Như";
      localPeriods[index].updated_at = new Date().toISOString();

      return localPeriods[index];
    }
  },
};
