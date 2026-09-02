import {
  AlertCircle,
  ArrowLeft,
  CheckCircle2,
  Clock3,
  FilePenLine,
  FileText,
  Pencil,
  Send,
  XCircle,
} from "lucide-react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { PaymentLines } from "../components/PaymentLines.jsx";
import { PaymentState } from "../components/PaymentState.jsx";
import { PaymentStatus } from "../components/PaymentStatus.jsx";
import { PaymentTotals } from "../components/PaymentTotals.jsx";
import { usePaymentContracts } from "../hooks/usePaymentContracts.js";
import { usePayment, useSubmitPayment } from "../hooks/usePayments.js";

const workflowByStatus = {
  DRAFT: [
    { state: "current", icon: Clock3, title: "Đang ở bản nháp", description: "Kế toán đang hoàn thiện bảng thanh toán." },
    { title: "Chờ gửi phê duyệt" },
  ],
  PENDING_APPROVAL: [
    { state: "done", icon: CheckCircle2, title: "Kế toán đã gửi", description: "Người thực hiện: Nguyễn Văn A" },
    { state: "current", icon: Clock3, title: "Chờ Pháp chế phê duyệt", description: "Đang xử lý" },
    { title: "Chờ Giám đốc phê duyệt" },
    { title: "Hoàn tất phê duyệt" },
  ],
  REVISION_REQUESTED: [
    { state: "done", icon: CheckCircle2, title: "Kế toán đã gửi", description: "Đã trình bảng thanh toán để phê duyệt." },
    { state: "revision", icon: AlertCircle, title: "Pháp chế yêu cầu chỉnh sửa", description: "Người yêu cầu: Nguyễn Văn B (Nhân viên Pháp chế)", reason: "Sản lượng thanh toán chưa thống nhất với hồ sơ đối soát." },
    { title: "Chờ kế toán gửi lại" },
  ],
  REJECTED: [
    { state: "done", icon: CheckCircle2, title: "Kế toán đã gửi", description: "Đã trình bảng thanh toán để phê duyệt." },
    { state: "rejected", icon: XCircle, title: "Bảng thanh toán bị từ chối", description: "Người xử lý: Nguyễn Văn B (Nhân viên Pháp chế)", reason: "Thông tin và sản lượng thanh toán chưa phù hợp với biên bản đối soát." },
  ],
  APPROVED: [
    { state: "done", icon: CheckCircle2, title: "Kế toán đã gửi" },
    { state: "done", icon: CheckCircle2, title: "Pháp chế đã phê duyệt" },
    { state: "done", icon: CheckCircle2, title: "Giám đốc đã phê duyệt" },
    { state: "done", icon: CheckCircle2, title: "Hoàn tất phê duyệt" },
  ],
  SIGNED: [
    { state: "done", icon: CheckCircle2, title: "Kế toán đã gửi" },
    { state: "done", icon: CheckCircle2, title: "Pháp chế đã phê duyệt" },
    { state: "done", icon: CheckCircle2, title: "Giám đốc đã phê duyệt" },
    { state: "done", icon: CheckCircle2, title: "Đã ký và hoàn tất" },
  ],
};

function ApprovalTimeline({ payment }) {
  const items = workflowByStatus[payment.status] ?? workflowByStatus.DRAFT;
  const updatedAt = payment.updated_at
    ? new Date(payment.updated_at).toLocaleString("vi-VN")
    : "Đang cập nhật";

  return (
    <aside className="pay-panel approval-timeline">
      <h3>Lịch sử &amp; tiến độ phê duyệt</h3>
      <small className="approval-updated">Cập nhật: {updatedAt}</small>
      {items.map(({ state = "waiting", icon: Icon, title, description, reason }) => (
        <div className={`timeline ${state}`} key={title}>
          {Icon ? <Icon /> : <span className="timeline-dot" />}
          <div>
            <strong>{title}</strong>
            {description ? <p>{description}</p> : null}
            {reason ? <div className="approval-reason"><b>Lý do</b>{reason}</div> : null}
          </div>
        </div>
      ))}
      <div className="approval-api-note">
        {payment.approval_instance_id ? `Mã quy trình: ${payment.approval_instance_id}. ` : ""}
        Người duyệt, thời gian và lý do đang dùng dữ liệu mẫu cho đến khi Approval Service cung cấp API lịch sử.
      </div>
    </aside>
  );
}

export function PaymentApprovalPage() {
  const { paymentId } = useParams();
  const navigate = useNavigate();
  const { data: payment, isPending, error } = usePayment(paymentId);
  const submit = useSubmitPayment();
  const { getCustomerName } = usePaymentContracts();

  if (isPending) return <PaymentState title="Đang tải chi tiết..." />;
  if (error) return <PaymentState title="Không thể tải bảng" description={error.message} />;

  const period = new Date(payment.period_start).toLocaleDateString("vi-VN", {
    month: "2-digit",
    year: "numeric",
  });
  const customerName = getCustomerName(payment.contract_id, payment.customer_id);

  return <>
    <Link className="pay-back" to="/payments"><ArrowLeft size={16} />Quay lại danh sách</Link>
    <div className="pay-page-heading approval-page-heading">
      <div>
        <h1>{payment.id}</h1>
        <p>{customerName} · {payment.contract_id} · Kỳ {period}</p>
      </div>
      <div>
        <PaymentStatus status={payment.status} />
        {payment.status === "DRAFT" ? <Link className="pay-button outline" to={`/payments/${payment.id}/edit`}><Pencil size={16} />Chỉnh sửa</Link> : null}
        {payment.status === "DRAFT" ? <button className="pay-button primary" onClick={() => submit.mutate(payment.id, { onSuccess: () => navigate(`/payments/${payment.id}/approval`) })}><Send size={16} />Gửi phê duyệt</button> : null}
        {payment.status === "REVISION_REQUESTED" ? <Link className="pay-button primary" to={`/payments/${payment.id}/adjust`}><FilePenLine size={16} />Điều chỉnh</Link> : null}
      </div>
    </div>

    <div className="approval-grid">
      <div>
        <section className="pay-panel create-detail">
          <PaymentLines lines={payment.lines} />
          <PaymentTotals payment={payment} />
        </section>
        <div className="approval-subgrid">
          <article className="pay-panel">
            <h3>Thông tin đối tác</h3>
            <p>Khách hàng<br/><strong>{customerName}</strong></p>
            <p>Số hợp đồng<br/><strong className="blue-text">{payment.contract_id}</strong></p>
          </article>
          <article className="pay-panel">
            <h3>Tài liệu đính kèm</h3>
            <p><FileText size={16} /> Biên bản kê sản lượng.pdf</p>
            <p><FileText size={16} /> Biên bản đối soát.docx</p>
          </article>
        </div>
      </div>
      <ApprovalTimeline payment={payment} />
    </div>
  </>;
}
