import { ChevronRight } from "lucide-react";
import { Link } from "react-router-dom";

export function PaymentBreadcrumb({ items = [] }) {
  return (
    <div className="pay-breadcrumb">
      <Link to="/payments">Bảng thanh toán</Link>

      {items.map((item) => (
        <span key={item.label}>
          <ChevronRight size={13} />

          {item.to ? (
            <Link to={item.to}>{item.label}</Link>
          ) : (
            <strong>{item.label}</strong>
          )}
        </span>
      ))}
    </div>
  );
}