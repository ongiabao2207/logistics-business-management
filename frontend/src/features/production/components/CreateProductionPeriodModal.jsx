import React, { useState, useEffect } from "react";
import { X, Plus, Trash2, AlertTriangle, CheckCircle, Calendar, Building, FileText } from "lucide-react";
import { SAMPLE_CUSTOMERS, SERVICE_CATALOG } from "../constants/productionConstants";
import { productionApi } from "../api/productionApi";

export function CreateProductionPeriodModal({ isOpen, onClose, onSuccess }) {
  const [selectedCustomerId, setSelectedCustomerId] = useState("");
  const [selectedContractId, setSelectedContractId] = useState("");
  const [periodName, setPeriodName] = useState("");
  const [fromDate, setFromDate] = useState("");
  const [toDate, setToDate] = useState("");

  const [details, setDetails] = useState([
    {
      service_code: "SRV-BX-20FT",
      recorded_date: new Date().toISOString().split("T")[0],
      quantity: 10,
      unit: "Cont",
      notes: "Bốc xếp container nhập bãi",
    },
  ]);

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [alertState, setAlertState] = useState(null); // { type: 'success' | 'invalid_date' | 'overlap', title, message }

  const selectedCustomer = SAMPLE_CUSTOMERS.find((c) => c.id === selectedCustomerId);
  const contract = selectedCustomer?.contract;

  // Auto set contract when customer changes
  useEffect(() => {
    if (selectedCustomer) {
      setSelectedContractId(selectedCustomer.contract.id);
      const currentMonth = new Date().toLocaleDateString("vi-VN", { month: "2-digit", year: "numeric" });
      setPeriodName(`Sản lượng Tháng ${currentMonth}`);
    } else {
      setSelectedContractId("");
    }
  }, [selectedCustomerId]);

  if (!isOpen) return null;

  const handleAddRow = () => {
    const defaultSrv = SERVICE_CATALOG[0];
    setDetails([
      ...details,
      {
        service_code: defaultSrv.code,
        recorded_date: fromDate || new Date().toISOString().split("T")[0],
        quantity: 1,
        unit: defaultSrv.unit,
        notes: "",
      },
    ]);
  };

  const handleRemoveRow = (index) => {
    if (details.length <= 1) return;
    setDetails(details.filter((_, i) => i !== index));
  };

  const handleDetailChange = (index, field, value) => {
    const updated = [...details];
    updated[index][field] = value;
    if (field === "service_code") {
      const match = SERVICE_CATALOG.find((s) => s.code === value);
      if (match) {
        updated[index].unit = match.unit;
      }
    }
    setDetails(updated);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setAlertState(null);

    if (!selectedCustomerId || !selectedContractId || !fromDate || !toDate) {
      alert("Vui lòng điền đầy đủ các thông tin bắt buộc.");
      return;
    }

    if (new Date(fromDate) > new Date(toDate)) {
      alert("Ngày bắt đầu không được lớn hơn ngày kết thúc.");
      return;
    }

    // Check contract date validity
    if (contract) {
      const pFrom = new Date(fromDate);
      const pTo = new Date(toDate);
      const cFrom = new Date(contract.validFrom);
      const cTo = new Date(contract.validTo);

      if (pFrom < cFrom || pTo > cTo) {
        setAlertState({
          type: "invalid_date",
          title: "Khoảng thời gian không hợp lệ",
          message: `Khoảng thời gian tính phí bạn nhập nằm ngoài thời hạn hiệu lực của hợp đồng (${contract.validFrom} đến ${contract.validTo}). Vui lòng kiểm tra lại.`,
        });
        return;
      }
    }

    setIsSubmitting(true);
    try {
      // Check overlap API
      const overlapRes = await productionApi.checkOverlap({
        customer_id: selectedCustomerId,
        contract_id: selectedContractId,
        from_date: fromDate,
        to_date: toDate,
      });

      if (overlapRes.overlaps) {
        setAlertState({
          type: "overlap",
          title: "Cảnh báo: Trùng lặp kỳ sản lượng",
          message: `Hệ thống phát hiện Khách hàng và Hợp đồng này đã có bảng sản lượng tồn tại trong khoảng thời gian đã chọn (Kỳ #${overlapRes.conflicting_period_ids.join(", #")}).`,
        });
        setIsSubmitting(false);
        return;
      }

      // Create Draft
      const payload = {
        customer_id: selectedCustomerId,
        contract_id: selectedContractId,
        period_name: periodName,
        from_date: fromDate,
        to_date: toDate,
        details: details.map((d) => ({
          service_code: d.service_code,
          recorded_date: d.recorded_date,
          quantity: Number(d.quantity),
          unit: d.unit,
          notes: d.notes,
        })),
      };

      const created = await productionApi.createDraft(payload);

      setAlertState({
        type: "success",
        title: "Lưu thành công!",
        message: `Dữ liệu kỳ sản lượng (${created.period_name || created.id}) đã được ghi nhận vào hệ thống ở trạng thái Bản nháp (DRAFT). Bạn có thể xem lại hoặc chỉnh sửa sau này.`,
        createdId: created.id,
      });
    } catch (err) {
      alert(`Đã xảy ra lỗi: ${err.message || "Không thể tạo kỳ sản lượng"}`);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="modal-overlay">
      <div className="modal-content">
        <div className="modal-header">
          <div>
            <h2>Khai báo sản lượng kỳ mới</h2>
            <p>Thiết lập thông tin chung và nhập dữ liệu chi tiết cho kỳ tính phí hiện tại.</p>
          </div>
          <button className="btn-close" type="button" onClick={onClose}>
            <X size={20} />
          </button>
        </div>

        <div className="modal-body">
          {/* Success State View */}
          {alertState?.type === "success" ? (
            <div style={{ textAlign: "center", padding: "30px 20px" }}>
              <div style={{ display: "inline-flex", background: "#dcfce7", color: "#16a34a", padding: "16px", borderRadius: "999px", marginBottom: "16px" }}>
                <CheckCircle size={48} />
              </div>
              <h3 style={{ fontSize: "22px", margin: "0 0 8px", color: "#0f172a" }}>{alertState.title}</h3>
              <p style={{ maxWidth: "560px", margin: "0 auto 24px", color: "#64748b", lineHeight: "1.5" }}>
                {alertState.message}
              </p>
              <div style={{ display: "flex", justifyContent: "center", gap: "12px" }}>
                <button
                  className="btn-action primary"
                  type="button"
                  onClick={() => {
                    onSuccess();
                    onClose();
                  }}
                >
                  Về danh sách
                </button>
                <button
                  className="btn-action secondary"
                  type="button"
                  onClick={() => {
                    setAlertState(null);
                    setFromDate("");
                    setToDate("");
                  }}
                >
                  Tiếp tục khai báo
                </button>
              </div>
            </div>
          ) : (
            <form id="create-period-form" onSubmit={handleSubmit}>
              {/* Warning Alert Boxes if any */}
              {alertState?.type === "invalid_date" && (
                <div className="alert-box danger">
                  <AlertTriangle size={24} className="alert-icon" />
                  <div className="alert-body">
                    <h4>{alertState.title}</h4>
                    <p>{alertState.message}</p>
                  </div>
                </div>
              )}

              {alertState?.type === "overlap" && (
                <div className="alert-box warning">
                  <AlertTriangle size={24} className="alert-icon" />
                  <div className="alert-body">
                    <h4>{alertState.title}</h4>
                    <p>{alertState.message}</p>
                  </div>
                </div>
              )}

              {/* General Info Grid */}
              <div className="form-grid">
                <div className="form-group">
                  <label>
                    <Building size={14} style={{ display: "inline", marginRight: "4px" }} />
                    Khách hàng <span className="required">*</span>
                  </label>
                  <select
                    className="form-control"
                    value={selectedCustomerId}
                    onChange={(e) => setSelectedCustomerId(e.target.value)}
                    required
                  >
                    <option value="">-- Chọn khách hàng --</option>
                    {SAMPLE_CUSTOMERS.map((c) => (
                      <option key={c.id} value={c.id}>
                        {c.name} ({c.id})
                      </option>
                    ))}
                  </select>
                </div>

                <div className="form-group">
                  <label>
                    <FileText size={14} style={{ display: "inline", marginRight: "4px" }} />
                    Hợp đồng áp dụng <span className="required">*</span>
                  </label>
                  <input
                    className="form-control"
                    type="text"
                    value={contract ? `${contract.name} (${contract.id})` : ""}
                    placeholder="Tự động chọn hợp đồng tương ứng"
                    readOnly
                  />
                </div>

                <div className="form-group full-width">
                  <label>Tên kỳ ghi nhận sản lượng <span className="required">*</span></label>
                  <input
                    className="form-control"
                    type="text"
                    value={periodName}
                    onChange={(e) => setPeriodName(e.target.value)}
                    placeholder="VD: Sản lượng Tháng 10/2026"
                    required
                  />
                </div>

                <div className="form-group">
                  <label>
                    <Calendar size={14} style={{ display: "inline", marginRight: "4px" }} />
                    Từ ngày <span className="required">*</span>
                  </label>
                  <input
                    className="form-control"
                    type="date"
                    value={fromDate}
                    onChange={(e) => setFromDate(e.target.value)}
                    required
                  />
                </div>

                <div className="form-group">
                  <label>
                    <Calendar size={14} style={{ display: "inline", marginRight: "4px" }} />
                    Đến ngày <span className="required">*</span>
                  </label>
                  <input
                    className="form-control"
                    type="date"
                    value={toDate}
                    onChange={(e) => setToDate(e.target.value)}
                    required
                  />
                </div>
              </div>

              {/* Service Details Section */}
              <div className="service-table-section">
                <div className="service-table-header">
                  <h3>Danh mục dịch vụ &amp; Sản lượng thực tế</h3>
                  <button className="btn-action secondary" type="button" onClick={handleAddRow}>
                    <Plus size={14} />
                    Thêm dòng sản lượng
                  </button>
                </div>

                <div style={{ overflowX: "auto" }}>
                  <table className="record-table">
                    <thead>
                      <tr>
                        <th style={{ width: "30%" }}>Hạng mục dịch vụ</th>
                        <th style={{ width: "20%" }}>Ngày ghi nhận</th>
                        <th style={{ width: "15%" }}>Sản lượng</th>
                        <th style={{ width: "15%" }}>Đơn vị</th>
                        <th>Ghi chú</th>
                        <th style={{ width: "60px", textAlign: "center" }}>Xóa</th>
                      </tr>
                    </thead>
                    <tbody>
                      {details.map((item, idx) => (
                        <tr key={idx}>
                          <td>
                            <select
                              className="form-control"
                              value={item.service_code}
                              onChange={(e) => handleDetailChange(idx, "service_code", e.target.value)}
                            >
                              {SERVICE_CATALOG.map((s) => (
                                <option key={s.code} value={s.code}>
                                  {s.name}
                                </option>
                              ))}
                            </select>
                          </td>
                          <td>
                            <input
                              className="form-control"
                              type="date"
                              value={item.recorded_date}
                              onChange={(e) => handleDetailChange(idx, "recorded_date", e.target.value)}
                              required
                            />
                          </td>
                          <td>
                            <input
                              className="form-control"
                              type="number"
                              min="0.001"
                              step="any"
                              value={item.quantity}
                              onChange={(e) => handleDetailChange(idx, "quantity", e.target.value)}
                              required
                            />
                          </td>
                          <td>
                            <input className="form-control" type="text" value={item.unit} readOnly />
                          </td>
                          <td>
                            <input
                              className="form-control"
                              type="text"
                              placeholder="Nhập ghi chú..."
                              value={item.notes}
                              onChange={(e) => handleDetailChange(idx, "notes", e.target.value)}
                            />
                          </td>
                          <td style={{ textAlign: "center" }}>
                            <button
                              type="button"
                              className="btn-action danger"
                              style={{ padding: "6px" }}
                              onClick={() => handleRemoveRow(idx)}
                              disabled={details.length <= 1}
                            >
                              <Trash2 size={14} />
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </form>
          )}
        </div>

        {alertState?.type !== "success" && (
          <div className="modal-footer">
            <button className="btn-action secondary" type="button" onClick={onClose} disabled={isSubmitting}>
              Hủy
            </button>
            <button className="btn-action primary" type="submit" form="create-period-form" disabled={isSubmitting}>
              {isSubmitting ? "Đang xử lý..." : "Lưu tạm (Draft)"}
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
