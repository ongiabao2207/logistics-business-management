import { formatCompactContractValue } from "./contractDisplay";

export function ContractKpiCards({ contracts }) {
  const activeCount = contracts.filter((contract) => contract.status === "ACTIVE").length;
  const draftCount = contracts.filter((contract) => contract.status === "DRAFT").length;
  const totalValue = contracts.reduce(
    (sum, contract) => sum + Number(contract.total_value || 0),
    0,
  );

  return (
    <section className="contract-kpi-grid" aria-label="Contract summary">
      <article className="contract-kpi-card contract-kpi-green">
        <span>Hợp đồng hoạt động</span>
        <strong>{activeCount}</strong>
        <small>Đang hiệu lực</small>
      </article>
      <article className="contract-kpi-card contract-kpi-amber">
        <span>Bản nháp chờ ký</span>
        <strong>{draftCount}</strong>
        <small>Cần xử lý</small>
      </article>
      <article className="contract-kpi-card contract-kpi-blue">
        <span>Tổng giá trị hợp đồng</span>
        <strong>{formatCompactContractValue(totalValue)}</strong>
        <small>VND</small>
      </article>
    </section>
  );
}
