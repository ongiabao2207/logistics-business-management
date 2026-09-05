import { Navigate } from "react-router-dom";

// Giữ tương thích với đường dẫn cũ; kỳ thanh toán hiện được chọn trực tiếp từ
// danh sách kỳ Production đã LOCKED tại trang /payments/create.
export function PaymentPeriodsPage() {
  return <Navigate to="/payments/create" replace />;
}
