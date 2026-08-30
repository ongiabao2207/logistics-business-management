import { Search } from "lucide-react";

export function TopBar() {
  return (
    <header className="topbar">
      <label className="search-box">
        <Search size={16} />
        <input type="search" placeholder="Search business records" />
      </label>
      <div className="user-chip">
        <span className="avatar">AD</span>
        <span>Admin User</span>
      </div>
    </header>
  );
}
