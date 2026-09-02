import { createBrowserRouter } from "react-router-dom";

import { ApprovalTasksPage } from "../features/approvals/pages/ApprovalTasksPage.jsx";
import { CustomerListPage } from "../features/customers/pages/CustomerListPage.jsx";
import { DashboardPage } from "../features/dashboard/pages/DashboardPage.jsx";
import { IdentityLoginPage } from "../features/identity/pages/IdentityLoginPage.jsx";
import { ContractCreatePage } from "../features/contracts/pages/ContractCreatePage.jsx";
import { ContractEditPage } from "../features/contracts/pages/ContractEditPage.jsx";
import { ContractListPage } from "../features/contracts/pages/ContractListPage.jsx";
import { NotificationListPage } from "../features/notifications/pages/NotificationListPage.jsx";
import { PaymentListPage } from "../features/payments/pages/PaymentListPage.jsx";
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
      { path: "payments", element: <PaymentListPage /> },
      { path: "approvals", element: <ApprovalTasksPage /> },
      { path: "notifications", element: <NotificationListPage /> },
    ],
  },
]);
