import { useMemo, useState } from "react";
import { ArrowLeft, Send, Save } from "lucide-react";
import { useNavigate } from "react-router-dom";

import { usePageTitle } from "../../../shared/hooks/usePageTitle";
import { AddContractServiceModal } from "../components/AddContractServiceModal.jsx";
import { ContractCreateCustomerCard } from "../components/ContractCreateCustomerCard.jsx";
import { ContractCreateTermCard } from "../components/ContractCreateTermCard.jsx";
import { ContractServiceLinesTable } from "../components/ContractServiceLinesTable.jsx";
import {
  getLocalTodayIso,
  parseDisplayDateToIso,
} from "../components/contractFormUtils";
import {
  formatContractCurrency,
  getContractLineTotal,
} from "../components/contractDisplay";
import { fakeCustomers } from "../data/fakeCustomers";
import { useCreateContract } from "../hooks/useCreateContract";
import { useSubmitContract } from "../hooks/useSubmitContract";
import "../contracts.css";

const initialForm = {
  customerId: "",
  validFrom: "",
  validTo: "",
  paymentTerms: "",
};

function buildPayload(form, serviceLines) {
  return {
    customer_id: form.customerId,
    valid_from: parseDisplayDateToIso(form.validFrom),
    valid_to: parseDisplayDateToIso(form.validTo),
    payment_terms: form.paymentTerms.trim(),
    services: serviceLines.map((line) => ({
      service_id: line.service_id,
      quantity: line.quantity,
    })),
  };
}

function validateForm(form, serviceLines) {
  const validFrom = parseDisplayDateToIso(form.validFrom);
  const validTo = parseDisplayDateToIso(form.validTo);

  if (!form.customerId) {
    return "Vui lòng chọn khách hàng.";
  }

  if (!validFrom || !validTo) {
    return "Ngày hiệu lực và ngày hết hạn phải theo định dạng dd/mm/yyyy.";
  }

  if (validFrom <= getLocalTodayIso()) {
    return "Ngày hiệu lực phải lớn hơn ngày hiện tại.";
  }

  if (validTo < validFrom) {
    return "Ngày hết hạn phải lớn hơn hoặc bằng ngày hiệu lực.";
  }

  if (!form.paymentTerms.trim()) {
    return "Vui lòng nhập điều khoản thanh toán.";
  }

  if (serviceLines.length === 0) {
    return "Vui lòng thêm ít nhất một dịch vụ.";
  }

  return null;
}

export function ContractCreatePage() {
  usePageTitle("Create Contract");

  const navigate = useNavigate();
  const createContract = useCreateContract();
  const submitContract = useSubmitContract();
  const [form, setForm] = useState(initialForm);
  const [serviceLines, setServiceLines] = useState([]);
  const [isAddServiceOpen, setIsAddServiceOpen] = useState(false);
  const [formError, setFormError] = useState("");
  const selectedCustomer = fakeCustomers.find((customer) => customer.id === form.customerId);
  const totalValue = serviceLines.reduce(
    (sum, line) => sum + getContractLineTotal(line),
    0,
  );
  const disabledServiceIds = useMemo(
    () => serviceLines.map((line) => line.service_id),
    [serviceLines],
  );
  const isSaving = createContract.isPending || submitContract.isPending;
  const mutationError = createContract.error?.message || submitContract.error?.message;

  function updateForm(nextForm) {
    setForm((currentForm) => ({ ...currentForm, ...nextForm }));
    setFormError("");
  }

  function addServiceLine(line) {
    setServiceLines((currentLines) => [...currentLines, line]);
    setIsAddServiceOpen(false);
    setFormError("");
  }

  function removeServiceLine(serviceId) {
    setServiceLines((currentLines) =>
      currentLines.filter((line) => line.service_id !== serviceId),
    );
  }

  async function saveContract({ submitAfterCreate = false } = {}) {
    const validationError = validateForm(form, serviceLines);
    if (validationError) {
      setFormError(validationError);
      return;
    }

    try {
      const createdContract = await createContract.mutateAsync(buildPayload(form, serviceLines));

      if (submitAfterCreate) {
        await submitContract.mutateAsync(createdContract.id);
      }

      navigate("/contracts");
    } catch {
      return;
    }
  }

  return (
    <div className="contract-create-page">
      <header className="contract-create-header">
        <button className="contract-back-button" type="button" onClick={() => navigate("/contracts")}>
          <ArrowLeft size={18} />
        </button>
        <h1>Lập hồ sơ Hợp đồng mới</h1>
      </header>

      <div className="contract-create-grid">
        <ContractCreateCustomerCard
          customers={fakeCustomers}
          selectedCustomerId={form.customerId}
          selectedCustomer={selectedCustomer}
          onChange={(customerId) => updateForm({ customerId })}
        />
        <ContractCreateTermCard
          validFrom={form.validFrom}
          validTo={form.validTo}
          paymentTerms={form.paymentTerms}
          onChange={updateForm}
        />
      </div>

      <ContractServiceLinesTable
        lines={serviceLines}
        onAddService={() => setIsAddServiceOpen(true)}
        onRemoveService={removeServiceLine}
      />

      {(formError || mutationError) ? (
        <p className="contract-create-error">{formError || mutationError}</p>
      ) : null}

      <footer className="contract-create-footer">
        <span>Tổng giá trị: {formatContractCurrency(totalValue)} VND</span>
        <p>Vui lòng kiểm tra kỹ các thông tin trước khi gửi duyệt.</p>
        <div>
          <button className="button secondary" type="button" onClick={() => navigate("/contracts")}>
            Hủy bỏ
          </button>
          <button
            className="button secondary"
            type="button"
            disabled={isSaving}
            onClick={() => saveContract()}
          >
            <Save size={16} />
            Lưu bản nháp
          </button>
          <button
            className="button"
            type="button"
            disabled={isSaving}
            onClick={() => saveContract({ submitAfterCreate: true })}
          >
            <Send size={16} />
            Gửi duyệt
          </button>
        </div>
      </footer>

      {isAddServiceOpen ? (
        <AddContractServiceModal
          disabledServiceIds={disabledServiceIds}
          onAdd={addServiceLine}
          onClose={() => setIsAddServiceOpen(false)}
        />
      ) : null}
    </div>
  );
}
