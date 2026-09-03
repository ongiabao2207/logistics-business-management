import { Bell, FilePenLine, Files, LogOut, WalletCards } from "lucide-react";
import { Link, Outlet, useLocation, useNavigate } from "react-router-dom";

import { useAuth } from "../../identity/hooks/useAuth.js";
import "../payment.css";

const navigation = [
  { to: "/payments", label: "Bảng thanh toán", icon: WalletCards, end: true },
  { to: "/payments?view=adjustments", label: "Hồ sơ điều chỉnh", icon: FilePenLine },
];

export function PaymentShell() {
  const location = useLocation();
  const navigate = useNavigate();
  const { logout } = useAuth();
  const adjustmentView = new URLSearchParams(location.search).get("view") === "adjustments";

  function handleLogout() {
    logout();
    navigate("/login", { replace: true });
  }

  return (
    <div className="pay-shell">
      <aside className="pay-sidebar">
        <div className="pay-brand"><span><Files size={21} /></span><div><strong>Quản lý Thanh toán</strong><small>Hệ thống doanh nghiệp</small></div></div>
        <nav>{navigation.map(({ to, label, icon: Icon }, index) => { const path = to.split("?")[0]; const active = location.pathname === path && (index === 0 ? !adjustmentView : adjustmentView); return <Link key={label} to={to} className={`pay-nav-link${active ? " active" : ""}`}><Icon size={18} />{label}</Link>; })}</nav>
        <button className="pay-logout-button" type="button" onClick={handleLogout}>
          <LogOut size={18} />
          Đăng xuất
        </button>
      </aside>
      <div className="pay-main">
        <header className="pay-topbar"><strong>Bảng thanh toán</strong><div className="pay-top-actions"><Bell size={18} /><span className="pay-divider" /><div className="pay-user"><div><strong>Nguyễn Văn A</strong><small>Nhân viên Kế toán</small></div><span className="pay-avatar">NA</span></div></div></header>
        <main className="pay-page"><Outlet /></main>
      </div>
    </div>
  );
}
