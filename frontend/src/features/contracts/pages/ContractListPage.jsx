import { Plus } from "lucide-react";

import { DataState } from "../../../shared/components/DataState.jsx";
import { PageHeader } from "../../../shared/components/PageHeader.jsx";
import { StatusBadge } from "../../../shared/components/StatusBadge.jsx";
import { usePageTitle } from "../../../shared/hooks/usePageTitle";
import { ROLES } from "../../identity/constants/permissions";
import { useAuth } from "../../identity/hooks/useAuth";

const sampleContracts = [
  { id: "CTR-SAMPLE", number: "CTR-0001", customer: "Sample Customer", status: "DRAFT" },
];

export function ContractListPage() {
  usePageTitle("Contracts");
  const { user } = useAuth();

  return (
    <>
      <PageHeader
        eyebrow="Contract Service"
        title="Contracts"
        description="Create drafts, submit approval requests, and monitor contract lifecycle states."
        actions={user.role === ROLES.SALE ? (
          <button className="button" type="button">
            <Plus size={16} />
            Contract
          </button>
        ) : null}
      />

      {sampleContracts.length ? (
        <section className="table-panel">
          <table className="record-table">
            <thead>
              <tr>
                <th>Number</th>
                <th>Customer</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {sampleContracts.map((contract) => (
                <tr key={contract.id}>
                  <td>{contract.number}</td>
                  <td>{contract.customer}</td>
                  <td>
                    <StatusBadge tone="blue">{contract.status}</StatusBadge>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      ) : (
        <DataState title="No contracts yet" />
      )}
    </>
  );
}
