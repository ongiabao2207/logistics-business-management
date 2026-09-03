import {
  AlertCircle,
  CheckCircle2,
  Clock3,
  Eye,
  Filter,
  Pencil,
  PlusCircle,
  Search,
  Send,
  WalletCards,
} from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";

import { usePageTitle } from "../../../shared/hooks/usePageTitle.js";
import { formatDate } from "../../../shared/utils/formatters.js";
import { ROLES } from "../../identity/constants/permissions.js";
import { useAuth } from "../../identity/hooks/useAuth.js";
import { PaymentState } from "../components/PaymentState.jsx";
import { PaymentStatus } from "../components/PaymentStatus.jsx";
import { usePaymentContracts } from "../hooks/usePaymentContracts.js";
import { usePayments } from "../hooks/usePayments.js";
import { paymentStatusLabels } from "../types/index.js";

export function PaymentListPage() {
  usePageTitle("Quản lý Bảng thanh toán");
  const { user } = useAuth();
  const canManage = user?.role === ROLES.ACCOUNTANT;

  const [params, setParams] = useSearchParams();
  const [keyword, setKeyword] = useState("");
  const [page, setPage] = useState(1);
  const pageSize = 5;

  const status = params.get("status") ?? "";
  const year = params.get("year") ?? "";
  const month = params.get("month") ?? "";

  const {
    data: payments = [],
    isPending,
    error,
  } = usePayments();
  const { getCustomerName } = usePaymentContracts();

  const yearOptions = useMemo(() => {
    const years = new Set(payments.map((item) => (
      String(new Date(item.period_start).getFullYear())
    )));
    return [...years].sort((left, right) => Number(right) - Number(left));
  }, [payments]);

  const rows = useMemo(() => {
    const normalizedKeyword = keyword.trim().toLowerCase();

    return payments.map((item) => ({
      ...item,
      customer_name: getCustomerName(item.contract_id, item.customer_id),
    })).filter((item) => {
      const matchesStatus = !status || item.status === status;
      const itemDate = new Date(item.period_start);
      const matchesYear = !year || String(itemDate.getFullYear()) === year;
      const matchesMonth = !month || String(itemDate.getMonth() + 1) === month;

      const matchesKeyword =
        !normalizedKeyword ||
        [item.id, item.customer_name, item.customer_id, item.contract_id].some((value) =>
          value.toLowerCase().includes(normalizedKeyword),
        );

      return matchesStatus && matchesYear && matchesMonth && matchesKeyword;
    });
  }, [payments, keyword, year, month, status, getCustomerName]);

  const pageCount = Math.max(1, Math.ceil(rows.length / pageSize));
  const currentPage = Math.min(page, pageCount);
  const firstRow = (currentPage - 1) * pageSize;
  const paginatedRows = rows.slice(firstRow, firstRow + pageSize);

  useEffect(() => {
    setPage(1);
  }, [keyword, year, month, status]);

  function setStatus(value) {
    const nextParams = new URLSearchParams(params);

    if (value) {
      nextParams.set("status", value);
    } else {
      nextParams.delete("status");
    }

    setParams(nextParams);
  }

  function setDateFilter(name, value) {
    const nextParams = new URLSearchParams(params);

    if (value) {
      nextParams.set(name, value);
    } else {
      nextParams.delete(name);
    }

    setParams(nextParams);
  }

  const totalRevenue = payments.reduce(
    (sum, item) => sum + Number(item.total_amount),
    0,
  );

  const summary = [
    {
      label: "Tổng doanh thu kỳ này",
      value: `${new Intl.NumberFormat("vi-VN").format(totalRevenue)} ₫`,
      icon: WalletCards,
      tone: "blue",
    },
    {
      label: "Đang chờ phê duyệt",
      value: `${
        payments.filter(
          (item) => item.status === "PENDING_APPROVAL",
        ).length
      } hồ sơ`,
      icon: Clock3,
      tone: "orange",
    },
    {
      label: "Đã hoàn tất thanh toán",
      value: `${
        payments.filter((item) =>
          ["APPROVED", "SIGNED"].includes(item.status),
        ).length
      } bảng`,
      icon: CheckCircle2,
      tone: "green",
    },
    {
      label: "Cần điều chỉnh",
      value: `${
        payments.filter(
          (item) => item.status === "REVISION_REQUESTED",
        ).length
      } bảng`,
      icon: AlertCircle,
      tone: "red",
    },
  ];

  return (
    <>
      <div className="pay-page-heading">
        <div>
          <h1>Quản lý Bảng thanh toán</h1>

          <p>
            Theo dõi, kiểm tra và phê duyệt các bảng thanh toán
            định kỳ của khách hàng.
          </p>
        </div>

        {canManage ? (
          <Link className="pay-button primary" to="/payments/create">
            <PlusCircle size={17} />
            Lập bảng thanh toán
          </Link>
        ) : null}
      </div>

      <section className="pay-filter-card">
        <label className="pay-field search">
          <span>Tìm kiếm</span>

          <div>
            <Search size={17} />

            <input
              type="search"
              value={keyword}
              onChange={(event) => setKeyword(event.target.value)}
              placeholder="Tìm theo mã bảng, khách hàng hoặc hợp đồng"
            />
          </div>
        </label>

        <label className="pay-field">
          <span>Năm thanh toán</span>

          <select value={year} onChange={(event) => setDateFilter("year", event.target.value)}>
            <option value="">Tất cả năm</option>
            {yearOptions.map((value) => (
              <option key={value} value={value}>{value}</option>
            ))}
          </select>
        </label>

        <label className="pay-field">
          <span>Tháng thanh toán</span>

          <select value={month} onChange={(event) => setDateFilter("month", event.target.value)}>
            <option value="">Tất cả tháng</option>
            {Array.from({ length: 12 }, (_, index) => index + 1).map((value) => (
              <option key={value} value={value}>Tháng {value}</option>
            ))}
          </select>
        </label>

        <label className="pay-field">
          <span>Trạng thái</span>

          <select
            value={status}
            onChange={(event) => setStatus(event.target.value)}
          >
            <option value="">Tất cả trạng thái</option>

            {Object.entries(paymentStatusLabels).map(
              ([value, label]) => (
                <option key={value} value={value}>
                  {label}
                </option>
              ),
            )}
          </select>
        </label>

        <button
          className="pay-icon-button"
          type="button"
          aria-label="Mở bộ lọc nâng cao"
          title="Bộ lọc nâng cao"
        >
          <Filter size={18} />
        </button>
      </section>

      {isPending ? (
        <PaymentState title="Đang tải bảng thanh toán..." />
      ) : null}

      {error ? (
        <PaymentState
          title="Không thể tải dữ liệu"
          description={error.message}
        />
      ) : null}

      {!isPending && !error && !rows.length ? (
        <PaymentState
          title="Chưa có bảng thanh toán"
          description="Hãy lập bảng thanh toán đầu tiên hoặc thay đổi bộ lọc."
        />
      ) : null}

      {rows.length ? (
        <section className="pay-panel pay-list-panel">
          <div className="pay-table-scroll">
            <table className="pay-table">
              <thead>
                <tr>
                  <th>Mã bảng</th>
                  <th>Khách hàng</th>
                  <th>Hợp đồng</th>
                  <th>Kỳ thanh toán</th>
                  <th>Tổng tiền</th>
                  <th>Trạng thái</th>
                  <th>Ngày tạo</th>
                  <th>Thao tác</th>
                </tr>
              </thead>

              <tbody>
                {paginatedRows.map((item) => (
                  <tr key={item.id}>
                    <td>
                      <Link
                        className="pay-record-link"
                        to={`/payments/${item.id}`}
                      >
                        {item.id}
                      </Link>
                    </td>

                    <td>
                      <strong>{item.customer_name}</strong>
                    </td>

                    <td>{item.contract_id}</td>

                    <td>
                      {new Date(
                        item.period_start,
                      ).toLocaleDateString("vi-VN", {
                        month: "2-digit",
                        year: "numeric",
                      })}
                    </td>

                    <td>
                      <strong>
                        {new Intl.NumberFormat("vi-VN").format(
                          Number(item.total_amount),
                        )}{" "}
                        ₫
                      </strong>
                    </td>

                    <td>
                      <PaymentStatus status={item.status} />
                    </td>

                    <td>{formatDate(item.created_at)}</td>

                    <td>
                      <div className="pay-row-actions">
                        <Link
                          to={`/payments/${item.id}`}
                          title="Xem chi tiết"
                          aria-label="Xem chi tiết"
                        >
                          <Eye size={17} />
                        </Link>

                        {canManage && item.status === "DRAFT" ? (
                          <Link
                            to={`/payments/${item.id}/edit`}
                            title="Chỉnh sửa bản nháp"
                            aria-label="Chỉnh sửa bản nháp"
                          >
                            <Pencil size={17} />
                          </Link>
                        ) : null}

                        {canManage && item.status === "DRAFT" ? (
                          <Link
                            to={`/payments/${item.id}`}
                            title="Gửi phê duyệt"
                            aria-label="Gửi phê duyệt"
                          >
                            <Send size={17} />
                          </Link>
                        ) : null}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <footer>
            <span>
              Hiển thị {firstRow + 1} – {Math.min(firstRow + pageSize, rows.length)} của {rows.length} bảng
              thanh toán
            </span>

            <div>
              <button type="button" disabled={currentPage === 1} onClick={() => setPage((value) => Math.max(1, value - 1))}>‹</button>
              {Array.from({ length: pageCount }, (_, index) => index + 1).map((pageNumber) => (
                <button className={pageNumber === currentPage ? "active" : ""} type="button" key={pageNumber} onClick={() => setPage(pageNumber)}>{pageNumber}</button>
              ))}
              <button type="button" disabled={currentPage === pageCount} onClick={() => setPage((value) => Math.min(pageCount, value + 1))}>›</button>
            </div>
          </footer>
        </section>
      ) : null}

      <section className="pay-summary-grid">
        {summary.map(({ label, value, icon: Icon, tone }) => (
          <article key={label} className={tone}>
            <span>
              <Icon size={20} />
            </span>

            <div>
              <small>{label}</small>
              <strong>{value}</strong>
            </div>
          </article>
        ))}
      </section>
    </>
  );
}
