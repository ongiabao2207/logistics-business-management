import { useAuth } from "../../features/identity/hooks/useAuth";

export function TopBar() {
  const { user } = useAuth();
  const initials = user?.username?.slice(0, 2).toUpperCase() ?? "--";

  return (
    <header className="topbar">
      <div className="topbar-actions">
        <div className="user-chip"><div><strong>{user?.username}</strong><small>{user?.roleLabel}</small></div><span className="avatar">{initials}</span></div>
      </div>
    </header>
  );
}
