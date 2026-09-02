import { Navigate, useParams } from "react-router-dom";
import { PaymentState } from "../components/PaymentState.jsx";
import { usePayment } from "../hooks/usePayments.js";

export function PaymentDetailPage() {
  const { paymentId } = useParams();
  const { data: payment, isPending, error } = usePayment(paymentId);

  if (isPending) return <PaymentState title="Đang tải dữ liệu..." />;
  if (error) return <PaymentState title="Không thể tải bảng" description={error.message} />;

  return <Navigate to={`/payments/${payment.id}/approval`} replace />;
}
