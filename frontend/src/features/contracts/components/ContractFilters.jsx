import { useRef } from "react";
import { CalendarDays, Search } from "lucide-react";

import { CONTRACT_STATUS_OPTIONS } from "./contractDisplay";
import {
  formatDateInput,
  formatIsoDateToDisplay,
  parseDisplayDateToIso,
} from "./contractFormUtils";

function DatePickerInput({ value, onChange, ariaLabel }) {
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
    <label className="contract-date-picker-field">
      <CalendarDays size={15} />
      <input
        type="text"
        inputMode="numeric"
        value={value}
        onChange={(event) => onChange(formatDateInput(event.target.value))}
        placeholder="dd/mm/yyyy"
        maxLength={10}
        aria-label={ariaLabel}
      />
      <button type="button" aria-label={`Chọn ${ariaLabel.toLowerCase()}`} onClick={openPicker}>
        <CalendarDays size={15} />
      </button>
      <input
        ref={dateInputRef}
        className="contract-native-date-input"
        type="date"
        tabIndex={-1}
        value={isoValue}
        onChange={(event) => onChange(formatIsoDateToDisplay(event.target.value))}
      />
    </label>
  );
}

export function ContractFilters({ customers, filters, onChange }) {
  return (
    <section className="contract-filter-area" aria-label="Contract filters">
      <label className="contract-search">
        <Search size={18} />
        <input
          type="search"
          value={filters.search}
          placeholder="Tìm kiếm hợp đồng, khách hàng..."
          onChange={(event) => onChange({ search: event.target.value })}
        />
      </label>

      <div className="contract-filter-grid">
        <label className="contract-filter-card">
          <span>Khách hàng</span>
          <span className="contract-select-wrap">
            <select
              value={filters.customer}
              onChange={(event) => onChange({ customer: event.target.value })}
            >
              <option value="">Tất cả khách hàng</option>
              {customers.map((customer) => (
                <option key={customer} value={customer}>
                  {customer}
                </option>
              ))}
            </select>
          </span>
        </label>

        <div className="contract-filter-card contract-date-card" role="group" aria-label="Thời gian">
          <span>Thời gian</span>
          <div className="contract-date-inputs">
            <DatePickerInput
              value={filters.from}
              ariaLabel="Từ ngày"
              onChange={(from) => onChange({ from })}
            />
            <DatePickerInput
              value={filters.to}
              ariaLabel="Đến ngày"
              onChange={(to) => onChange({ to })}
            />
          </div>
        </div>

        <div className="contract-filter-card contract-status-filter" role="group" aria-label="Trạng thái">
          <span>Trạng thái</span>
          <div className="contract-status-options">
            {CONTRACT_STATUS_OPTIONS.map((status) => (
              <button
                key={status}
                className={filters.status === status ? "is-active" : ""}
                type="button"
                onClick={() =>
                  onChange({ status: filters.status === status ? "" : status })
                }
              >
                {status}
              </button>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
