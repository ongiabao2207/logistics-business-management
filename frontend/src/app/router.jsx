import React from "react";
import { createBrowserRouter } from "react-router-dom";

import { ApprovalTasksPage } from "../features/approvals/pages/ApprovalTasksPage.jsx";
import { CustomerListPage } from "../features/customers/pages/CustomerListPage.jsx";
import { DashboardPage } from "../features/dashboard/pages/DashboardPage.jsx";
import { ContractCreatePage } from "../features/contracts/pages/ContractCreatePage.jsx";
import { ContractEditPage } from "../features/contracts/pages/ContractEditPage.jsx";
import { ContractListPage } from "../features/contracts/pages/ContractListPage.jsx";
import { MODULE_ROLES } from "../features/identity/constants/permissions.js";
import { IdentityLoginPage } from "../features/identity/pages/IdentityLoginPage.jsx";
import { LoginPage } from "../features/identity/pages/LoginPage.jsx";
import { NotificationListPage } from "../features/notifications/pages/NotificationListPage.jsx";
import { PaymentListPage } from "../features/payments/pages/PaymentListPage.jsx";
import { PriceListPage } from "../features/prices/pages/PriceListPage.jsx";
import { ProductionPeriodListPage } from "../features/production/pages/ProductionPeriodListPage.jsx";
import { CreateProductionPeriodPage } from "../features/production/pages/CreateProductionPeriodPage.jsx";
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
      {
        path: "identity",
        element: protectedElement(<IdentityLoginPage />, MODULE_ROLES.identity),
      },
      {
        path: "customers",
        element: protectedElement(<CustomerListPage />, MODULE_ROLES.customers),
      },
      {
        path: "contracts",
        element: protectedElement(<ContractListPage />, MODULE_ROLES.contracts),
      },
      {
        path: "contracts/new",
        element: protectedElement(<ContractCreatePage />, MODULE_ROLES.contracts),
      },
      {
        path: "contracts/:contractId/edit",
        element: protectedElement(<ContractEditPage />, MODULE_ROLES.contracts),
      },
      {
        path: "prices",
        element: protectedElement(<PriceListPage />, MODULE_ROLES.prices),
      },
      {
        path: "production",
        element: protectedElement(<ProductionPeriodListPage />, MODULE_ROLES.production),
      },
      {
        path: "production/new",
        element: protectedElement(<CreateProductionPeriodPage />, MODULE_ROLES.production),
      },
      {
        path: "payments",
        element: protectedElement(<PaymentListPage />, MODULE_ROLES.payments),
      },
      {
        path: "approvals",
        element: protectedElement(<ApprovalTasksPage />, MODULE_ROLES.approvals),
      },
      { path: "notifications", element: <NotificationListPage /> },
    ],
  },
]);
