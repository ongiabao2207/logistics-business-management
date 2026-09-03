import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { AlertCircle, CheckCircle2, ClipboardList, Eye, FileText, Lock, Plus, Search, SlidersHorizontal } from "lucide-react";

import { PageHeader } from "../../../shared/components/PageHeader.jsx";
import { useAuth } from "../../identity/hooks/useAuth";
import { ROLES } from "../../identity/constants/permissions";
import { usePageTitle } from "../../../shared/hooks/usePageTitle";
import { ProductionPeriodDetailModal } from "../components/ProductionPeriodDetailModal.jsx";
import { LockConfirmationModal } from "../components/LockConfirmationModal.jsx";
import { productionApi } from "../api/productionApi";
import { SAMPLE_CUSTOMERS } from "../constants/productionConstants";
import "../styles/production.css";

export function ProductionPeriodListPage() {
  usePageTitle("Quản lý sản lượng");
  const navigate = useNavigate();
  const { user } = useAuth();
  const canManage = user?.role === ROLES.OPERATION;
  const [periods, setPeriods] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");
  const [statusFilter, setStatusFilter] = useState("ALL");
  const [customerFilter, setCustomerFilter] = useState("ALL");
  const [selectedDetailPeriodId, setSelectedDetailPeriodId] = useState(null);
  const [periodToLock, setPeriodToLock] = useState(null);

  async function fetchPeriods() {
    setIsLoading(true);
    try {
      setPeriods((await productionApi.listProductionPeriods()) || []);
    } catch (error) {
      console.error("Lỗi tải danh sách kỳ sản lượng:", error);
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => { fetchPeriods(); }, []);

  const draftCount = useMemo(() => periods.filter((period) => period.status === "DRAFT").length, [periods]);
  const lockedCount = useMemo(() => periods.filter((period) => period.status === "LOCKED").length, [periods]);
  const hasActiveFilters = searchTerm || (canManage && statusFilter !== "ALL") || customerFilter !== "ALL";

  const filteredPeriods = useMemo(() => periods.filter((period) => {
    if (!canManage && period.status !== "LOCKED") return false;
    if (statusFilter !== "ALL" && period.status !== statusFilter) return false;
    if (customerFilter !== "ALL" && period.customer_id !== customerFilter) return false;
    const term = searchTerm.trim().toLowerCase();
    if (!term) return true;
    return [period.id, period.customer_name, period.customer_id, period.contract_id, period.period_name]
      .some((value) => String(value || "").toLowerCase().includes(term));
  }), [canManage, customerFilter, periods, searchTerm, statusFilter]);

  function clearFilters() {
    setSearchTerm("");
    if (canManage) setStatusFilter("ALL");
    setCustomerFilter("ALL");
  }

  return (
    <div className="prod-container">
      <PageHeader
        eyebrow="Production Service"
        title="Quản lý sản lượng"
        description={canManage ? "Theo dõi, đối soát và khóa số liệu sản lượng theo từng kỳ hợp đồng." : "Xem các kỳ sản lượng đã khóa để phục vụ nghiệp vụ kế toán."}
        actions={canManage ? <button className="button navy" type="button" onClick={() => navigate("/production/new")}><Plus size={17} /> Khai báo kỳ mới</button> : null}
      />

      <section className={`prod-stats-grid${canManage ? "" : " accountant-summary"}`} aria-label="Tổng quan kỳ sản lượng">
        {canManage ? <><SummaryCard icon={<ClipboardList size={22} />} tone="total" label="Tổng kỳ sản lượng" value={`${periods.length} kỳ`} /><SummaryCard icon={<FileText size={22} />} tone="draft" label="Đang soạn thảo" value={`${draftCount} kỳ`} /><SummaryCard icon={<Lock size={22} />} tone="locked" label="Đã khóa" value={`${lockedCount} kỳ`} /></> : <SummaryCard icon={<Lock size={22} />} tone="locked" label="Kỳ sản lượng đã khóa" value={`${lockedCount} kỳ`} />}
      </section>

      <section className="prod-filter-bar" aria-label="Lọc kỳ sản lượng">
        <label className="prod-search-field">
          <Search size={18} aria-hidden="true" />
          <input value={searchTerm} onChange={(event) => setSearchTerm(event.target.value)} placeholder="Tìm mã kỳ, hợp đồng hoặc khách hàng" />
        </label>
        <div className="prod-filter-group">
          <label className="prod-customer-filter">
            <SlidersHorizontal size={16} aria-hidden="true" />
            <select className="prod-select" value={customerFilter} onChange={(event) => setCustomerFilter(event.target.value)} aria-label="Lọc theo khách hàng">
              <option value="ALL">Tất cả khách hàng</option>
              {SAMPLE_CUSTOMERS.map((customer) => <option key={customer.id} value={customer.id}>{customer.name}</option>)}
            </select>
          </label>
          {hasActiveFilters && <button className="prod-reset-filter" type="button" onClick={clearFilters}>Xóa bộ lọc</button>}
        </div>
      </section>

      <section className="table-panel prod-list-panel">
        <div className="prod-list-heading">
          <div>
            <h2>Danh sách kỳ sản lượng</h2>
            <p>{isLoading ? "Đang cập nhật dữ liệu" : `${filteredPeriods.length} trên ${periods.length} kỳ sản lượng`}</p>
          </div>
          {canManage && <div className="prod-tabs" role="group" aria-label="Lọc theo trạng thái">
            <FilterTab active={statusFilter === "ALL"} label="Tất cả" count={periods.length} onClick={() => setStatusFilter("ALL")} />
            <FilterTab active={statusFilter === "DRAFT"} label="Soạn thảo" count={draftCount} onClick={() => setStatusFilter("DRAFT")} />
            <FilterTab active={statusFilter === "LOCKED"} label="Đã khóa" count={lockedCount} onClick={() => setStatusFilter("LOCKED")} />
          </div>}
        </div>

        {isLoading ? <div className="prod-table-state">Đang tải danh sách kỳ sản lượng...</div> : (
          filteredPeriods.length === 0 ? <div className="data-state prod-empty-state"><AlertCircle size={34} aria-hidden="true" /><h3>Không tìm thấy kỳ sản lượng nào</h3><p>Thử điều chỉnh từ khóa tìm kiếm hoặc tạo kỳ sản lượng mới.</p></div> : (
            <div className="prod-table-scroll">
              <table className="record-table prod-record-table">
                <thead><tr><th>Mã kỳ sản lượng</th><th>Khách hàng</th><th>Hợp đồng</th><th>Thời gian áp dụng</th><th>Trạng thái</th><th className="prod-actions-column">Thao tác</th></tr></thead>
                <tbody>{filteredPeriods.map((period) => <ProductionRow key={period.id} period={period} canManage={canManage} onDetail={setSelectedDetailPeriodId} onLock={setPeriodToLock} />)}</tbody>
              </table>
            </div>
          )
        )}
      </section>

      <ProductionPeriodDetailModal isOpen={Boolean(selectedDetailPeriodId)} periodId={selectedDetailPeriodId} onClose={() => setSelectedDetailPeriodId(null)} onRefreshList={fetchPeriods} onOpenLockModal={setPeriodToLock} />
      <LockConfirmationModal isOpen={Boolean(periodToLock)} period={periodToLock} onClose={() => setPeriodToLock(null)} onSuccess={() => { fetchPeriods(); if (selectedDetailPeriodId === periodToLock?.id) setSelectedDetailPeriodId(null); }} />
    </div>
  );
}

function SummaryCard({ icon, tone, label, value }) {
  return <div className={`prod-stat-card ${tone}`}><div className={`prod-stat-icon ${tone}`}>{icon}</div><div className="prod-stat-info"><span>{label}</span><strong>{value}</strong></div></div>;
}

function FilterTab({ active, label, count, onClick }) {
  return <button className={`prod-tab${active ? " active" : ""}`} type="button" onClick={onClick}>{label} <span>{count}</span></button>;
}

function ProductionRow({ period, canManage, onDetail, onLock }) {
  const isLocked = period.status === "LOCKED";
  return <tr>
    <td><strong className="prod-period-code">{period.period_name || `SL-${period.id}`}</strong>{period.period_name && !period.period_name.startsWith("SL-") && <span className="prod-period-note">{period.period_name}</span>}</td>
    <td><span className="prod-customer-name">{period.customer_name || period.customer_id}</span></td>
    <td><span className="prod-contract-code">{period.contract_id}</span></td>
    <td><span className="prod-date-range"><time>{period.from_date}</time><span aria-hidden="true">→</span><time>{period.to_date}</time></span></td>
    <td>{isLocked ? <span className="badge-status locked"><CheckCircle2 size={12} /> Đã khóa</span> : <span className="badge-status draft">Soạn thảo</span>}</td>
    <td className="prod-row-actions"><div><button type="button" className="btn-action secondary" onClick={() => onDetail(period.id)}><Eye size={14} /> Chi tiết</button>{canManage && !isLocked && <button type="button" className="btn-action lock" onClick={() => onLock(period)}><Lock size={13} /> Khóa kỳ</button>}</div></td>
  </tr>;
}
