import { Navigate, createBrowserRouter } from "react-router-dom";

import { ContractCreatePage } from "../features/contracts/pages/ContractCreatePage.jsx";
import { ContractEditPage } from "../features/contracts/pages/ContractEditPage.jsx";
import { ContractListPage } from "../features/contracts/pages/ContractListPage.jsx";
import { CustomerListPage } from "../features/customers/pages/CustomerListPage.jsx";
import { DashboardPage } from "../features/dashboard/pages/DashboardPage.jsx";
import { MODULE_ROLES, ROLES } from "../features/identity/constants/permissions.js";
import { IdentityLoginPage } from "../features/identity/pages/IdentityLoginPage.jsx";
import { LoginPage } from "../features/identity/pages/LoginPage.jsx";
import { NotificationListPage } from "../features/notifications/pages/NotificationListPage.jsx";
import { PaymentShell } from "../features/payments/components/PaymentShell.jsx";
import { PaymentApprovalPage } from "../features/payments/pages/PaymentApprovalPage.jsx";
import { PaymentCreatePage } from "../features/payments/pages/PaymentCreatePage.jsx";
import { PaymentCustomersPage } from "../features/payments/pages/PaymentCustomersPage.jsx";
import { PaymentDetailPage } from "../features/payments/pages/PaymentDetailPage.jsx";
import { PaymentEditPage } from "../features/payments/pages/PaymentEditPage.jsx";
import { PaymentListPage } from "../features/payments/pages/PaymentListPage.jsx";
import { PaymentSearchPage } from "../features/payments/pages/PaymentSearchPage.jsx";
import { PriceListPage } from "../features/prices/pages/PriceListPage.jsx";
import { ProductionPeriodListPage } from "../features/production/pages/ProductionPeriodListPage.jsx";
import { ProtectedRoute } from "../shared/components/ProtectedRoute.jsx";
import { AppLayout } from "../shared/layouts/AppLayout.jsx";

function protect(element, allowedRoles) {
  return <ProtectedRoute allowedRoles={allowedRoles}>{element}</ProtectedRoute>;
}

export const router = createBrowserRouter([
  { path: "/login", element: <LoginPage /> },
  {
    path: "/",
    element: protect(<AppLayout />),
    children: [
      { index: true, element: <DashboardPage /> },
      { path: "identity", element: protect(<IdentityLoginPage />, MODULE_ROLES.identity) },
      { path: "customers", element: protect(<CustomerListPage />, MODULE_ROLES.customers) },
      { path: "contracts", element: protect(<ContractListPage />, MODULE_ROLES.contracts) },
      { path: "contracts/new", element: protect(<ContractCreatePage />, MODULE_ROLES.contracts) },
      { path: "contracts/:contractId/edit", element: protect(<ContractEditPage />, MODULE_ROLES.contracts) },
      { path: "prices", element: protect(<PriceListPage />, MODULE_ROLES.prices) },
      { path: "production", element: protect(<ProductionPeriodListPage />, MODULE_ROLES.production) },
      { path: "notifications", element: <NotificationListPage /> },
    ],
  },
  {
    path: "/payments",
    element: protect(<PaymentShell />, MODULE_ROLES.payments),
    children: [
      { index: true, element: <PaymentListPage /> },
      { path: "create", element: protect(<PaymentSearchPage />, [ROLES.ACCOUNTANT]) },
      { path: "periods", element: protect(<Navigate to="/payments/create" replace />, [ROLES.ACCOUNTANT]) },
      { path: "periods/:periodKey/customers", element: protect(<PaymentCustomersPage />, [ROLES.ACCOUNTANT]) },
      { path: "new", element: protect(<PaymentCreatePage />, [ROLES.ACCOUNTANT]) },
      { path: ":paymentId", element: <PaymentDetailPage /> },
      { path: ":paymentId/edit", element: protect(<PaymentEditPage />, [ROLES.ACCOUNTANT]) },
      { path: ":paymentId/adjust", element: protect(<PaymentEditPage adjustment />, [ROLES.ACCOUNTANT]) },
      { path: ":paymentId/approval", element: <PaymentApprovalPage /> },
    ],
  },
]);
