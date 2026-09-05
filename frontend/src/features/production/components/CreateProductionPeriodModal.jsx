import React, { useState, useEffect } from "react";
import { X, Plus, Trash2, AlertTriangle, CheckCircle, Calendar, Building, FileText } from "lucide-react";
import { contractApi } from "../../contracts/api/contractApi";
import { productionApi } from "../api/productionApi";

export function CreateProductionPeriodModal({ isOpen, onClose, onSuccess, pageMode = false }) {
  const [selectedContractId, setSelectedContractId] = useState("");
  const [contracts, setContracts] = useState([]);
  const [selectedContract, setSelectedContract] = useState(null);
  const [isContractsLoading, setIsContractsLoading] = useState(true);
  const [contractsError, setContractsError] = useState("");
  const [fromDate, setFromDate] = useState("");
  const [toDate, setToDate] = useState("");

  const [details, setDetails] = useState([]);

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [alertState, setAlertState] = useState(null);

  const contract = contracts.find((item) => item.contract_id === selectedContractId);
  const contractServices = selectedContract?.services ?? [];

  useEffect(() => {
    let cancelled = false;
    setIsContractsLoading(true);
    setContractsError("");
    contractApi.listContracts()
      .then((items) => {
        if (!cancelled) setContracts(items.filter((item) => item.status === "ACTIVE"));
      })
      .catch((error) => {
        if (!cancelled) setContractsError(error.message || "Không thể tải danh sách hợp đồng.");
      })
      .finally(() => {
        if (!cancelled) setIsContractsLoading(false);
      });
    return () => { cancelled = true; };
  }, []);

  useEffect(() => {
    let cancelled = false;
    setSelectedContract(null);
    setDetails([]);
    if (!selectedContractId) return () => { cancelled = true; };

    contractApi.getContract(selectedContractId)
      .then((item) => {
        if (cancelled) return;
        setSelectedContract(item);
        const firstService = item.services[0];
        if (firstService) {
          setDetails([{
            service_code: String(firstService.service_id),
            recorded_date: new Date().toISOString().split("T")[0],
            quantity: 1,
            unit: firstService.service_unit,
            notes: "",
          }]);
        }
      })
      .catch((error) => {
        if (!cancelled) setContractsError(error.message || "Không thể tải chi tiết hợp đồng.");
      });
    return () => { cancelled = true; };
  }, [selectedContractId]);

  // The contract is the source of truth; its linked customer is displayed automatically.
  useEffect(() => {
    setAlertState(null);
  }, [selectedContractId]);

  if (!isOpen) return null;

  const handleAddRow = () => {
    const defaultSrv = contractServices[0];
    if (!defaultSrv) return;
    setDetails([
      ...details,
      {
        service_code: String(defaultSrv.service_id),
        recorded_date: fromDate || new Date().toISOString().split("T")[0],
        quantity: 1,
        unit: defaultSrv.service_unit,
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
      const match = contractServices.find((service) => String(service.service_id) === value);
      if (match) {
        updated[index].unit = match.service_unit;
      }
    }
    setDetails(updated);
  };

  const handleFromDateChange = (value) => {
    setFromDate(value);
    setDetails((currentDetails) => currentDetails.map((detail) => ({ ...detail, recorded_date: value })));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setAlertState(null);

    if (!contract || !fromDate || !toDate) {
      setAlertState({
        type: "error",
        title: "Thiếu thông tin bắt buộc",
        message: "Vui lòng chọn hợp đồng và nhập đầy đủ khoảng thời gian trước khi lưu.",
      });
      return;
    }

    if (new Date(fromDate) > new Date(toDate)) {
      setAlertState({
        type: "error",
        title: "Khoảng thời gian không hợp lệ",
        message: "Ngày bắt đầu không được lớn hơn ngày kết thúc.",
      });
      return;
    }

    // Check contract date validity
    if (contract) {
      const pFrom = new Date(fromDate);
      const pTo = new Date(toDate);
      const cFrom = new Date(contract.valid_from);
      const cTo = new Date(contract.valid_to);

      if (pFrom < cFrom || pTo > cTo) {
        setAlertState({
          type: "invalid_date",
          title: "Khoảng thời gian không hợp lệ",
          message: `Khoảng thời gian tính phí bạn nhập nằm ngoài thời hạn hiệu lực của hợp đồng (${contract.valid_from} đến ${contract.valid_to}). Vui lòng kiểm tra lại.`,
        });
        return;
      }
    }

    setIsSubmitting(true);
    try {
      // Check overlap API
      const overlapRes = await productionApi.checkOverlap({
        customer_id: contract.customer_id,
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
        customer_id: contract.customer_id,
        contract_id: selectedContractId,
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
        message: `Kỳ sản lượng ${created.period_name || created.id} đã được ghi nhận vào hệ thống ở trạng thái Bản nháp (DRAFT). Bạn có thể xem lại hoặc chỉnh sửa sau này.`,
        createdId: created.id,
      });
    } catch (err) {
      setAlertState({
        type: "error",
        title: "Không thể tạo kỳ sản lượng",
        message: err.message || "Vui lòng kiểm tra lại dữ liệu và thử lại.",
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className={pageMode ? "production-create-page" : "modal-overlay"}>
      <div className={`modal-content${pageMode ? " production-create-card" : ""}`}>
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
              {/* General Info Grid */}
              <div className="form-grid">
                <div className="form-group">
                  <label>
                    <FileText size={14} style={{ display: "inline", marginRight: "4px" }} />
                    Hợp đồng áp dụng <span className="required">*</span>
                  </label>
                  <select
                    className="form-control"
                    value={selectedContractId}
                    onChange={(e) => setSelectedContractId(e.target.value)}
                    required
                  >
                    <option value="">-- Chọn hợp đồng --</option>
                    {contracts.map((item) => (
                      <option key={item.contract_id} value={item.contract_id}>
                        {item.contract_id} — {item.customer_name}
                      </option>
                    ))}
                  </select>
                  {isContractsLoading && <small>Đang tải hợp đồng từ hệ thống...</small>}
                  {!isContractsLoading && contracts.length === 0 && !contractsError && <small>Chưa có hợp đồng hiệu lực để khai báo sản lượng.</small>}
                  {contractsError && <small className="form-error">{contractsError}</small>}
                </div>

                <div className="form-group">
                  <label>
                    <Building size={14} style={{ display: "inline", marginRight: "4px" }} />
                    Khách hàng
                  </label>
                  <input
                    className="form-control"
                    type="text"
                  value={contract?.customer_name ?? ""}
                    placeholder="Tự động điền theo hợp đồng"
                    readOnly
                  />
                </div>

                <div className="form-group full-width">
                  <label>Mã kỳ sản lượng</label>
                  <input
                    className="form-control"
                    type="text"
                    value={contract ? `SL-${contract.contract_id.match(/20\d{2}/)?.[0] || "YYYY"}-XXX` : ""}
                    placeholder="Tự động tạo sau khi lưu"
                    readOnly
                  />
                  <small>Hệ thống tạo mã theo năm trong mã hợp đồng và số thứ tự kỳ cùng năm.</small>
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
                    onChange={(e) => handleFromDateChange(e.target.value)}
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
                  <button className="btn-action secondary" type="button" onClick={handleAddRow} disabled={!contractServices.length}>
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
                              {contractServices.map((service) => (
                                <option key={service.service_id} value={String(service.service_id)}>
                                  {service.service_name}
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

        {alertState && alertState.type !== "success" && (
          <div className={`alert-box ${alertState.type === "overlap" ? "warning" : "danger"} form-footer-alert`}>
            <AlertTriangle size={24} className="alert-icon" />
            <div className="alert-body">
              <h4>{alertState.title}</h4>
              <p>{alertState.message}</p>
            </div>
          </div>
        )}

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
