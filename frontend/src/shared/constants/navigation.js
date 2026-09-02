import {
  CreditCard,
  Factory,
  FileText,
  Home,
  KeyRound,
  Tags,
} from "lucide-react";
import { MODULE_ROLES } from "../../features/identity/constants/permissions";

export const navigationItems = [
  { label: "Tổng quan", path: "/", icon: Home },
  { label: "Người dùng", path: "/identity", icon: KeyRound, roles: MODULE_ROLES.identity },
  { label: "Hợp đồng", path: "/contracts", icon: FileText, roles: MODULE_ROLES.contracts },
  { label: "Bảng giá", path: "/prices", icon: Tags, roles: MODULE_ROLES.prices },
  { label: "Sản lượng", path: "/production", icon: Factory, roles: MODULE_ROLES.production },
  { label: "Thanh toán", path: "/payments", icon: CreditCard, roles: MODULE_ROLES.payments },
];

export const moduleSummaryItems = [
  { label: "Active Contracts", value: "0", tone: "blue" },
  { label: "Pending Approvals", value: "0", tone: "amber" },
  { label: "Locked Periods", value: "0", tone: "green" },
  { label: "Open Payments", value: "0", tone: "slate" },
];
