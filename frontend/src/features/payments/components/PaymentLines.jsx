import { useMemo } from "react";

import { usePaymentServiceCatalog } from "../hooks/usePaymentServiceCatalog.js";

const formatVnd = (value) => `${new Intl.NumberFormat("vi-VN", { maximumFractionDigits: 0 }).format(Number(value))} ₫`;
const fallbackServiceUnits = { DV001: "Container", DV002: "Container", DV003: "Ngày", DV004: "Chuyến", DV005: "Lô hàng", DV006: "Lần" };

export function PaymentLines({ lines, editable = false, values = {}, onChange, onRemove }) {
  const catalog = usePaymentServiceCatalog();
  const units = useMemo(
    () => new Map((catalog.data ?? []).map((service) => [String(service.id), service.unit])),
    [catalog.data],
  );

  return <div className="pay-table-scroll"><table className="pay-table pay-lines"><thead><tr><th>Tên hạng mục / Dịch vụ</th><th>Đơn vị tính</th><th>Sản lượng xác nhận</th><th>Sản lượng thanh toán</th><th>Đơn giá (VNĐ)</th><th>Thuế (%)</th><th>Thành tiền (VNĐ)</th>{onRemove ? <th>Thao tác</th> : null}</tr></thead><tbody>{lines.map((line) => <tr key={line.service_id}><td><strong>{line.description}</strong></td><td>{line.service_unit ?? line.unit ?? units.get(String(line.service_id)) ?? fallbackServiceUnits[line.service_id] ?? (catalog.isPending ? "Đang tải..." : "—")}</td><td>{Number(line.confirmed_quantity).toLocaleString("vi-VN")}</td><td>{editable ? <input className="pay-qty" type="number" min="0.0001" max={line.confirmed_quantity} step="any" value={values[line.service_id] ?? line.billing_quantity} onChange={(event) => onChange(line.service_id, event.target.value)} /> : Number(line.billing_quantity).toLocaleString("vi-VN")}</td><td>{new Intl.NumberFormat("vi-VN").format(Number(line.unit_price_snapshot))}</td><td>{Number(line.tax_rate) * 100}%</td><td><strong className="pay-money">{formatVnd(line.line_amount)}</strong></td>{onRemove ? <td><button className="pay-text-action" type="button" disabled={lines.length === 1} onClick={() => onRemove(line.service_id)}>Xóa</button></td> : null}</tr>)}</tbody></table></div>;
}
