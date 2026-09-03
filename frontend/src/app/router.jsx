import { Navigate, createBrowserRouter } from "react-router-dom";

import { ApprovalTasksPage } from "../features/approvals/pages/ApprovalTasksPage.jsx";
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

function protectedElement(element, allowedRoles) {
  return <ProtectedRoute allowedRoles={allowedRoles}>{element}</ProtectedRoute>;
}

export const router = createBrowserRouter([
  { path: "/login", element: <LoginPage /> },
  {
    path: "/",
    element: (
      <ProtectedRoute>
        <AppLayout />
      </ProtectedRoute>
    ),
    children: [
      { index: true, element: <DashboardPage /> },
      { path: "identity", element: protectedElement(<IdentityLoginPage />, MODULE_ROLES.identity) },
      { path: "customers", element: protectedElement(<CustomerListPage />, MODULE_ROLES.customers) },
      { path: "contracts", element: protectedElement(<ContractListPage />, MODULE_ROLES.contracts) },
      { path: "contracts/new", element: protectedElement(<ContractCreatePage />, MODULE_ROLES.contracts) },
      { path: "contracts/:contractId/edit", element: protectedElement(<ContractEditPage />, MODULE_ROLES.contracts) },
      { path: "prices", element: protectedElement(<PriceListPage />, MODULE_ROLES.prices) },
      { path: "production", element: protectedElement(<ProductionPeriodListPage />, MODULE_ROLES.production) },
      { path: "approvals", element: protectedElement(<ApprovalTasksPage />, MODULE_ROLES.approvals) },
      { path: "notifications", element: <NotificationListPage /> },
    ],
  },
  {
    path: "/payments",
    element: protectedElement(<PaymentShell />, MODULE_ROLES.payments),
    children: [
      { index: true, element: <PaymentListPage /> },
      { path: "create", element: protectedElement(<PaymentSearchPage />, [ROLES.ACCOUNTANT]) },
      { path: "periods", element: protectedElement(<Navigate to="/payments/create" replace />, [ROLES.ACCOUNTANT]) },
      { path: "periods/:periodKey/customers", element: protectedElement(<PaymentCustomersPage />, [ROLES.ACCOUNTANT]) },
      { path: "new", element: protectedElement(<PaymentCreatePage />, [ROLES.ACCOUNTANT]) },
      { path: ":paymentId", element: <PaymentDetailPage /> },
      { path: ":paymentId/edit", element: protectedElement(<PaymentEditPage />, [ROLES.ACCOUNTANT]) },
      { path: ":paymentId/adjust", element: protectedElement(<PaymentEditPage adjustment />, [ROLES.ACCOUNTANT]) },
      { path: ":paymentId/approval", element: <PaymentApprovalPage /> },
    ],
  },
]);
