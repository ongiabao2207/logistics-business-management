import { createBrowserRouter } from "react-router-dom";

import { DashboardPage } from "../features/dashboard/pages/DashboardPage.jsx";
import { IdentityLoginPage } from "../features/identity/pages/IdentityLoginPage.jsx";
import { LoginPage } from "../features/identity/pages/LoginPage.jsx";
import { MODULE_ROLES } from "../features/identity/constants/permissions.js";
import { ContractListPage } from "../features/contracts/pages/ContractListPage.jsx";
import { ContractCreatePage } from "../features/contracts/pages/ContractCreatePage.jsx";
import { ContractEditPage } from "../features/contracts/pages/ContractEditPage.jsx";
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
      { path: "contracts", element: <ProtectedRoute allowedRoles={MODULE_ROLES.contracts}><ContractListPage /></ProtectedRoute> },
      { path: "contracts/new", element: <ProtectedRoute allowedRoles={MODULE_ROLES.contracts}><ContractCreatePage /></ProtectedRoute> },
      { path: "contracts/:contractId/edit", element: <ProtectedRoute allowedRoles={MODULE_ROLES.contracts}><ContractEditPage /></ProtectedRoute> },
      { path: "prices", element: <ProtectedRoute allowedRoles={MODULE_ROLES.prices}><PriceListPage /></ProtectedRoute> },
      { path: "production", element: <ProtectedRoute allowedRoles={MODULE_ROLES.production}><ProductionPeriodListPage /></ProtectedRoute> },
      { path: "payments", element: <ProtectedRoute allowedRoles={MODULE_ROLES.payments}><PaymentListPage /></ProtectedRoute> },
    ],
  },
]);
