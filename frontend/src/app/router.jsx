import { Navigate, createBrowserRouter } from "react-router-dom";

import { ApprovalTasksPage } from "../features/approvals/pages/ApprovalTasksPage.jsx";
import { CustomerListPage } from "../features/customers/pages/CustomerListPage.jsx";
import { DashboardPage } from "../features/dashboard/pages/DashboardPage.jsx";
import { IdentityLoginPage } from "../features/identity/pages/IdentityLoginPage.jsx";
import { ContractCreatePage } from "../features/contracts/pages/ContractCreatePage.jsx";
import { ContractEditPage } from "../features/contracts/pages/ContractEditPage.jsx";
import { ContractListPage } from "../features/contracts/pages/ContractListPage.jsx";
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
import { AppLayout } from "../shared/layouts/AppLayout.jsx";

export const router = createBrowserRouter([
  {
    path: "/",
    element: <AppLayout />,
    children: [
      { index: true, element: <DashboardPage /> },
      { path: "identity", element: <IdentityLoginPage /> },
      { path: "customers", element: <CustomerListPage /> },
      { path: "contracts", element: <ContractListPage /> },
      { path: "contracts/new", element: <ContractCreatePage /> },
      { path: "contracts/:contractId/edit", element: <ContractEditPage /> },
      { path: "prices", element: <PriceListPage /> },
      { path: "production", element: <ProductionPeriodListPage /> },
      { path: "approvals", element: <ApprovalTasksPage /> },
      { path: "notifications", element: <NotificationListPage /> },
    ],
  },
  {
    path: "/payments",
    element: <PaymentShell />,
    children: [
      { index: true, element: <PaymentListPage /> },
      { path: "create", element: <PaymentSearchPage /> },
      { path: "periods", element: <Navigate to="/payments/create" replace /> },
      { path: "periods/:periodKey/customers", element: <PaymentCustomersPage /> },
      { path: "new", element: <PaymentCreatePage /> },
      { path: ":paymentId", element: <PaymentDetailPage /> },
      { path: ":paymentId/edit", element: <PaymentEditPage /> },
      { path: ":paymentId/adjust", element: <PaymentEditPage adjustment /> },
      { path: ":paymentId/approval", element: <PaymentApprovalPage /> },
    ],
  },
]);
