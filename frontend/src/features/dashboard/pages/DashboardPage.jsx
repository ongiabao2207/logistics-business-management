import { ArrowRight, CreditCard, Factory, FileText, KeyRound, Tags } from "lucide-react";
import { Link } from "react-router-dom";

import { hasRole, ROLE_LABELS, ROLES } from "../../identity/constants/permissions";
import { useAuth } from "../../identity/hooks/useAuth";
import { usePageTitle } from "../../../shared/hooks/usePageTitle";

const roleMessages = {
  [ROLES.ADMIN]: "Quản lý tài khoản, vai trò và tình trạng truy cập hệ thống.",
  [ROLES.SALE]: "Theo dõi khách hàng, hợp đồng và các phiên bản bảng giá đang phụ trách.",
  [ROLES.OPERATION]: "Quản lý dữ liệu sản lượng, đối soát và khóa kỳ vận hành.",
  [ROLES.ACCOUNTANT]: "Kiểm tra dữ liệu đầu vào và quản lý các bảng thanh toán.",
  [ROLES.LEGAL]: "Rà soát hồ sơ nghiệp vụ và xử lý các bước phê duyệt được phân công.",
  [ROLES.DIRECTOR]: "Theo dõi hồ sơ quan trọng và xử lý các yêu cầu phê duyệt.",
};

const modules = [
  { title: "Người dùng & phân quyền", description: "Quản lý tài khoản và vai trò hệ thống", path: "/identity", icon: KeyRound, roles: [ROLES.ADMIN], stat: "48 tài khoản" },
  { title: "Hợp đồng", description: "Quản lý, xem chi tiết và xử lý hợp đồng", path: "/contracts", icon: FileText, roles: [ROLES.SALE, ROLES.LEGAL, ROLES.DIRECTOR], stat: "Danh sách hợp đồng" },
  { title: "Bảng giá", description: "Quản lý, xem chi tiết và xử lý bảng giá", path: "/prices", icon: Tags, roles: [ROLES.SALE, ROLES.LEGAL, ROLES.DIRECTOR], stat: "Danh sách bảng giá" },
  { title: "Sản lượng", description: "Quản lý, xem chi tiết và xử lý sản lượng", path: "/production", icon: Factory, roles: [ROLES.OPERATION, ROLES.LEGAL, ROLES.DIRECTOR], stat: "Danh sách kỳ sản lượng" },
  { title: "Thanh toán", description: "Lập và kiểm tra bảng thanh toán", path: "/payments", icon: CreditCard, roles: [ROLES.ACCOUNTANT, ROLES.DIRECTOR, ROLES.LEGAL], stat: "9 hồ sơ" },
];

export function DashboardPage() {
  usePageTitle("Tổng quan");
  const { user } = useAuth();
  const availableModules = modules.filter((module) => hasRole(user, module.roles));

  return <section className="workspace role-dashboard">
    <div className="dashboard-welcome"><div><span className="breadcrumb">Tổng quan / {ROLE_LABELS[user.role]}</span><h1>Xin chào, {user.username}</h1><p>{roleMessages[user.role]}</p></div><span className="role-identity"><strong>{ROLE_LABELS[user.role]}</strong><small>{user.email}</small></span></div>
    <div className="dashboard-section-heading"><div><h2>Module dành cho bạn</h2><p>Các chức năng hiển thị theo quyền của tài khoản đang đăng nhập.</p></div><span>{availableModules.length} module</span></div>
    {availableModules.length ? <div className="module-card-grid">{availableModules.map((module) => {
      const Icon = module.icon;
      return <Link className="module-card" to={module.path} key={module.path}><span className="module-card-icon"><Icon size={22} /></span><div><h3>{module.title}</h3><p>{module.description}</p><small>{module.stat}</small></div><ArrowRight className="module-arrow" size={19} /></Link>;
    })}</div> : <div className="empty-permission-state"><KeyRound size={25} /><h2>Không có module nghiệp vụ</h2><p>Tài khoản của bạn hiện chưa được gán chức năng nghiệp vụ phù hợp.</p></div>}
  </section>;
}
