import { Outlet } from "react-router-dom";

import { Sidebar } from "../components/Sidebar.jsx";
import { TopBar } from "../components/TopBar.jsx";

export function AppLayout() {
  return (
    <div className="app-shell">
      <Sidebar />
      <div className="app-main">
        <TopBar />
        <main className="page-surface">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
