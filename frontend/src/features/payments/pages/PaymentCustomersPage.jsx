import { RefreshCw } from "lucide-react";
import { useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { PaymentBreadcrumb } from "../components/PaymentBreadcrumb.jsx";
import { PaymentState } from "../components/PaymentState.jsx";
import { usePaymentContracts } from "../hooks/usePaymentContracts.js";
import { usePayments } from "../hooks/usePayments.js";

function datesFromPeriod(period) {
  const [year, month] = period.split("-").map(Number);
  return {
    start: `${year}-${String(month).padStart(2, "0")}-01`,
    end: `${year}-${String(month).padStart(2, "0")}-${String(new Date(year, month, 0).getDate()).padStart(2, "0")}`,
  };
}

export function PaymentCustomersPage() {
  const { periodKey } = useParams();
  const [selected, setSelected] = useState([]);
  const [syncMessage, setSyncMessage] = useState("");
  const [isSyncing, setIsSyncing] = useState(false);
  const periodDates = datesFromPeriod(periodKey);
  const paymentsQuery = usePayments({
    offset: 0,
    limit: 200,
    period_start: periodDates.start,
    period_end: periodDates.end,
  });
  const {
    contracts,
    error,
    getCustomerId,
    getCustomerName,
    isPending,
    refetch,
  } = usePaymentContracts();

  const candidates = useMemo(() => contracts.map((contract) => {
    const customerId = getCustomerId(contract);
    const existingPayment = (paymentsQuery.data ?? []).find((payment) => (
      payment.contract_id === contract.contract_id
      && payment.period_start === periodDates.start
      && payment.period_end === periodDates.end
    ));
    const ready = contract.status === "ACTIVE" && Boolean(customerId) && !existingPayment;
    return {
      contractId: contract.contract_id,
      customerId,
      customerName: getCustomerName(contract.contract_id, customerId),
      status: contract.status,
      validFrom: contract.valid_from,
      validTo: contract.valid_to,
      existingPayment,
      ready,
    };
  }), [contracts, getCustomerId, getCustomerName, paymentsQuery.data, periodDates.end, periodDates.start]);

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

  async function syncContracts() {
    setIsSyncing(true);
    setSyncMessage("");
    const [contractsResult, paymentsResult] = await Promise.allSettled([
      refetch(),
      paymentsQuery.refetch(),
    ]);
    const failed = [contractsResult, paymentsResult].some((result) => (
      result.status === "rejected" || result.value?.isError
    ));
    setSyncMessage(failed
      ? "Không thể đồng bộ đầy đủ dữ liệu. Vui lòng thử lại."
      : "Đã cập nhật hợp đồng và trạng thái bảng thanh toán mới nhất.");
    setIsSyncing(false);
  }

  return <>
    <PaymentBreadcrumb items={[
      { label: "Lập bảng thanh toán", to: "/payments/create" },
      { label: "Chọn khách hàng" },
    ]} />
    <div className="pay-customer-heading">
      <div><h2>Chuẩn bị dữ liệu lập bảng thanh toán kỳ {periodKey}</h2></div>
      <div>
        <button className="pay-button primary" type="button" disabled={isSyncing} onClick={syncContracts}><RefreshCw className={isSyncing ? "pay-spin" : ""} size={16} />{isSyncing ? "Đang đồng bộ..." : "Đồng bộ hợp đồng"}</button>
      </div>
    </div>

    {syncMessage ? <div className={`pay-alert ${syncMessage.startsWith("Không") ? "error" : "success"}`}>{syncMessage}</div> : null}

    <section className="pay-metric-grid">
      <article><small>Tổng số hợp đồng</small><strong>{candidates.length}</strong></article>
      <article><small>Hợp đồng đang hiệu lực</small><strong className="blue">{readyCandidates.length}</strong></article>
      <article><small>Chưa đủ dữ liệu</small><strong className="red">{candidates.length - readyCandidates.length}</strong></article>
      <article><small>Nguồn dữ liệu</small><strong>Contract Service</strong></article>
    </section>

    {isPending || paymentsQuery.isPending ? <PaymentState title="Đang kiểm tra dữ liệu hợp đồng và bảng thanh toán..." /> : null}
    {error ? <PaymentState title="Không thể tải dữ liệu hợp đồng hoặc khách hàng" description={error.message} /> : null}
    {paymentsQuery.error ? <PaymentState title="Không thể kiểm tra bảng thanh toán đã tồn tại" description={paymentsQuery.error.message} /> : null}
    {!isPending && !paymentsQuery.isPending && !error && !paymentsQuery.error && !candidates.length ? <PaymentState title="Chưa có hợp đồng" description="Contract Service chưa có dữ liệu hợp đồng." /> : null}

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
              <td>{item.existingPayment ? <span className="mini-status ok">Đã lập bảng</span> : <span className="mini-status warn">Sẵn sàng lập bảng</span>}</td>
              <td>{item.existingPayment ? <Link className="pay-button small outline" to={`/payments/${item.existingPayment.id}`}>Xem bảng {item.existingPayment.id}</Link> : <Link className={`pay-button small ${item.ready ? "primary" : "disabled"}`} to={item.ready ? createUrl : "#"}>Lập bảng</Link>}</td>
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
    <p className="pay-demo-note">Tên và mã khách hàng được lấy từ Customer Service; thông tin hợp đồng được lấy từ Contract Service.</p>
  </>;
}
