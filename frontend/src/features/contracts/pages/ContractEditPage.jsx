import { useEffect, useMemo, useState } from "react";
import { ArrowLeft, Save, Send } from "lucide-react";
import { useNavigate, useParams } from "react-router-dom";

import { DataState } from "../../../shared/components/DataState.jsx";
import { usePageTitle } from "../../../shared/hooks/usePageTitle";
import { AddContractServiceModal } from "../components/AddContractServiceModal.jsx";
import { ContractCreateCustomerCard } from "../components/ContractCreateCustomerCard.jsx";
import { ContractCreateTermCard } from "../components/ContractCreateTermCard.jsx";
import { ContractServiceLinesTable } from "../components/ContractServiceLinesTable.jsx";
import {
  formatIsoDateToDisplay,
  getLocalTodayIso,
  parseDisplayDateToIso,
} from "../components/contractFormUtils";
import {
  formatContractCurrency,
  getContractLineTotal,
} from "../components/contractDisplay";
import { fakeCustomers } from "../data/fakeCustomers";
import { useContractDetail } from "../hooks/useContractDetail";
import { useContractServiceCatalog } from "../hooks/useContractServiceCatalog";
import { useSubmitContract } from "../hooks/useSubmitContract";
import { useUpdateContract } from "../hooks/useUpdateContract";
import "../contracts.css";

const initialForm = {
  validFrom: "",
  validTo: "",
  paymentTerms: "",
};

function buildUpdatePayload(form, serviceLines) {
  return {
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

  if (serviceLines.some((line) => !line.service_id)) {
    return "Không xác định được mã dịch vụ từ danh mục Price Service. Vui lòng tải lại trang.";
  }

  return null;
}

function mapContractServices(contractServices, catalogServices) {
  return contractServices.map((service) => {
    const catalogService = catalogServices.find((item) => item.name === service.service_name);

    return {
      service_id: catalogService?.id ?? null,
      service_name: service.service_name,
      service_unit: service.service_unit,
      service_price: service.service_price,
      quantity: service.quantity,
    };
  });
}

export function ContractEditPage() {
  const { contractId } = useParams();
  usePageTitle(`Edit ${contractId ?? "Contract"}`);

  const navigate = useNavigate();
  const contractDetail = useContractDetail(contractId);
  const catalog = useContractServiceCatalog();
  const updateContract = useUpdateContract(contractId);
  const submitContract = useSubmitContract();
  const [form, setForm] = useState(initialForm);
  const [serviceLines, setServiceLines] = useState([]);
  const [isAddServiceOpen, setIsAddServiceOpen] = useState(false);
  const [formError, setFormError] = useState("");
  const [isInitialized, setIsInitialized] = useState(false);
  const contract = contractDetail.data;
  const catalogServices = useMemo(
    () => (Array.isArray(catalog.data) ? catalog.data : []),
    [catalog.data],
  );
  const selectedCustomer = useMemo(() => {
    if (!contract) {
      return null;
    }

    return (
      fakeCustomers.find((customer) => customer.name === contract.customer_name) ?? {
        id: contract.customer_name,
        name: contract.customer_name,
        taxCode: "-",
        customerType: "-",
      }
    );
  }, [contract]);
  const customerOptions = useMemo(() => {
    if (
      !selectedCustomer ||
      fakeCustomers.some((customer) => customer.id === selectedCustomer.id)
    ) {
      return fakeCustomers;
    }

    return [selectedCustomer, ...fakeCustomers];
  }, [selectedCustomer]);
  const totalValue = serviceLines.reduce(
    (sum, line) => sum + getContractLineTotal(line),
    0,
  );
  const disabledServiceIds = useMemo(
    () => serviceLines.map((line) => line.service_id).filter(Boolean),
    [serviceLines],
  );
  const isSaving = updateContract.isPending || submitContract.isPending;
  const mutationError = updateContract.error?.message || submitContract.error?.message;

  useEffect(() => {
    if (!contract || catalog.isLoading || catalog.isError || isInitialized) {
      return;
    }

    setForm({
      validFrom: formatIsoDateToDisplay(contract.valid_from),
      validTo: formatIsoDateToDisplay(contract.valid_to),
      paymentTerms: contract.payment_terms,
    });
    setServiceLines(mapContractServices(contract.services, catalogServices));
    setIsInitialized(true);
  }, [catalog.isError, catalog.isLoading, catalogServices, contract, isInitialized]);

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

  async function saveChanges({ submitAfterSave = false } = {}) {
    const validationError = validateForm(form, serviceLines);
    if (validationError) {
      setFormError(validationError);
      return;
    }

    try {
      await updateContract.mutateAsync(buildUpdatePayload(form, serviceLines));

      if (submitAfterSave) {
        await submitContract.mutateAsync(contractId);
      }

      navigate("/contracts");
    } catch {
      return;
    }
  }

  if (contractDetail.isLoading || catalog.isLoading) {
    return <DataState title="Đang tải hợp đồng" />;
  }

  if (contractDetail.isError) {
    return (
      <DataState
        title="Không tải được hợp đồng"
        description={contractDetail.error?.message ?? "Vui lòng thử lại sau."}
      />
    );
  }

  if (catalog.isError) {
    return (
      <DataState
        title="Không tải được danh mục dịch vụ"
        description={catalog.error?.message ?? "Vui lòng đăng nhập lại hoặc kiểm tra Price Service."}
      />
    );
  }

  if (contract?.status !== "DRAFT") {
    return (
      <DataState
        title="Không thể chỉnh sửa hợp đồng"
        description="Chỉ hợp đồng ở trạng thái DRAFT mới được chỉnh sửa."
      />
    );
  }

  return (
    <div className="contract-create-page">
      <header className="contract-create-header">
        <button className="contract-back-button" type="button" onClick={() => navigate("/contracts")}>
          <ArrowLeft size={18} />
        </button>
        <h1>Chỉnh sửa Hợp đồng {contractId}</h1>
      </header>

      <div className="contract-create-grid">
        <ContractCreateCustomerCard
          customers={customerOptions}
          selectedCustomerId={selectedCustomer?.id ?? ""}
          selectedCustomer={selectedCustomer}
          disabled
          onChange={() => {}}
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
        <p>Các thay đổi chỉ áp dụng cho hợp đồng đang ở trạng thái bản nháp.</p>
        <div>
          <button className="button secondary" type="button" onClick={() => navigate("/contracts")}>
            Hủy bỏ
          </button>
          <button
            className="button secondary"
            type="button"
            disabled={isSaving}
            onClick={() => saveChanges()}
          >
            <Save size={16} />
            Lưu thay đổi
          </button>
          <button
            className="button"
            type="button"
            disabled={isSaving}
            onClick={() => saveChanges({ submitAfterSave: true })}
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
