import { PlusCircle, X } from "lucide-react";
import { useState } from "react";

import {
  useContractServiceCatalog,
  useEffectiveServicePrice,
} from "../hooks/useContractServiceCatalog";
import { formatContractCurrency } from "./contractDisplay";

export function AddContractServiceModal({ disabledServiceIds, onAdd, onClose }) {
  const [serviceId, setServiceId] = useState("");
  const [quantity, setQuantity] = useState(1);
  const catalog = useContractServiceCatalog();
  const selectedServiceId = serviceId ? Number(serviceId) : null;
  const price = useEffectiveServicePrice(selectedServiceId);
  const services = Array.isArray(catalog.data) ? catalog.data : [];
  const activeServices = services.filter((service) => service.is_active);
  const selectedService = activeServices.find((service) => service.id === selectedServiceId);
  const isCatalogUnavailable = catalog.isLoading || catalog.isError || activeServices.length === 0;
  const canAdd = Boolean(selectedService && price.data && Number(quantity) > 0);

  function getPlaceholderLabel() {
    if (catalog.isLoading) {
      return "Đang tải dịch vụ...";
    }

    if (catalog.isError) {
      return "Không tải được dịch vụ";
    }

    if (activeServices.length === 0) {
      return "Chưa có dịch vụ đang hoạt động";
    }

    return "Chọn dịch vụ từ danh mục...";
  }

  function handleSubmit(event) {
    event.preventDefault();

    if (!canAdd) {
      return;
    }

    onAdd({
      service_id: selectedService.id,
      service_name: price.data.service_name,
      service_unit: price.data.unit,
      service_price: price.data.unit_price,
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
            {activeServices.map((service) => (
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
              Không tải được danh mục dịch vụ. Hãy đăng nhập lại hoặc kiểm tra Price Service.
            </span>
          ) : null}
          {price.isFetching ? <span>Đang lấy đơn giá hiệu lực...</span> : null}
          {price.isError ? (
            <span>Không tìm thấy đơn giá hiệu lực cho dịch vụ này.</span>
          ) : null}
          {price.data ? (
            <span>
              Đơn giá áp dụng:{" "}
              <strong>
                {formatContractCurrency(price.data.unit_price)} VND / {price.data.unit}
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
