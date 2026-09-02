import { Plus } from "lucide-react";

import { DataState } from "../../../shared/components/DataState.jsx";
import { PageHeader } from "../../../shared/components/PageHeader.jsx";
import { usePageTitle } from "../../../shared/hooks/usePageTitle";
import { ROLES } from "../../identity/constants/permissions";
import { useAuth } from "../../identity/hooks/useAuth";

export function ProductionPeriodListPage() {
  usePageTitle("Production");
  const { user } = useAuth();

  return (
    <>
      <PageHeader
        eyebrow="Production Service"
        title="Production Periods"
        description="Create draft production periods, record details, reconcile quantities, and lock periods for payment."
        actions={user.role === ROLES.OPERATION ? (
          <button className="button" type="button">
            <Plus size={16} />
            Period
          </button>
        ) : null}
      />
      <DataState
        title="Production workspace ready"
        description="The API wrapper targets the implemented /api/v1/production-periods endpoints."
      />
    </>
  );
}
