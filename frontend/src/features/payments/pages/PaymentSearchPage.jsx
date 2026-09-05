import { CalendarDays, CheckCircle2, Info, Search } from "lucide-react";
import { useMemo, useState } from "react";
import { Link } from "react-router-dom";

import { PaymentBreadcrumb } from "../components/PaymentBreadcrumb.jsx";
import { PaymentState } from "../components/PaymentState.jsx";
import { usePaymentContracts } from "../hooks/usePaymentContracts.js";
import { usePaymentProductionPeriods } from "../hooks/usePaymentProductionPeriods.js";
import { usePayments } from "../hooks/usePayments.js";

function paymentKey(contractId, periodStart, periodEnd) {
  return `${contractId}:${periodStart}:${periodEnd}`;
}

function formatPeriodDate(value) {
  return new Intl.DateTimeFormat("vi-VN", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    timeZone: "UTC",
  }).format(new Date(value));
}

export function PaymentSearchPage() {
  const [keyword, setKeyword] = useState("");
  const productionQuery = usePaymentProductionPeriods();
  const paymentsQuery = usePayments({ offset: 0, limit: 200 });
  const { getCustomerName } = usePaymentContracts();

  const existingPayments = useMemo(
    () => new Map((paymentsQuery.data ?? []).map((payment) => [
      paymentKey(payment.contract_id, payment.period_start, payment.period_end),
      payment,
    ])),
    [paymentsQuery.data],
  );

  const periods = useMemo(() => {
    const normalizedKeyword = keyword.trim().toLowerCase();

    return (productionQuery.data ?? [])
      .map((period) => ({
        ...period,
        customerName: getCustomerName(period.contract_id, period.customer_id),
        existingPayment: existingPayments.get(paymentKey(
          period.contract_id,
          period.from_date,
          period.to_date,
        )),
      }))
      .filter((period) => !normalizedKeyword || [
        period.period_name,
        period.contract_id,
        period.customer_id,
        period.customerName,
        period.from_date,
        period.to_date,
      ].some((value) => String(value ?? "").toLowerCase().includes(normalizedKeyword)))
      .sort((left, right) => (
        right.from_date.localeCompare(left.from_date)
        || right.to_date.localeCompare(left.to_date)
        || Number(right.id) - Number(left.id)
      ));
  }, [existingPayments, getCustomerName, keyword, productionQuery.data]);

  const isPending = productionQuery.isPending || paymentsQuery.isPending;
  const error = productionQuery.error ?? paymentsQuery.error;

  return (
    <>
      <PaymentBreadcrumb items={[{ label: "Lập bảng thanh toán" }]} />

      <div className="pay-intro">
        <h2>Chọn kỳ sản lượng đã khóa</h2>
        <p>
          Mỗi kỳ được hiển thị theo đúng ngày bắt đầu và ngày kết thúc đã tạo
          bên Production Service, không quy đổi thành tháng.
        </p>
      </div>

      <section className="pay-search-period pay-locked-period-search">
        <label className="pay-field search">
          <span>Tìm kỳ sản lượng</span>
          <div>
            <Search size={17} />
            <input
              type="search"
              value={keyword}
              onChange={(event) => setKeyword(event.target.value)}
              placeholder="Tìm theo tên kỳ, khách hàng hoặc hợp đồng"
            />
          </div>
        </label>

        <div className="pay-locked-period-note">
          <Info size={18} />
          Chỉ các kỳ có trạng thái Đã khóa mới đủ điều kiện lập bảng thanh toán.
        </div>
      </section>

      {isPending ? <PaymentState title="Đang tải các kỳ sản lượng đã khóa..." /> : null}
      {error ? (
        <PaymentState
          title="Không thể tải kỳ sản lượng"
          description={error.message}
        />
      ) : null}
      {!isPending && !error && !periods.length ? (
        <PaymentState
          title="Không có kỳ sản lượng phù hợp"
          description="Production Service chưa có kỳ đã khóa hoặc không có kỳ khớp nội dung tìm kiếm."
        />
      ) : null}

      {periods.length ? (
        <section className="pay-panel pay-locked-period-panel">
          <div className="pay-table-scroll">
            <table className="pay-table pay-locked-period-table">
              <thead>
                <tr>
                  <th>Kỳ sản lượng</th>
                  <th>Khách hàng</th>
                  <th>Hợp đồng</th>
                  <th>Khoảng thời gian</th>
                  <th>Trạng thái</th>
                  <th>Thao tác</th>
                </tr>
              </thead>
              <tbody>
                {periods.map((period) => {
                  const createUrl = [
                    "/payments/new?",
                    `customer_id=${encodeURIComponent(period.customer_id)}`,
                    `&contract_id=${encodeURIComponent(period.contract_id)}`,
                    `&period_start=${period.from_date}`,
                    `&period_end=${period.to_date}`,
                  ].join("");

                  return (
                    <tr key={period.id}>
                      <td><strong>{period.period_name || `Kỳ #${period.id}`}</strong></td>
                      <td>{period.customerName}</td>
                      <td><strong className="blue-text">{period.contract_id}</strong></td>
                      <td>
                        <span className="pay-period-range">
                          <CalendarDays size={16} />
                          {formatPeriodDate(period.from_date)} – {formatPeriodDate(period.to_date)}
                        </span>
                      </td>
                      <td>
                        <span className="mini-status ok">
                          <CheckCircle2 size={14} />Đã khóa
                        </span>
                      </td>
                      <td>
                        {period.existingPayment ? (
                          <Link
                            className="pay-button small outline"
                            to={`/payments/${period.existingPayment.id}`}
                          >
                            Xem bảng {period.existingPayment.id}
                          </Link>
                        ) : (
                          <Link className="pay-button small primary" to={createUrl}>
                            Lập bảng
                          </Link>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </section>
      ) : null}
    </>
  );
}
