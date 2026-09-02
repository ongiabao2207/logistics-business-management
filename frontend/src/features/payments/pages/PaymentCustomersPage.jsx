import { RefreshCw } from "lucide-react";
import { useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { PaymentBreadcrumb } from "../components/PaymentBreadcrumb.jsx";
import { PaymentState } from "../components/PaymentState.jsx";
import { usePaymentContracts } from "../hooks/usePaymentContracts.js";

export function PaymentCustomersPage() {
  const { periodKey } = useParams();
  const [selected, setSelected] = useState([]);
  const {
    contracts,
    error,
    getCustomerId,
    isPending,
    refetch,
  } = usePaymentContracts();

  const candidates = useMemo(() => contracts.map((contract) => {
    const customerId = getCustomerId(contract);
    const ready = contract.status === "ACTIVE" && Boolean(customerId);
    return {
      contractId: contract.contract_id,
      customerId,
      customerName: contract.customer_name,
      status: contract.status,
      validFrom: contract.valid_from,
      validTo: contract.valid_to,
      ready,
    };
  }), [contracts, getCustomerId]);

  const readyCandidates = candidates.filter((item) => item.ready);
  const selectedCandidate = candidates.find((item) => (
    `${item.contractId}:${item.customerId}` === selected[0]
  ));

  function candidateKey(item) {
    return `${item.contractId}:${item.customerId}`;
  }

  function toggle(item) {
    const key = candidateKey(item);
    setSelected((current) => current.includes(key)
      ? current.filter((value) => value !== key)
      : [...current, key]);
  }

  function toggleAll() {
    setSelected((current) => current.length === readyCandidates.length
      ? []
      : readyCandidates.map(candidateKey));
  }

  return <>
    <PaymentBreadcrumb items={[
      { label: "Lập bảng thanh toán", to: "/payments/create" },
      { label: "Chọn khách hàng" },
    ]} />
    <div className="pay-customer-heading">
      <div><h2>Chuẩn bị dữ liệu lập bảng thanh toán kỳ {periodKey}</h2></div>
      <div>
        <button className="pay-button primary" type="button" onClick={() => refetch()}><RefreshCw size={16} />Đồng bộ hợp đồng</button>
      </div>
    </div>

    <section className="pay-metric-grid">
      <article><small>Tổng số hợp đồng</small><strong>{candidates.length}</strong></article>
      <article><small>Hợp đồng đang hiệu lực</small><strong className="blue">{readyCandidates.length}</strong></article>
      <article><small>Chưa đủ dữ liệu</small><strong className="red">{candidates.length - readyCandidates.length}</strong></article>
      <article><small>Nguồn dữ liệu</small><strong>Contract Service</strong></article>
    </section>

    {isPending ? <PaymentState title="Đang tải hợp đồng..." /> : null}
    {error ? <PaymentState title="Không thể tải Contract Service" description={error.message} /> : null}
    {!isPending && !error && !candidates.length ? <PaymentState title="Chưa có hợp đồng" description="Contract Service chưa có dữ liệu hợp đồng." /> : null}

    {candidates.length ? <section className="pay-panel customer-table">
      <div className="customer-table-top">
        <label><input type="checkbox" checked={selected.length === readyCandidates.length && readyCandidates.length > 0} onChange={toggleAll} />Chọn tất cả hợp đồng đủ điều kiện</label>
        <strong>Hiển thị: {candidates.length} hợp đồng</strong>
      </div>
      <div className="pay-table-scroll">
        <table className="pay-table">
          <thead><tr><th></th><th>Khách hàng</th><th>Mã hợp đồng</th><th>Hiệu lực</th><th>Trạng thái</th><th>Bảng giá / Sản lượng</th><th>Thao tác</th></tr></thead>
          <tbody>{candidates.map((item) => {
            const key = candidateKey(item);
            const createUrl = `/payments/new?customer_id=${item.customerId}&contract_id=${item.contractId}&period=${periodKey}`;
            return <tr key={key} className={!item.ready ? "disabled" : ""}>
              <td><input type="checkbox" checked={selected.includes(key)} disabled={!item.ready} onChange={() => toggle(item)} /></td>
              <td><strong>{item.customerName}</strong></td>
              <td><strong className="blue-text">{item.contractId}</strong></td>
              <td>{item.validFrom} – {item.validTo}</td>
              <td><span className={`mini-status ${item.status === "ACTIVE" ? "ok" : "bad"}`}>{item.status === "ACTIVE" ? "Đang hiệu lực" : item.status}</span></td>
              <td><span className="mini-status warn">Kiểm tra khi lập bảng</span></td>
              <td><Link className={`pay-button small ${item.ready ? "primary" : "disabled"}`} to={item.ready ? createUrl : "#"}>Lập bảng</Link></td>
            </tr>;
          })}</tbody>
        </table>
      </div>
    </section> : null}

    {selected.length ? <div className="pay-batch-bar">
      <span className="batch-count">{selected.length}</span>
      <p>Đã chọn {selected.length} hợp đồng</p>
      <button type="button" onClick={() => setSelected([])}>Hủy chọn</button>
      {selectedCandidate ? <Link className="pay-button light" to={`/payments/new?customer_id=${selectedCandidate.customerId}&contract_id=${selectedCandidate.contractId}&period=${periodKey}`}>Lập bảng đã chọn</Link> : null}
    </div> : null}
    <p className="pay-demo-note">Tên khách hàng, mã hợp đồng, trạng thái và thời hạn được lấy từ Contract Service. Mã khách hàng tạm đối chiếu từ dữ liệu mẫu cho đến khi Customer Service hoàn chỉnh.</p>
  </>;
}
