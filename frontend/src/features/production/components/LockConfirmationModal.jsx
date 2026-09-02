import React, { useState } from "react";
import { Lock, AlertTriangle, X } from "lucide-react";
import { productionApi } from "../api/productionApi";

export function LockConfirmationModal({ isOpen, period, onClose, onSuccess }) {
  const [isLocking, setIsLocking] = useState(false);

  if (!isOpen || !period) return null;

  const handleLock = async () => {
    setIsLocking(true);
    try {
      await productionApi.lockProductionPeriod(period.id, "Nguyễn Hoàng Uyển Như");
      onSuccess();
      onClose();
    } catch (err) {
      alert(`Khóa kỳ thất bại: ${err.message || "Lỗi hệ thống"}`);
    } finally {
      setIsLocking(false);
    }
  };

  return (
    <div className="modal-overlay">
      <div className="modal-content" style={{ maxWidth: "520px" }}>
        <div className="modal-header">
          <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
            <div style={{ background: "#fef3c7", color: "#d97706", padding: "8px", borderRadius: "8px" }}>
              <Lock size={20} />
            </div>
            <div>
              <h2>Xác nhận Khóa kỳ sản lượng</h2>
            </div>
          </div>
          <button className="btn-close" type="button" onClick={onClose}>
            <X size={20} />
          </button>
        </div>

        <div className="modal-body">
          <p style={{ margin: "0 0 16px", fontSize: "14px", color: "#334155", lineHeight: "1.5" }}>
            Bạn có chắc chắn muốn khóa kỳ sản lượng này? Sau khi khóa, dữ liệu sẽ không thể chỉnh sửa và trạng thái sẽ chuyển thành <strong>Đã khóa (Locked)</strong> để phục vụ tính tiền.
          </p>

          <div style={{ background: "#f8fafc", border: "1px solid #e2e8f0", borderRadius: "10px", padding: "14px 16px", marginBottom: "16px" }}>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "10px", fontSize: "13px" }}>
              <div>
                <span style={{ color: "#64748b", display: "block" }}>MÃ KỲ SẢN LƯỢNG</span>
                <strong style={{ color: "#0f172a" }}>SL-{period.id}</strong>
              </div>
              <div>
                <span style={{ color: "#64748b", display: "block" }}>TRẠNG THÁI HIỆN TẠI</span>
                <span className="badge-status draft">Soạn thảo (Draft)</span>
              </div>
              <div style={{ gridColumn: "span 2" }}>
                <span style={{ color: "#64748b", display: "block" }}>KHÁCH HÀNG</span>
                <strong style={{ color: "#0f172a" }}>{period.customer_name || period.customer_id}</strong>
              </div>
            </div>
          </div>

          <div className="alert-box danger" style={{ margin: 0, padding: "12px 14px" }}>
            <AlertTriangle size={20} className="alert-icon" />
            <div className="alert-body">
              <h4 style={{ fontSize: "13px" }}>Lưu ý quan trọng</h4>
              <p style={{ fontSize: "12px" }}>
                Hành động này không thể hoàn tác trực tiếp. Vui lòng đối soát kỹ số liệu sản lượng trước khi thực hiện.
              </p>
            </div>
          </div>
        </div>

        <div className="modal-footer">
          <button className="btn-action secondary" type="button" onClick={onClose} disabled={isLocking}>
            Hủy
          </button>
          <button className="btn-action lock" type="button" onClick={handleLock} disabled={isLocking}>
            <Lock size={14} />
            {isLocking ? "Đang khóa..." : "Đồng ý khóa kỳ"}
          </button>
        </div>
      </div>
    </div>
  );
}
