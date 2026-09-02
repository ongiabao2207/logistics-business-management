import { StatusBadge } from "../../../shared/components/StatusBadge.jsx";

import {
  formatContractCurrency,
  formatContractDate,
  getStatusMeta,
} from "./contractDisplay";

export function ContractTable({ contracts, onSelectContract }) {
  return (
    <section className="table-panel contract-table-panel">
      <table className="record-table contract-table">
        <thead>
          <tr>
            <th>Mã HĐ</th>
            <th>Tên khách hàng</th>
            <th>Ngày hiệu lực</th>
            <th>Ngày hết hạn</th>
            <th>Giá trị (VND)</th>
            <th>Trạng thái</th>
          </tr>
        </thead>
        <tbody>
          {contracts.map((contract) => {
            const status = getStatusMeta(contract.status);

            return (
              <tr
                key={contract.contract_id}
                tabIndex={0}
                role="button"
                onClick={() => onSelectContract(contract.contract_id)}
                onKeyDown={(event) => {
                  if (event.key === "Enter" || event.key === " ") {
                    event.preventDefault();
                    onSelectContract(contract.contract_id);
                  }
                }}
              >
                <td>
                  <strong className="contract-number">{contract.contract_id}</strong>
                </td>
                <td>
                  <strong>{contract.customer_name}</strong>
                </td>
                <td>{formatContractDate(contract.valid_from)}</td>
                <td>{formatContractDate(contract.valid_to)}</td>
                <td>
                  <strong>{formatContractCurrency(contract.total_value)}</strong>
                </td>
                <td>
                  <StatusBadge tone={status.tone}>{status.label}</StatusBadge>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </section>
  );
}
