import {
  Bell,
  ClipboardCheck,
  CreditCard,
  Factory,
  FileText,
  Home,
  KeyRound,
  Tags,
  Users,
} from "lucide-react";

export const navigationItems = [
  { label: "Dashboard", path: "/", icon: Home },
  { label: "Identity", path: "/identity", icon: KeyRound },
  { label: "Customers", path: "/customers", icon: Users },
  { label: "Contracts", path: "/contracts", icon: FileText },
  { label: "Prices", path: "/prices", icon: Tags },
  { label: "Production", path: "/production", icon: Factory },
  { label: "Payments", path: "/payments", icon: CreditCard },
  { label: "Approvals", path: "/approvals", icon: ClipboardCheck },
  { label: "Notifications", path: "/notifications", icon: Bell },
];

export const moduleSummaryItems = [
  { label: "Active Contracts", value: "0", tone: "blue" },
  { label: "Pending Approvals", value: "0", tone: "amber" },
  { label: "Locked Periods", value: "0", tone: "green" },
  { label: "Open Payments", value: "0", tone: "slate" },
];
