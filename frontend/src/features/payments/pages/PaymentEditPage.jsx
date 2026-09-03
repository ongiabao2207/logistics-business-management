import { ArrowLeft, Info, Save, Send } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";

import { PaymentBreadcrumb } from "../components/PaymentBreadcrumb.jsx";
import { PaymentLines } from "../components/PaymentLines.jsx";
import { PaymentState } from "../components/PaymentState.jsx";
import { PaymentStatus } from "../components/PaymentStatus.jsx";
import { PaymentTotals } from "../components/PaymentTotals.jsx";
import { usePaymentContracts } from "../hooks/usePaymentContracts.js";
import { useCreateAdjustment, usePayment, useUpdatePayment } from "../hooks/usePayments.js";

function recalculateTax(payment, taxPercent) {
  const taxRate = Number(taxPercent) / 100;
  const lines = payment.lines.map((line) => {
    const confirmedQuantity = Number(line.confirmed_quantity);
    const lineAmount = confirmedQuantity * Number(line.unit_price_snapshot);
    return {
      ...line,
      billing_quantity: confirmedQuantity,
      line_amount: lineAmount,
      tax_rate: taxRate,
      tax_amount: lineAmount * taxRate,
    };
  });
  const subtotal = lines.reduce((sum, line) => sum + line.line_amount, 0);
  const taxAmount = lines.reduce((sum, line) => sum + line.tax_amount, 0);
  return { ...payment, lines, subtotal, tax_amount: taxAmount, total_amount: subtotal + taxAmount };
}

const historyLabels = {
  DRAFT_EDIT: "Chỉnh sửa bản nháp",
  REVISION_ADJUSTMENT: "Điều chỉnh theo yêu cầu duyệt",
};

function formatTaxRate(value) {
  if (value === null || value === undefined) return "—";
  return `${Number(value) * 100}%`;
}

function groupAdjustmentHistory(adjustments = []) {
  const groups = new Map();
  adjustments.forEach((item) => {
    const key = `${item.change_type}|${item.adjustment_note}|${item.created_at}|${item.previous_tax_rate}|${item.new_tax_rate}`;
    if (!groups.has(key)) groups.set(key, item);
  });
  return [...groups.values()].sort((left, right) => new Date(right.created_at) - new Date(left.created_at));
}

function AdjustmentHistory({ adjustments }) {
  const items = groupAdjustmentHistory(adjustments);
  if (!items.length) {
    return <div className="history-entry"><strong>Khởi tạo bản nháp</strong><p>Chưa có lần điều chỉnh thuế suất nào.</p></div>;
  }
  return items.map((item) => <div className="history-entry" key={`${item.id}-${item.created_at}`}>
    <div className="history-entry-heading">
      <strong>{historyLabels[item.change_type] ?? "Điều chỉnh bảng thanh toán"}</strong>
      <time>{new Date(item.created_at).toLocaleString("vi-VN")}</time>
    </div>
    <p className="history-tax-change">Thuế suất: <b>{formatTaxRate(item.previous_tax_rate)}</b><span>→</span><b>{formatTaxRate(item.new_tax_rate)}</b></p>
    <p>{item.adjustment_note}</p>
  </div>);
}

