import { createBrowserRouter } from "react-router-dom";

import { ApprovalTasksPage } from "../features/approvals/pages/ApprovalTasksPage.jsx";
import { CustomerListPage } from "../features/customers/pages/CustomerListPage.jsx";
import { DashboardPage } from "../features/dashboard/pages/DashboardPage.jsx";
import { IdentityLoginPage } from "../features/identity/pages/IdentityLoginPage.jsx";
import { LoginPage } from "../features/identity/pages/LoginPage.jsx";
import { MODULE_ROLES } from "../features/identity/constants/permissions.js";
import { ContractListPage } from "../features/contracts/pages/ContractListPage.jsx";
import { NotificationListPage } from "../features/notifications/pages/NotificationListPage.jsx";
import { PaymentListPage } from "../features/payments/pages/PaymentListPage.jsx";
import { PriceListPage } from "../features/prices/pages/PriceListPage.jsx";
import { ProductionPeriodListPage } from "../features/production/pages/ProductionPeriodListPage.jsx";
import { AppLayout } from "../shared/layouts/AppLayout.jsx";
import { ProtectedRoute } from "../shared/components/ProtectedRoute.jsx";

export const router = createBrowserRouter([
  { path: "/login", element: <LoginPage /> },
  {
    path: "/",
    element: <ProtectedRoute><AppLayout /></ProtectedRoute>,
    children: [
      { index: true, element: <DashboardPage /> },
      { path: "identity", element: <ProtectedRoute allowedRoles={MODULE_ROLES.identity}><IdentityLoginPage /></ProtectedRoute> },
      { path: "customers", element: <ProtectedRoute allowedRoles={MODULE_ROLES.customers}><CustomerListPage /></ProtectedRoute> },
      { path: "contracts", element: <ProtectedRoute allowedRoles={MODULE_ROLES.contracts}><ContractListPage /></ProtectedRoute> },
      { path: "prices", element: <ProtectedRoute allowedRoles={MODULE_ROLES.prices}><PriceListPage /></ProtectedRoute> },
      { path: "production", element: <ProtectedRoute allowedRoles={MODULE_ROLES.production}><ProductionPeriodListPage /></ProtectedRoute> },
      { path: "payments", element: <ProtectedRoute allowedRoles={MODULE_ROLES.payments}><PaymentListPage /></ProtectedRoute> },
      { path: "approvals", element: <ProtectedRoute allowedRoles={MODULE_ROLES.approvals}><ApprovalTasksPage /></ProtectedRoute> },
      { path: "notifications", element: <NotificationListPage /> },
    ],
  },
]);
