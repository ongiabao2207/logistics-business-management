import { CalendarDays, Search } from "lucide-react";

import { CONTRACT_STATUS_OPTIONS } from "./contractDisplay";

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
        </label>

        <fieldset className="contract-filter-card contract-date-card">
          <legend>Thời gian</legend>
          <div className="contract-date-inputs">
            <label>
              <CalendarDays size={15} />
              <input
                type="date"
                value={filters.from}
                onChange={(event) => onChange({ from: event.target.value })}
                aria-label="Từ ngày"
              />
            </label>
            <label>
              <CalendarDays size={15} />
              <input
                type="date"
                value={filters.to}
                onChange={(event) => onChange({ to: event.target.value })}
                aria-label="Đến ngày"
              />
            </label>
          </div>
        </fieldset>

        <fieldset className="contract-filter-card contract-status-filter">
          <legend>Trạng thái</legend>
          <div className="contract-status-options">
            <button
              className={filters.status === "" ? "is-active" : ""}
              type="button"
              onClick={() => onChange({ status: "" })}
            >
              Tất cả
            </button>
            {CONTRACT_STATUS_OPTIONS.map((status) => (
              <button
                key={status}
                className={filters.status === status ? "is-active" : ""}
                type="button"
                onClick={() => onChange({ status })}
              >
                {status}
              </button>
            ))}
          </div>
        </fieldset>
      </div>
    </section>
  );
}