export function PaymentEditPage({ adjustment = false }) {
  const { paymentId } = useParams();
  const navigate = useNavigate();
  const { data: payment, isPending, error } = usePayment(paymentId);
  const update = useUpdatePayment();
  const adjust = useCreateAdjustment();
  const [taxPercent, setTaxPercent] = useState("");
  const [reason, setReason] = useState("");
  const [revisionId] = useState(() => `mock-revision-${paymentId}`);
  const { getCustomerName } = usePaymentContracts();

  useEffect(() => {
    if (payment) setTaxPercent(String(Number(payment.lines[0]?.tax_rate ?? 0.1) * 100));
  }, [payment]);

  const displayedPayment = useMemo(
    () => payment ? recalculateTax(payment, taxPercent) : null,
    [payment, taxPercent],
  );

  if (isPending) return <PaymentState title="Đang tải dữ liệu..." />;
  if (error) return <PaymentState title="Không thể tải dữ liệu" description={error.message} />;

  const hasAppliedRevision = (payment.adjustments ?? []).some((item) => item.change_type === "REVISION_ADJUSTMENT");
  if (adjustment && hasAppliedRevision) {
    return <PaymentState title="Đã gửi phê duyệt lại" description="Yêu cầu điều chỉnh này đã được xử lý và đang chờ người duyệt." />;
  }

  const editableStatuses = adjustment ? ["REVISION_REQUESTED", "REJECTED"] : ["DRAFT"];
  if (!editableStatuses.includes(payment.status)) {
    return <PaymentState title="Không thể chỉnh sửa" description={`Bảng đang ở trạng thái ${payment.status}.`} />;
  }

  const customerName = getCustomerName(payment.contract_id, payment.customer_id);
  const mutation = adjustment ? adjust : update;

  function save(event) {
    event.preventDefault();
    const taxRate = Number(taxPercent) / 100;
    const payload = adjustment
      ? { revision_request_id: revisionId, adjustment_note: reason, tax_rate: taxRate }
      : { reason, tax_rate: taxRate };
    mutation.mutate(
      { id: paymentId, payload },
      { onSuccess: () => navigate(adjustment ? `/payments/${paymentId}/approval` : `/payments/${paymentId}`) },
    );
  }

  const taxField = <label>Thuế suất (%)<input required type="number" min="0" max="100" step="0.01" value={taxPercent} onChange={(event) => setTaxPercent(event.target.value)} /></label>;
  const editFields = <section className="pay-panel revision-edit-panel">
    {taxField}
    <label>Ghi chú điều chỉnh<textarea required minLength="3" value={reason} onChange={(event) => setReason(event.target.value)} placeholder="Nhập lý do điều chỉnh thuế suất..." /></label>
  </section>;
  const commonInfo = <section className="pay-panel common-info compact-common-info">
    <h3>ⓘ Thông tin chung</h3>
    <div>
      <label>Mã bảng thanh toán<input value={payment.id} readOnly /></label>
      <label>Đối tác<input value={customerName} readOnly /></label>
      <label>Kỳ thanh toán<input value={`${payment.period_start} – ${payment.period_end}`} readOnly /></label>
      <label>Hợp đồng tham chiếu<input value={payment.contract_id} readOnly /></label>
    </div>
  </section>;

  if (adjustment) {
    return <form onSubmit={save}>
      <Link className="pay-back" to={`/payments/${paymentId}`}><ArrowLeft size={16} />Quay lại danh sách</Link>
      <div className="revision-heading"><div><h2>Điều chỉnh bảng thanh toán - {payment.id}</h2></div><PaymentStatus status={payment.status} /></div>
      <section className="revision-request"><Info /><div><strong>Yêu cầu chỉnh sửa từ người duyệt</strong><div className="request-meta"><p><small>Người yêu cầu</small>Nguyễn Văn B (Nhân viên Pháp chế)</p><p><small>Thời gian</small>Đang cập nhật</p><p><small>Lý do</small>Thuế suất chưa chính xác</p></div><p className="request-detail"><small>Nội dung chi tiết</small>Kiểm tra và cập nhật lại thuế suất áp dụng cho bảng thanh toán.</p></div></section>
      <div className="payment-edit-layout">
        {editFields}
        {commonInfo}
        <section className="pay-panel revision-lines"><h3>▣ Chi tiết bảng thanh toán</h3><PaymentLines lines={displayedPayment.lines} /></section>
        <div className="edit-lower-grid">
          <section className="pay-panel revision-total"><h3>▤ Tổng hợp thanh toán</h3><PaymentTotals payment={displayedPayment} /></section>
          <section className="pay-panel revision-history"><h3>◴ Lịch sử điều chỉnh</h3><AdjustmentHistory adjustments={payment.adjustments} /></section>
        </div>
      </div>
      {mutation.error ? <div className="pay-alert error">{mutation.error.message}</div> : null}
      <div className="pay-bottom-bar"><span>◉ Điều chỉnh được lưu vào lịch sử trước khi gửi lại phê duyệt</span><div><Link className="pay-button outline" to={`/payments/${paymentId}`}>Hủy</Link><button className="pay-button primary"><Send size={16} />Lưu và gửi phê duyệt lại</button></div></div>
    </form>;
  }

  return <form onSubmit={save}>
    <PaymentBreadcrumb items={[{ label: payment.id, to: `/payments/${payment.id}` }, { label: "Điều chỉnh" }]} />
    <div className="pay-page-heading"><h1>Điều chỉnh bảng thanh toán</h1><PaymentStatus status={payment.status} /></div>
    <div className="pay-info-banner"><Info size={18} />Sản lượng đã được Production xác nhận và không thể chỉnh sửa. Kế toán chỉ được thay đổi thuế suất.</div>
    <div className="payment-edit-layout">
      {editFields}
      {commonInfo}
      <section className="pay-panel draft-lines"><h3>▣ Chi tiết bảng thanh toán</h3><PaymentLines lines={displayedPayment.lines} /></section>
      <div className="edit-lower-grid">
        <section className="pay-panel draft-summary"><h3>▣ Tổng hợp thanh toán</h3><PaymentTotals payment={displayedPayment} /></section>
        <section className="pay-panel draft-history"><h3>◴ Lịch sử điều chỉnh</h3><AdjustmentHistory adjustments={payment.adjustments} /></section>
      </div>
    </div>
    {mutation.error ? <div className="pay-alert error">{mutation.error.message}</div> : null}
    <div className="pay-bottom-bar"><span>Sản lượng được lấy cố định từ Production Service</span><div><Link className="pay-button outline" to={`/payments/${paymentId}`}>Hủy</Link><button className="pay-button primary"><Save size={16} />Lưu thay đổi</button></div></div>
  </form>;
}
