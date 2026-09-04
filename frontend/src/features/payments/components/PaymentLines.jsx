import { useMemo } from "react";

import { usePaymentServiceCatalog } from "../hooks/usePaymentServiceCatalog.js";

const formatVnd = (value) => `${new Intl.NumberFormat("vi-VN", { maximumFractionDigits: 0 }).format(Number(value))} ₫`;
const fallbackServiceUnits = { DV001: "Container", DV002: "Container", DV003: "Ngày", DV004: "Chuyến", DV005: "Lô hàng", DV006: "Lần" };

export function PaymentLines({ lines }) {
  const catalog = usePaymentServiceCatalog();
  const units = useMemo(
    () => new Map((catalog.data ?? []).map((service) => [String(service.id), service.unit])),
    [catalog.data],
  );

  return <div className="pay-table-scroll"><table className="pay-table pay-lines"><thead><tr><th>Tên hạng mục / Dịch vụ</th><th>Đơn vị tính</th><th>Sản lượng xác nhận</th><th>Đơn giá (VNĐ)</th><th>Thuế (%)</th><th>Thành tiền (VNĐ)</th></tr></thead><tbody>{lines.map((line) => <tr key={line.service_id}><td><strong>{line.description}</strong></td><td>{line.service_unit ?? line.unit ?? units.get(String(line.service_id)) ?? fallbackServiceUnits[line.service_id] ?? (catalog.isPending ? "Đang tải..." : "—")}</td><td>{Number(line.confirmed_quantity).toLocaleString("vi-VN")}</td><td>{new Intl.NumberFormat("vi-VN").format(Number(line.unit_price_snapshot))}</td><td>{Number(line.tax_rate) * 100}%</td><td><strong className="pay-money">{formatVnd(line.line_amount)}</strong></td></tr>)}</tbody></table></div>;
}
