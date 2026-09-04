import { FilePenLine, Files } from "lucide-react";
import { Link, useLocation } from "react-router-dom";
const items = [{ to: "/payments", label: "Bảng thanh toán", icon: Files }, { to: "/payments?view=adjustments", label: "Hồ sơ điều chỉnh", icon: FilePenLine }];
export function PaymentTabs() { const location = useLocation(); const adjustmentView = new URLSearchParams(location.search).get("view") === "adjustments"; return <nav className="payment-tabs">{items.map(({ to, label, icon: Icon }, index) => { const path = to.split("?")[0]; const active = location.pathname === path && (index === 0 ? !adjustmentView : adjustmentView); return <Link key={label} to={to} className={`payment-tab${active ? " active" : ""}`}><Icon size={17} />{label}</Link>; })}</nav>; }
