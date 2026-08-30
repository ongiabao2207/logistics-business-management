import { Plus } from "lucide-react";

import { DataState } from "../../../shared/components/DataState.jsx";
import { PageHeader } from "../../../shared/components/PageHeader.jsx";
import { usePageTitle } from "../../../shared/hooks/usePageTitle";

export function CustomerListPage() {
  usePageTitle("Customers");

  return (
    <>
      <PageHeader
        eyebrow="Customer Service"
        title="Customers"
        description="Search, create, update, and suspend customer records."
        actions={
          <button className="button" type="button">
            <Plus size={16} />
            Customer
          </button>
        }
      />
      <DataState
        title="Customer module placeholder"
        description="Customer Service is not implemented yet, so this page is ready for mock data or the future public API."
      />
    </>
  );
}
