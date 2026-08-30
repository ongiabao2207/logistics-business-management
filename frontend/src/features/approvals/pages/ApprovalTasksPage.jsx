import { DataState } from "../../../shared/components/DataState.jsx";
import { PageHeader } from "../../../shared/components/PageHeader.jsx";
import { usePageTitle } from "../../../shared/hooks/usePageTitle";

export function ApprovalTasksPage() {
  usePageTitle("Approvals");

  return (
    <>
      <PageHeader
        eyebrow="Approval Service"
        title="Approval Tasks"
        description="Review assigned approval steps for contracts, appendices, price lists, and payments."
      />
      <DataState
        title="Approval module placeholder"
        description="Approval Service is planned but not implemented in this repo yet."
      />
    </>
  );
}
