import { Edit3, FileText, Info, Send, X } from "lucide-react";
import { useNavigate } from "react-router-dom";

import { DataState } from "../../../shared/components/DataState.jsx";
import { StatusBadge } from "../../../shared/components/StatusBadge.jsx";
import { useContractDetail } from "../hooks/useContractDetail";
import { useSubmitContract } from "../hooks/useSubmitContract";

import {
  formatContractCurrency,
  formatContractDate,
  formatUpdatedAt,
  getContractLineTotal,
  getStatusMeta,
} from "./contractDisplay";

export function ContractDetailModal({ contractId, onClose }) {
  const navigate = useNavigate();
  const { data: contract, isLoading, isError, error } = useContractDetail(contractId);
  const submitContract = useSubmitContract();
  const status = getStatusMeta(contract?.status);
  const canEditDraft = contract?.status === "DRAFT";

  function handleEdit() {
    onClose();
    navigate(`/contracts/${contractId}/edit`);
  }

  return (
    <div className="contract-modal-backdrop" role="presentation" onMouseDown={onClose}>
      <section
        className="contract-detail-modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="contract-detail-title"
        onMouseDown={(event) => event.stopPropagation()}
      >
        <header className="contract-modal-header">
          <div className="contract-modal-title">
            <span className="contract-modal-icon">
              <FileText size={26} />
            </span>
            <div>
              <h2 id="contract-detail-title">Hợp đồng {contractId}</h2>
              <p>Cập nhật lần cuối: {formatUpdatedAt(contract?.updated_at)}</p>
            </div>
            {contract?.status ? (
              <StatusBadge tone={status.tone}>{status.detailLabel}</StatusBadge>
            ) : null}
          </div>
          <button className="contract-icon-button" type="button" aria-label="Đóng" onClick={onClose}>
            <X size={24} />
          </button>
        </header>

        <div className="contract-modal-body">
          {isLoading ? <DataState title="Đang tải hợp đồng" /> : null}
          {isError ? (
            <DataState
              title="Không tải được hợp đồng"
              description={error?.message ?? "Vui lòng thử lại sau."}
            />
          ) : null}
          {contract ? (
            <>
              <section className="contract-detail-section">
                <h3>Thông tin chung</h3>
                <div className="contract-info-card">
                  <div>
                    <span>Khách hàng</span>
                    <strong>{contract.customer_name}</strong>
                  </div>
                  <div>
                    <span>Ngày bắt đầu</span>
                    <strong>{formatContractDate(contract.valid_from)}</strong>
                  </div>
                  <div>
                    <span>Ngày hết hạn</span>
                    <strong className="contract-expiry">
                      {formatContractDate(contract.valid_to)}
                    </strong>
                  </div>
                </div>
              </section>

              <section className="contract-detail-section">
                <h3>Chi tiết dịch vụ</h3>
                <div className="contract-service-table">
                  <table>
                    <thead>
                      <tr>
                        <th>Loại dịch vụ</th>
                        <th>Số lượng</th>
                        <th>Đơn vị</th>
                        <th>Đơn giá</th>
                        <th>Thành tiền</th>
                      </tr>
                    </thead>
                    <tbody>
                      {contract.services.map((service) => (
                        <tr key={service.id}>
                          <td>{service.service_name}</td>
                          <td>
                            <strong>{service.quantity}</strong>
                          </td>
                          <td>{service.service_unit}</td>
                          <td>{formatContractCurrency(service.service_price)} đ</td>
                          <td>
                            <strong>{formatContractCurrency(getContractLineTotal(service))} đ</strong>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </section>

              <section className="contract-total-panel">
                <p>Điều khoản: {contract.payment_terms}</p>
                <div>
                  <span>Tổng giá trị hợp đồng</span>
                  <strong>{formatContractCurrency(contract.total_value)} đ</strong>
                </div>
              </section>
              {submitContract.isError ? (
                <p className="contract-create-error">
                  {submitContract.error?.message ?? "Không gửi duyệt được hợp đồng."}
                </p>
              ) : null}
            </>
          ) : null}
        </div>

        <footer className="contract-modal-footer">
          <span>
            <Info size={16} />
            Hợp đồng này được lưu trữ theo tiêu chuẩn ISO 27001.
          </span>
          <div>
            <button className="button secondary" type="button" onClick={onClose}>
              Hủy bỏ
            </button>
            {canEditDraft ? (
              <button className="button secondary" type="button" onClick={handleEdit}>
                <Edit3 size={16} />
                Chỉnh sửa
              </button>
            ) : null}
            <button
              className="button"
              type="button"
              disabled={!canEditDraft || submitContract.isPending}
              onClick={() => submitContract.mutate(contract.contract_id)}
            >
              <Send size={16} />
              Gửi duyệt
            </button>
          </div>
        </footer>
      </section>
    </div>
  );
}
