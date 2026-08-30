import { Plus } from "lucide-react";

import { DataState } from "../../../shared/components/DataState.jsx";
import { PageHeader } from "../../../shared/components/PageHeader.jsx";
import { usePageTitle } from "../../../shared/hooks/usePageTitle";

export function PriceListPage() {
  usePageTitle("Prices");

  return (
    <>
      <PageHeader
        eyebrow="Price Service"
        title="Prices"
        description="Manage service catalog items, price lists, and effective price resolution."
        actions={
          <button className="button" type="button">
            <Plus size={16} />
            Price List
          </button>
        }
      />
      <DataState
        title="Price workspace ready"
        description="The API wrapper is aligned with the existing Price Service routes under /api/v1."
      />
    </>
  );
}
