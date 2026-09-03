import { Plus, Trash2 } from "lucide-react";

import {
  formatContractCurrency,
  getContractLineTotal,
} from "./contractDisplay";

export function ContractServiceLinesTable({ lines, onAddService, onRemoveService }) {
  return (
    <section className="contract-service-lines">
      <header>
        <h2>Chi tiết Dịch vụ & Đơn giá</h2>
        <button className="button" type="button" onClick={onAddService}>
          <Plus size={16} />
          Thêm dịch vụ
        </button>
      </header>
      <div className="contract-service-lines-table">
        <table>
          <thead>
            <tr>
              <th>STT</th>
              <th>Loại dịch vụ</th>
              <th>Đơn vị tính</th>
              <th>Số lượng</th>
              <th>Đơn giá (VND)</th>
              <th>Thành tiền</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {lines.length === 0 ? (
              <tr>
                <td colSpan={7} className="contract-empty-line">
                  Chưa có dịch vụ nào trong hợp đồng.
                </td>
              </tr>
            ) : null}
            {lines.map((line, index) => (
              <tr key={line.service_id ?? line.service_name}>
                <td>{String(index + 1).padStart(2, "0")}</td>
                <td>
                  <strong>{line.service_name}</strong>
                </td>
                <td>{line.service_unit}</td>
                <td>{line.quantity}</td>
                <td>
                  <strong>{formatContractCurrency(line.service_price)}</strong>
                </td>
                <td>
                  <strong>{formatContractCurrency(getContractLineTotal(line))}</strong>
                </td>
                <td>
                  <button
                    className="contract-line-remove"
                    type="button"
                    aria-label="Xóa dịch vụ"
                    onClick={() => onRemoveService(line.service_id)}
                  >
                    <Trash2 size={18} />
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
