import { PageHeader } from "../../../shared/components/PageHeader.jsx";
import { moduleSummaryItems } from "../../../shared/constants/navigation";
import { usePageTitle } from "../../../shared/hooks/usePageTitle";

export function DashboardPage() {
  usePageTitle("Dashboard");

  return (
    <>
      <PageHeader
        eyebrow="Overview"
        title="Business Operations"
        description="A working surface for contracts, pricing, production, payments, approvals, and notifications."
      />

      <section className="content-grid" aria-label="Module summary">
        {moduleSummaryItems.map((item) => (
          <article className="summary-card" key={item.label}>
            <span>{item.label}</span>
            <strong>{item.value}</strong>
          </article>
        ))}
      </section>
    </>
  );
}
