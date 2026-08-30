import { NavLink } from "react-router-dom";

import { navigationItems } from "../constants/navigation";

export function Sidebar() {
  return (
    <aside className="sidebar">
      <div className="brand">
        <span className="brand-mark">LB</span>
        <div>
          <strong>Logistics</strong>
          <span>Business Management</span>
        </div>
      </div>

      <nav className="nav-list" aria-label="Main navigation">
        {navigationItems.map((item) => {
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
    </aside>
  );
}
