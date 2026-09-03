import { useState } from "react";
import { Eye, EyeOff, LockKeyhole, Truck, UserRound } from "lucide-react";
import { Navigate, useLocation, useNavigate, useSearchParams } from "react-router-dom";

import { usePageTitle } from "../../../shared/hooks/usePageTitle";
import { useAuth } from "../hooks/useAuth";

export function LoginPage() {
  usePageTitle("Đăng nhập");
  const navigate = useNavigate();
  const location = useLocation();
  const [params] = useSearchParams();
  const { user, login } = useAuth();
  const [username, setUsername] = useState(() => window.localStorage.getItem("logistics_remembered_username") ?? "");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [remember, setRemember] = useState(true);
  const [error, setError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  if (user) {
    return <Navigate to="/" replace />;
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setError("");
    setIsSubmitting(true);

    try {
      await login({ username: username.trim(), password });
      if (remember) window.localStorage.setItem("logistics_remembered_username", username.trim());
      else window.localStorage.removeItem("logistics_remembered_username");
      navigate(params.get("returnTo") ?? location.state?.from?.pathname ?? "/", { replace: true });
    } catch (requestError) {
      setError(requestError.status === 401 ? "Tên đăng nhập hoặc mật khẩu không chính xác." : "Không thể kết nối Identity Service. Vui lòng thử lại.");
    } finally {
      setIsSubmitting(false);
    }
  }

  return <main className="login-page">
    <section className="login-showcase">
      <div className="login-brand"><span><Truck size={30} /></span><div><strong>Quản lý Kinh doanh</strong><small>Logistics Business Management</small></div></div>
      <div className="showcase-content"><span aria-hidden="true" /><p>Vận hành logistics rõ ràng và hiệu quả.</p></div>
    </section>

    <section className="login-panel">
      <form className="login-form" onSubmit={handleSubmit}>
        <div className="mobile-login-brand"><Truck size={23} /><strong>Quản lý Kinh doanh</strong></div>
        <h1>Đăng nhập</h1>
        {(error || params.get("expired") === "1") && <div className="login-error" role="alert"><LockKeyhole size={18} /><span>{error || "Phiên đăng nhập đã hết hạn. Vui lòng đăng nhập lại để tiếp tục."}</span></div>}
        <label className="login-field"><span>Tên đăng nhập</span><div><UserRound size={19} /><input autoFocus autoComplete="username" value={username} onChange={(event) => setUsername(event.target.value)} placeholder="Nhập tên đăng nhập" required /></div></label>
        <label className="login-field"><span>Mật khẩu</span><div><LockKeyhole size={19} /><input type={showPassword ? "text" : "password"} autoComplete="current-password" value={password} onChange={(event) => setPassword(event.target.value)} placeholder="Nhập mật khẩu" required /><button type="button" onClick={() => setShowPassword(!showPassword)} aria-label={showPassword ? "Ẩn mật khẩu" : "Hiện mật khẩu"}>{showPassword ? <EyeOff size={19} /> : <Eye size={19} />}</button></div></label>
        <label className="login-remember"><input type="checkbox" checked={remember} onChange={(event) => setRemember(event.target.checked)} /> <span>Ghi nhớ tên đăng nhập</span></label>
        <button className="login-submit" type="submit" disabled={isSubmitting}>{isSubmitting ? <><span className="button-spinner" /> Đang đăng nhập...</> : "Đăng nhập"}</button>
      </form>
    </section>
  </main>;
}
