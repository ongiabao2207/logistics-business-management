import { Users } from "lucide-react";

export function ContractCreateCustomerCard({
  customers,
  selectedCustomerId,
  selectedCustomer,
  onChange,
  disabled = false,
}) {
  return (
    <section className="contract-create-card">
      <h2>
        <Users size={20} />
        Thông tin Khách hàng
      </h2>
      <label>
        <span>Chọn Khách hàng *</span>
        <select
          value={selectedCustomerId}
          disabled={disabled}
          onChange={(event) => onChange(event.target.value)}
        >
          <option value="">-- Tìm kiếm khách hàng --</option>
          {customers.map((customer) => (
            <option key={customer.id} value={customer.id}>
              {customer.name}
            </option>
          ))}
        </select>
      </label>
      <div className="contract-customer-note">
        {selectedCustomer ? (
          <>
            <strong>{selectedCustomer.name}</strong>
            <span>MST: {selectedCustomer.taxCode}</span>
            <span>Nhóm: {selectedCustomer.customerType}</span>
          </>
        ) : (
          <em>Thông tin doanh nghiệp, mã số thuế và địa chỉ sẽ được tự động trích xuất sau khi chọn khách hàng.</em>
        )}
      </div>
    </section>
  );
}
