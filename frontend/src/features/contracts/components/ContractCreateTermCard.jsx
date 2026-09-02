import { CalendarDays } from "lucide-react";

import { formatDateInput } from "./contractFormUtils";

export function ContractCreateTermCard({ validFrom, validTo, paymentTerms, onChange }) {
  return (
    <section className="contract-create-card">
      <h2>
        <CalendarDays size={20} />
        Thời hạn Hợp đồng
      </h2>
      <div className="contract-create-date-grid">
        <label>
          <span>Ngày hiệu lực *</span>
          <input
            inputMode="numeric"
            maxLength={10}
            placeholder="dd/mm/yyyy"
            value={validFrom}
            onChange={(event) => onChange({ validFrom: formatDateInput(event.target.value) })}
          />
        </label>
        <label>
          <span>Ngày hết hạn *</span>
          <input
            inputMode="numeric"
            maxLength={10}
            placeholder="dd/mm/yyyy"
            value={validTo}
            onChange={(event) => onChange({ validTo: formatDateInput(event.target.value) })}
          />
        </label>
      </div>
      <label>
        <span>Điều khoản thanh toán *</span>
        <input
          value={paymentTerms}
          onChange={(event) => onChange({ paymentTerms: event.target.value })}
          placeholder="Ví dụ: Thanh toán trong vòng 15 ngày"
        />
      </label>
      <p className="contract-create-hint">Hệ thống sẽ gửi cảnh báo trước 30 ngày kể từ ngày hết hạn.</p>
    </section>
  );
}
