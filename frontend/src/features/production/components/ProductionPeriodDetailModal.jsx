import React, { useCallback, useEffect, useState } from "react";
import { X, Lock, Save, Plus, Trash2, CheckCircle2, ShieldAlert } from "lucide-react";
import { SERVICE_CATALOG } from "../constants/productionConstants";
import { productionApi } from "../api/productionApi";
import { contractApi } from "../../contracts/api/contractApi";

export function ProductionPeriodDetailModal({ isOpen, periodId, onClose, onRefreshList, onOpenLockModal }) {
  const [period, setPeriod] = useState(null);
  const [details, setDetails] = useState([]);
  const [contractServices, setContractServices] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);

  const loadDetail = useCallback(async () => {
    setIsLoading(true);
    try {
      const data = await productionApi.getProductionPeriod(periodId);
      setPeriod(data);
      setDetails(data.details || []);
      try {
        const contract = await contractApi.getContract(data.contract_id);
        setContractServices(contract.services || []);
      } catch {
        // The period details remain readable even if Contract Service is unavailable.
        setContractServices([]);
      }
    } catch (err) {
      alert(`Không thể tải thông tin kỳ sản lượng: ${err.message}`);
    } finally {
      setIsLoading(false);
    }
  }, [periodId]);

  useEffect(() => {
    if (isOpen && periodId) {
      loadDetail();
    }
  }, [isOpen, loadDetail, periodId]);

  if (!isOpen) return null;

  const isLocked = period?.status === "LOCKED";

  const handleQuantityChange = (index, newQty) => {
    if (isLocked) return;
    const updated = [...details];
    updated[index].quantity = newQty;
    setDetails(updated);
  };

  const handleNotesChange = (index, newNotes) => {
    if (isLocked) return;
    const updated = [...details];
    updated[index].notes = newNotes;
    setDetails(updated);
  };

  const handleAddServiceItem = (serviceCode, unit) => {
    if (isLocked) return;
    const srv = SERVICE_CATALOG.find((s) => String(s.code) === String(serviceCode));
    setDetails([
      ...details,
      {
        id: Date.now(),
        service_code: serviceCode,
        recorded_date: period?.from_date || new Date().toISOString().split("T")[0],
        quantity: 1,
        unit: unit || srv?.unit || "Cont",
        notes: "Bổ sung đối soát",
      },
    ]);
  };

  const handleRemoveItem = (idToRemove) => {
    if (isLocked) return;
    setDetails(details.filter((d) => d.id !== idToRemove));
  };

  const handleSaveDetails = async () => {
    if (isLocked) return;
    setIsSaving(true);
    setSaveSuccess(false);
    try {
      const payload = {
        details: details.map((d) => ({
          service_code: d.service_code,
          recorded_date: d.recorded_date,
          quantity: Number(d.quantity),
          unit: d.unit,
          notes: d.notes,
        })),
      };
      await productionApi.replaceProductionDetails(periodId, payload);
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 3000);
      await loadDetail();
      if (onRefreshList) onRefreshList();
    } catch (err) {
      alert(`Lưu thất bại: ${err.message}`);
    } finally {
      setIsSaving(false);
    }
  };

  // Use the services of the period's own contract whenever available. This keeps
  // both draft and locked periods compatible with the real API service IDs.
  const availableServices = contractServices.length > 0
    ? contractServices.map((service) => ({
        code: String(service.service_id),
        name: service.service_name,
        unit: service.service_unit,
      }))
    : SERVICE_CATALOG;

  const groupedDetails = (() => {
    const groups = {};
    availableServices.forEach((service) => {
      const code = String(service.code);
      groups[code] = { service: { ...service, code }, items: [], subtotal: 0 };
    });

    details.forEach((item) => {
      const code = String(item.service_code);
      if (!groups[code]) {
        groups[code] = {
          service: { code, name: `Dịch vụ ${code}`, unit: item.unit || "" },
          items: [],
          subtotal: 0,
        };
      }
      groups[code].items.push(item);
      groups[code].subtotal += Number(item.quantity || 0);
    });

    return Object.values(groups).filter((group) => !isLocked || group.items.length > 0);
  })();

  return (
    <div className="modal-overlay">
      <div className="modal-content" style={{ maxWidth: "1050px" }}>
        {/* Header */}
        <div className="modal-header">
          <div>
            <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "4px" }}>
              <h2 style={{ fontSize: "20px" }}>Đối soát Chi tiết Sản lượng</h2>
              {isLocked ? (
                <span className="badge-status locked">
                  <Lock size={12} /> Đã khóa (Locked)
                </span>
              ) : (
                <span className="badge-status draft">Soạn thảo (Draft)</span>
              )}
            </div>
            {period && (
              <p>
                Mã kỳ: <strong>{period.period_name || `SL-${period.id}`}</strong> | Khách hàng: <strong>{period.customer_name || period.customer_id}</strong> | Hợp đồng: <strong>{period.contract_id}</strong>
              </p>
            )}
          </div>
          <button className="btn-close" type="button" onClick={onClose}>
            <X size={20} />
          </button>
        </div>

        {/* Body */}
        <div className="modal-body">
          {isLoading ? (
            <div style={{ textAlign: "center", padding: "40px", color: "#64748b" }}>Đang tải dữ liệu sản lượng...</div>
          ) : (
            <div className="reconcile-layout">
              <div>
                {saveSuccess && (
                  <div className="alert-box success" style={{ padding: "10px 14px", marginBottom: "16px" }}>
                    <CheckCircle2 size={18} className="alert-icon" />
                    <div className="alert-body">
                      <p style={{ fontWeight: "600" }}>Đã lưu thông tin đối soát thành công!</p>
                    </div>
                  </div>
                )}

                {isLocked && (
                  <div className="alert-box warning" style={{ padding: "10px 14px", marginBottom: "16px" }}>
                    <ShieldAlert size={18} className="alert-icon" />
                    <div className="alert-body">
                      <p style={{ fontWeight: "600" }}>Kỳ sản lượng đã được khóa (Locked). Toàn bộ số liệu đã cố định và không thể chỉnh sửa.</p>
                    </div>
                  </div>
                )}

                {/* Grouped Service Tables */}
                {groupedDetails.map((group) => (
                  <div key={group.service.code} className="service-group-block">
                    <div className="service-group-title">{group.service.name}</div>
                    <table className="record-table">
                      <thead>
                        <tr>
                          <th style={{ width: "20%" }}>Ngày cập nhật</th>
                          <th style={{ width: "35%" }}>Nội dung / Ghi chú</th>
                          <th style={{ width: "15%" }}>Đơn vị</th>
                          <th style={{ width: "20%" }}>Số lượng</th>
                          {!isLocked && <th style={{ width: "10%", textAlign: "center" }}>Xóa</th>}
                        </tr>
                      </thead>
                      <tbody>
                        {group.items.length === 0 ? (
                          <tr>
                            <td colSpan={isLocked ? 4 : 5} style={{ textAlign: "center", color: "#94a3b8", fontSize: "13px", padding: "12px" }}>
                              Chưa phát sinh sản lượng cho dịch vụ này
                            </td>
                          </tr>
                        ) : (
                          group.items.map((item) => {
                            const globalIndex = details.findIndex((d) => d.id === item.id);
                            return (
                              <tr key={item.id}>
                                <td>{item.recorded_date}</td>
                                <td>
                                  {isLocked ? (
                                    <span>{item.notes || "-"}</span>
                                  ) : (
                                    <input
                                      className="form-control"
                                      type="text"
                                      value={item.notes || ""}
                                      onChange={(e) => handleNotesChange(globalIndex, e.target.value)}
                                    />
                                  )}
                                </td>
                                <td>
                                  <span style={{ fontWeight: "600", color: "#475569" }}>{item.unit}</span>
                                </td>
                                <td>
                                  {isLocked ? (
                                    <strong style={{ fontSize: "14px", color: "#0f172a" }}>{item.quantity}</strong>
                                  ) : (
                                    <input
                                      className="form-control"
                                      type="number"
                                      step="any"
                                      value={item.quantity}
                                      onChange={(e) => handleQuantityChange(globalIndex, e.target.value)}
                                      style={{ fontWeight: "700", width: "100px" }}
                                    />
                                  )}
                                </td>
                                {!isLocked && (
                                  <td style={{ textAlign: "center" }}>
                                    <button
                                      type="button"
                                      className="btn-action danger"
                                      style={{ padding: "4px 8px" }}
                                      onClick={() => handleRemoveItem(item.id)}
                                    >
                                      <Trash2 size={13} />
                                    </button>
                                  </td>
                                )}
                              </tr>
                            );
                          })
                        )}
                      </tbody>
                    </table>

                    <div className="service-group-summary">
                      <span>TỔNG CỘNG ({group.service.name}):</span>
                      <span>
                        {group.subtotal} {group.service.unit}
                      </span>
                    </div>

                    {!isLocked && (
                      <div style={{ padding: "8px 12px", background: "#ffffff" }}>
                        <button
                          type="button"
                          className="btn-action secondary"
                          style={{ fontSize: "12px", padding: "4px 10px" }}
                          onClick={() => handleAddServiceItem(group.service.code, group.service.unit)}
                        >
                          <Plus size={12} /> Thêm sản lượng {group.service.name}
                        </button>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="modal-footer">
          <button className="btn-action secondary" type="button" onClick={onClose}>
            Quay lại
          </button>

          {!isLocked && (
            <>
              <button className="btn-action primary" type="button" onClick={handleSaveDetails} disabled={isSaving}>
                <Save size={14} />
                {isSaving ? "Đang lưu..." : "Lưu thay đổi"}
              </button>

              <button
                className="btn-action lock"
                type="button"
                onClick={() => {
                  onClose();
                  if (onOpenLockModal) onOpenLockModal(period);
                }}
              >
                <Lock size={14} />
                Khóa kỳ sản lượng
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
