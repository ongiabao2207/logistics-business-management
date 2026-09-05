import { Factory, FilePenLine, Files, LogOut, WalletCards } from "lucide-react";
import { Link, Outlet, useLocation, useNavigate } from "react-router-dom";

import { hasRole, ROLES } from "../../identity/constants/permissions.js";
import { useAuth } from "../../identity/hooks/useAuth.js";
import { NotificationBell } from "../../notifications/components/NotificationBell.jsx";
import "../payment.css";

const navigation = [
  { to: "/payments", label: "Bảng thanh toán", icon: WalletCards, end: true },
  { to: "/payments?view=adjustments", label: "Hồ sơ điều chỉnh", icon: FilePenLine },
  { to: "/payments/production", label: "Sản lượng", icon: Factory, roles: [ROLES.ACCOUNTANT] },
];

function getInitials(user) {
  const source = user?.full_name || user?.username || "NA";
  return source
    .split(/\s+/)
    .filter(Boolean)
    .slice(-2)
    .map((part) => part[0])
    .join("")
    .toUpperCase();
}

export function PaymentShell() {
  const location = useLocation();
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const params = new URLSearchParams(location.search);
  const adjustmentView = params.get("view") === "adjustments";
  const visibleNavigation = navigation.filter((item) => !item.roles || hasRole(user, item.roles));
  const activeItem = visibleNavigation.find((item) => {
    const path = item.to.split("?")[0];
    if (item.end) return location.pathname === path && !adjustmentView;
    if (item.to.includes("view=adjustments")) return location.pathname === path && adjustmentView;
    return location.pathname === path;
  }) ?? visibleNavigation[0];

  function handleLogout() {
    logout();
    navigate("/login", { replace: true });
  }

  return (
    <div className="pay-shell">
      <aside className="pay-sidebar">
        <div className="pay-brand">
          <span><Files size={21} /></span>
          <div>
            <strong>Quản lý Thanh toán</strong>
            <small>Hệ thống doanh nghiệp</small>
          </div>
        </div>
        <nav>
          {visibleNavigation.map(({ to, label, icon: Icon, end }) => {
            const path = to.split("?")[0];
            const active = end
              ? location.pathname === path && !adjustmentView
              : to.includes("view=adjustments")
                ? location.pathname === path && adjustmentView
                : location.pathname === path;
            return (
              <Link key={label} to={to} className={`pay-nav-link${active ? " active" : ""}`}>
                <Icon size={18} />
                {label}
              </Link>
            );
          })}
        </nav>
        <button className="pay-logout-button" type="button" onClick={handleLogout}>
          <LogOut size={18} />
          Đăng xuất
        </button>
      </aside>
      <div className="pay-main">
        <header className="pay-topbar">
          <strong>{activeItem?.label ?? "Bảng thanh toán"}</strong>
          <div className="pay-top-actions">
            <NotificationBell />
            <span className="pay-divider" />
            <div className="pay-user">
              <div>
                <strong>{user?.full_name || user?.username || "Người dùng"}</strong>
                <small>{user?.roleLabel || "Nhân viên Kế toán"}</small>
              </div>
              <span className="pay-avatar">{getInitials(user)}</span>
            </div>
          </div>
        </header>
        <main className="pay-page"><Outlet /></main>
      </div>
    </div>
  );
}
