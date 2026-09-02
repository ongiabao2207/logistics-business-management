import { Navigate, useLocation } from "react-router-dom";

import { hasRole } from "../../features/identity/constants/permissions";
import { useAuth } from "../../features/identity/hooks/useAuth";

export function ProtectedRoute({ children, allowedRoles }) {
  const location = useLocation();
  const { user, isLoading } = useAuth();

  if (isLoading) {
    return <div className="auth-loading"><span className="button-spinner" /><p>Đang xác thực phiên đăng nhập...</p></div>;
  }

  if (!user) {
    return <Navigate to="/login" replace state={{ from: location }} />;
  }

  if (allowedRoles && !hasRole(user, allowedRoles)) {
    return <Navigate to="/" replace />;
  }

  return children;
}
