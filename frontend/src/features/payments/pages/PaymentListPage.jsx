import { Calculator, Plus } from "lucide-react";

import { DataState } from "../../../shared/components/DataState.jsx";
import { PageHeader } from "../../../shared/components/PageHeader.jsx";
import { usePageTitle } from "../../../shared/hooks/usePageTitle";
import { ROLES } from "../../identity/constants/permissions";
import { useAuth } from "../../identity/hooks/useAuth";

export function PaymentListPage() {
  usePageTitle("Payments");
  const { user } = useAuth();

  return (
    <>
      <PageHeader
        eyebrow="Payment Service"
        title="Payments"
        description="Preview statements, create payment records, submit approvals, and track adjustments."
        actions={user.role === ROLES.ACCOUNTANT ? (
          <>
            <button className="button secondary" type="button">
              <Calculator size={16} />
              Preview
            </button>
            <button className="button" type="button">
              <Plus size={16} />
              Payment
            </button>
          </>
        ) : null}
      />
      <DataState
        title="Payment workspace ready"
        description="The API wrapper maps to the implemented Payment Service /payments routes."
      />
    </>
  );
}
