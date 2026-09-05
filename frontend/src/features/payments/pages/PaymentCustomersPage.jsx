import { Navigate } from "react-router-dom";

// Kỳ Production đã chứa customer_id và contract_id, vì vậy không cần chọn lại
// khách hàng bằng màn hình tháng cũ.
export function PaymentCustomersPage() {
  return <Navigate to="/payments/create" replace />;
}
