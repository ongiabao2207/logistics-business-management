import { KeyRound } from "lucide-react";

import { PageHeader } from "../../../shared/components/PageHeader.jsx";
import { DataState } from "../../../shared/components/DataState.jsx";
import { usePageTitle } from "../../../shared/hooks/usePageTitle";

export function IdentityLoginPage() {
  usePageTitle("Identity");

  return (
    <>
      <PageHeader
        eyebrow="Identity Service"
        title="Identity"
        description="Login, session state, roles, and permission-aware navigation will be connected here."
        actions={
          <button className="button secondary" type="button">
            <KeyRound size={16} />
            Session
          </button>
        }
      />
      <DataState
        title="Identity integration placeholder"
        description="This module is named for Identity Service consistency and can use a temporary token helper until the service is implemented."
      />
    </>
  );
}
