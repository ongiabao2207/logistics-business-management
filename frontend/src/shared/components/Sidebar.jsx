import { NavLink, useNavigate } from "react-router-dom";
import { LogOut } from "lucide-react";

import { navigationItems } from "../constants/navigation";
import { hasRole } from "../../features/identity/constants/permissions";
import { useAuth } from "../../features/identity/hooks/useAuth";

export function Sidebar() {
  const navigate = useNavigate();
  const { user, logout } = useAuth();

  function handleLogout() {
    logout();
    navigate("/login", { replace: true });
  }

  return (
    <aside className="sidebar">
      <div className="brand">
        <div>
          <strong>Quản lý Kinh doanh</strong>
          <span>Hệ thống quản trị tập trung</span>
        </div>
      </div>

      <nav className="nav-list" aria-label="Main navigation">
        {navigationItems.filter((item) => !item.roles || hasRole(user, item.roles)).map((item) => {
          const Icon = item.icon;

          return (
            <NavLink
              key={item.path}
              to={item.path}
              className={({ isActive }) => `nav-link${isActive ? " is-active" : ""}`}
              end={item.path === "/"}
            >
              <Icon size={18} />
              <span>{item.label}</span>
            </NavLink>
          );
        })}
      </nav>
      <button className="logout-button" type="button" onClick={handleLogout}><LogOut size={20} /><span>Đăng xuất</span></button>
    </aside>
  );
}
