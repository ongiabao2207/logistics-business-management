import React, { useState, useEffect, useMemo } from "react";
import { Plus, Search, Filter, Lock, FileText, Eye, CheckCircle2, AlertCircle } from "lucide-react";

import { PageHeader } from "../../../shared/components/PageHeader.jsx";
import { usePageTitle } from "../../../shared/hooks/usePageTitle";
import { productionApi } from "../api/productionApi";
import { SAMPLE_CUSTOMERS } from "../constants/productionConstants";
import { CreateProductionPeriodModal } from "../components/CreateProductionPeriodModal.jsx";
import { ProductionPeriodDetailModal } from "../components/ProductionPeriodDetailModal.jsx";
import { LockConfirmationModal } from "../components/LockConfirmationModal.jsx";

import "../styles/production.css";

export function ProductionPeriodListPage() {
  usePageTitle("Production Periods");

  const [periods, setPeriods] = useState([]);
  const [isLoading, setIsLoading] = useState(true);

  // Filters
  const [searchTerm, setSearchTerm] = useState("");
  const [statusFilter, setStatusFilter] = useState("ALL"); // ALL | DRAFT | LOCKED
  const [customerFilter, setCustomerFilter] = useState("ALL");

  // Modal states
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [selectedDetailPeriodId, setSelectedDetailPeriodId] = useState(null);
  const [periodToLock, setPeriodToLock] = useState(null);

  useEffect(() => {
    fetchPeriods();
  }, []);

  const fetchPeriods = async () => {
    setIsLoading(true);
    try {
      const data = await productionApi.listProductionPeriods();
      setPeriods(data || []);
    } catch (err) {
      console.error("Lỗi tải danh sách kỳ sản lượng:", err);
    } finally {
      setIsLoading(false);
    }
  };

  // KPI Statistics
  const draftCount = useMemo(() => periods.filter((p) => p.status === "DRAFT").length, [periods]);
  const lockedCount = useMemo(() => periods.filter((p) => p.status === "LOCKED").length, [periods]);

  // Filtered List
  const filteredPeriods = useMemo(() => {
    return periods.filter((p) => {
      // Status filter
      if (statusFilter !== "ALL" && p.status !== statusFilter) {
        return false;
      }
      // Customer filter
      if (customerFilter !== "ALL" && p.customer_id !== customerFilter) {
        return false;
      }
      // Search term filter
      if (searchTerm.trim() !== "") {
        const term = searchTerm.toLowerCase();
        const matchId = String(p.id).toLowerCase().includes(term);
        const matchCustomer = (p.customer_name || p.customer_id || "").toLowerCase().includes(term);
        const matchContract = (p.contract_id || "").toLowerCase().includes(term);
        const matchName = (p.period_name || "").toLowerCase().includes(term);
        return matchId || matchCustomer || matchContract || matchName;
      }
      return true;
    });
  }, [periods, statusFilter, customerFilter, searchTerm]);

  return (
    <div className="prod-container">
      {/* Header */}
      <PageHeader
        eyebrow="Production Service (Dịch vụ Quản lý Sản lượng)"
        title="Quản lý Sản lượng Dịch vụ"
        description="Tiếp nhận, ghi nhận và quản lý nhật ký sản lượng dịch vụ thực tế phát sinh theo ngày/kỳ của từng khách hàng."
        actions={
          <button className="button" type="button" onClick={() => setIsCreateModalOpen(true)}>
            <Plus size={16} />
            Khai báo sản lượng kỳ mới
          </button>
        }
      />

      {/* KPI Counters */}
      <div className="prod-stats-grid">
        <div className="prod-stat-card">
          <div className="prod-stat-icon draft">
            <FileText size={24} />
          </div>
          <div className="prod-stat-info">
            <span>Đang soạn thảo (Draft)</span>
            <strong>{draftCount} kỳ</strong>
          </div>
        </div>

        <div className="prod-stat-card">
          <div className="prod-stat-icon locked">
            <Lock size={24} />
          </div>
          <div className="prod-stat-info">
            <span>Đã khóa (Locked)</span>
            <strong>{lockedCount} kỳ</strong>
          </div>
        </div>
      </div>

      {/* Filter Bar */}
      <div className="prod-filter-bar">
        <div className="search-box" style={{ width: "320px" }}>
          <Search size={16} color="#64748b" />
          <input
            type="text"
            placeholder="Tìm kiếm mã kỳ, hợp đồng, khách hàng..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>

        <div className="prod-filter-group">
          {/* Status Tabs */}
          <div className="prod-tabs">
            <button
              className={`prod-tab ${statusFilter === "ALL" ? "active" : ""}`}
              type="button"
              onClick={() => setStatusFilter("ALL")}
            >
              Tất cả ({periods.length})
            </button>
            <button
              className={`prod-tab ${statusFilter === "DRAFT" ? "active" : ""}`}
              type="button"
              onClick={() => setStatusFilter("DRAFT")}
            >
              Đang soạn thảo ({draftCount})
            </button>
            <button
              className={`prod-tab ${statusFilter === "LOCKED" ? "active" : ""}`}
              type="button"
              onClick={() => setStatusFilter("LOCKED")}
            >
              Đã khóa ({lockedCount})
            </button>
          </div>

          {/* Customer Dropdown Filter */}
          <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
            <Filter size={14} color="#64748b" />
            <select
              className="prod-select"
              value={customerFilter}
              onChange={(e) => setCustomerFilter(e.target.value)}
            >
              <option value="ALL">Tất cả khách hàng</option>
              {SAMPLE_CUSTOMERS.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Data Table */}
      <div className="table-panel">
        {isLoading ? (
          <div style={{ textAlign: "center", padding: "40px", color: "#64748b" }}>Đang tải danh sách kỳ sản lượng...</div>
        ) : filteredPeriods.length === 0 ? (
          <div className="data-state">
            <AlertCircle size={36} color="#94a3b8" style={{ margin: "0 auto 12px" }} />
            <h3 style={{ fontSize: "16px", color: "#334155" }}>Không tìm thấy kỳ sản lượng nào</h3>
            <p>Thử điều chỉnh từ khóa tìm kiếm hoặc tạo kỳ sản lượng mới.</p>
          </div>
        ) : (
          <table className="record-table">
            <thead>
              <tr>
                <th style={{ width: "16%" }}>MÃ KỲ SẢN LƯỢNG</th>
                <th style={{ width: "26%" }}>TÊN KHÁCH HÀNG</th>
                <th style={{ width: "18%" }}>SỐ HỢP ĐỒNG</th>
                <th style={{ width: "18%" }}>KHOẢNG THỜI GIAN</th>
                <th style={{ width: "12%" }}>TRẠNG THÁI</th>
                <th style={{ width: "10%", textAlign: "center" }}>THAO TÁC</th>
              </tr>
            </thead>
            <tbody>
              {filteredPeriods.map((period) => {
                const isLocked = period.status === "LOCKED";
                return (
                  <tr key={period.id}>
                    <td>
                      <strong style={{ color: "#0f766e", fontSize: "13.5px" }}>{period.period_name || `SL-${period.id}`}</strong>
                      {period.period_name && !period.period_name.startsWith("SL-") && (
                        <span style={{ display: "block", fontSize: "11px", color: "#64748b" }}>
                          {period.period_name}
                        </span>
                      )}
                    </td>
                    <td>
                      <span style={{ fontWeight: "600", color: "#0f172a" }}>
                        {period.customer_name || period.customer_id}
                      </span>
                    </td>
                    <td>
                      <span style={{ fontSize: "13px", color: "#475569" }}>{period.contract_id}</span>
                    </td>
                    <td>
                      <span style={{ fontSize: "12.5px", color: "#334155" }}>
                        {period.from_date} &rarr; {period.to_date}
                      </span>
                    </td>
                    <td>
                      {isLocked ? (
                        <span className="badge-status locked">
                          <CheckCircle2 size={12} /> Đã khóa
                        </span>
                      ) : (
                        <span className="badge-status draft">Draft</span>
                      )}
                    </td>
                    <td style={{ textAlign: "center" }}>
                      <div style={{ display: "inline-flex", gap: "6px" }}>
                        <button
                          type="button"
                          className="btn-action secondary"
                          title="Xem chi tiết / Đối soát"
                          onClick={() => setSelectedDetailPeriodId(period.id)}
                        >
                          <Eye size={14} />
                          Chi tiết
                        </button>

                        {!isLocked && (
                          <button
                            type="button"
                            className="btn-action lock"
                            title="Khóa kỳ sản lượng"
                            onClick={() => setPeriodToLock(period)}
                          >
                            <Lock size={13} />
                            Khóa kỳ
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
      </div>

      {/* Modals */}
      <CreateProductionPeriodModal
        isOpen={isCreateModalOpen}
        onClose={() => setIsCreateModalOpen(false)}
        onSuccess={fetchPeriods}
      />

      <ProductionPeriodDetailModal
        isOpen={!!selectedDetailPeriodId}
        periodId={selectedDetailPeriodId}
        onClose={() => setSelectedDetailPeriodId(null)}
        onRefreshList={fetchPeriods}
        onOpenLockModal={(period) => setPeriodToLock(period)}
      />

      <LockConfirmationModal
        isOpen={!!periodToLock}
        period={periodToLock}
        onClose={() => setPeriodToLock(null)}
        onSuccess={() => {
          fetchPeriods();
          if (selectedDetailPeriodId === periodToLock?.id) {
            setSelectedDetailPeriodId(null);
          }
        }}
      />
    </div>
  );
}
