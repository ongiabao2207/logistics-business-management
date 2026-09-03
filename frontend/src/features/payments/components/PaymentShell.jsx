import { Bell, FilePenLine, Files, WalletCards } from "lucide-react";
import { Link, Outlet, useLocation } from "react-router-dom";
import "../payment.css";

const navigation = [
  { to: "/payments", label: "Bảng thanh toán", icon: WalletCards, end: true },
  { to: "/payments?status=REVISION_REQUESTED", label: "Hồ sơ điều chỉnh", icon: FilePenLine },
];

export function PaymentShell() {
  const location = useLocation();
  const selectedStatus = new URLSearchParams(location.search).get("status");
  return (
    <div className="pay-shell">
      <aside className="pay-sidebar">
        <div className="pay-brand"><span><Files size={21} /></span><div><strong>Quản lý Thanh toán</strong><small>Hệ thống doanh nghiệp</small></div></div>
        <nav>{navigation.map(({ to, label, icon: Icon }, index) => { const [path, query] = to.split("?"); const active = index === 0 ? location.pathname === path && selectedStatus !== "REVISION_REQUESTED" : location.pathname === path && location.search === `?${query}`; return <Link key={label} to={to} className={`pay-nav-link${active ? " active" : ""}`}><Icon size={18} />{label}</Link>; })}</nav>
      </aside>
      <div className="pay-main">
        <header className="pay-topbar"><strong>Bảng thanh toán</strong><div className="pay-top-actions"><Bell size={18} /><span className="pay-divider" /><div className="pay-user"><div><strong>Nguyễn Văn A</strong><small>Nhân viên Kế toán</small></div><span className="pay-avatar">NA</span></div></div></header>
        <main className="pay-page"><Outlet /></main>
      </div>
    </div>
  );
}
