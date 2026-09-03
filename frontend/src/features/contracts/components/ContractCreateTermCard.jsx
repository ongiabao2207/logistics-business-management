import { useRef } from "react";
import { CalendarDays } from "lucide-react";

import {
  formatDateInput,
  formatIsoDateToDisplay,
  parseDisplayDateToIso,
} from "./contractFormUtils";

function ContractDateField({ label, value, onChange }) {
  const dateInputRef = useRef(null);
  const isoValue = parseDisplayDateToIso(value) ?? "";

  function openPicker() {
    const picker = dateInputRef.current;

    if (!picker) {
      return;
    }

    if (picker.showPicker) {
      picker.showPicker();
      return;
    }

    picker.focus();
    picker.click();
  }

  return (
    <label className="contract-create-date-field">
      <span>{label}</span>
      <div className="contract-create-date-control">
        <input
          inputMode="numeric"
          maxLength={10}
          placeholder="dd/mm/yyyy"
          value={value}
          onChange={(event) => onChange(formatDateInput(event.target.value))}
        />
        <button type="button" aria-label={`Chọn ${label.toLowerCase()}`} onClick={openPicker}>
          <CalendarDays size={16} />
        </button>
        <input
          ref={dateInputRef}
          className="contract-native-date-input"
          type="date"
          tabIndex={-1}
          value={isoValue}
          onChange={(event) => onChange(formatIsoDateToDisplay(event.target.value))}
        />
      </div>
    </label>
  );
}

export function ContractCreateTermCard({ validFrom, validTo, paymentTerms, onChange }) {
  return (
    <section className="contract-create-card">
      <h2>
        <CalendarDays size={20} />
        Thời hạn Hợp đồng
      </h2>
      <div className="contract-create-date-grid">
        <ContractDateField
          label="Ngày hiệu lực *"
          value={validFrom}
          onChange={(nextValue) => onChange({ validFrom: nextValue })}
        />
        <ContractDateField
          label="Ngày hết hạn *"
          value={validTo}
          onChange={(nextValue) => onChange({ validTo: nextValue })}
        />
      </div>
      <label>
        <span>Điều khoản thanh toán *</span>
        <input
          value={paymentTerms}
          onChange={(event) => onChange({ paymentTerms: event.target.value })}
          placeholder="Ví dụ: Thanh toán trong vòng 15 ngày"
        />
      </label>
      <p className="contract-create-hint">
        Hệ thống sẽ gửi cảnh báo trước 30 ngày kể từ ngày hết hạn.
      </p>
    </section>
  );
}
