import { PlusCircle, X } from "lucide-react";
import { useState } from "react";

import { useContractServiceCatalog } from "../hooks/useContractServiceCatalog";
import { formatContractCurrency } from "./contractDisplay";

export function AddContractServiceModal({ disabledServiceIds, onAdd, onClose }) {
  const [serviceId, setServiceId] = useState("");
  const [quantity, setQuantity] = useState(1);
  const catalog = useContractServiceCatalog();
  const selectedServiceId = serviceId ? Number(serviceId) : null;
  const services = Array.isArray(catalog.data) ? catalog.data : [];
  const selectedService = services.find((service) => service.id === selectedServiceId);
  const isCatalogUnavailable = catalog.isLoading || catalog.isError || services.length === 0;
  const canAdd = Boolean(selectedService && Number(quantity) > 0);

  function getPlaceholderLabel() {
    if (catalog.isLoading) {
      return "Đang tải dịch vụ...";
    }

    if (catalog.isError) {
      return "Không tải được dịch vụ";
    }

    if (services.length === 0) {
      return "Chưa có dịch vụ trong bảng giá hiện hành";
    }

    return "Chọn dịch vụ từ bảng giá hiện hành...";
  }

  function handleSubmit(event) {
    event.preventDefault();

    if (!canAdd) {
      return;
    }

    onAdd({
      service_id: selectedService.id,
      service_name: selectedService.name,
      service_unit: selectedService.unit,
      service_price: selectedService.unit_price,
      quantity: Number(quantity),
    });
  }

  return (
    <div className="contract-create-modal-backdrop" role="presentation" onMouseDown={onClose}>
      <form
        className="contract-add-service-modal"
        onSubmit={handleSubmit}
        onMouseDown={(event) => event.stopPropagation()}
      >
        <header>
          <h2>
            <PlusCircle size={18} />
            Thêm dịch vụ mới
          </h2>
          <button type="button" aria-label="Đóng" onClick={onClose}>
            <X size={20} />
          </button>
        </header>

        <label>
          <span>Chọn dịch vụ *</span>
          <select
            value={serviceId}
            disabled={isCatalogUnavailable}
            onChange={(event) => setServiceId(event.target.value)}
          >
            <option value="">{getPlaceholderLabel()}</option>
            {services.map((service) => (
              <option
                key={service.id}
                value={service.id}
                disabled={disabledServiceIds.includes(service.id)}
              >
                {service.name}
              </option>
            ))}
          </select>
        </label>

        <label>
          <span>Số lượng *</span>
          <input
            min="1"
            type="number"
            value={quantity}
            onChange={(event) => setQuantity(event.target.value)}
          />
        </label>

        <div className="contract-price-preview">
          {catalog.isError ? (
            <span>
              Không tải được bảng giá hiện hành. Hãy đăng nhập lại hoặc kiểm tra Price Service.
            </span>
          ) : null}
          {selectedService ? (
            <span>
              Đơn giá áp dụng:{" "}
              <strong>
                {formatContractCurrency(selectedService.unit_price)} VND / {selectedService.unit}
              </strong>
            </span>
          ) : null}
        </div>

        <footer>
          <button className="button secondary" type="button" onClick={onClose}>
            Hủy bỏ
          </button>
          <button className="button" type="submit" disabled={!canAdd}>
            Thêm vào hợp đồng
          </button>
        </footer>
      </form>
    </div>
  );
}
