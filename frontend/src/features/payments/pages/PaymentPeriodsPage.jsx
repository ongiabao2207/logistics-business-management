import { CalendarDays, CheckCircle2, Clock3, RotateCcw } from "lucide-react";
import { Link, useSearchParams } from "react-router-dom";

import { PaymentBreadcrumb } from "../components/PaymentBreadcrumb.jsx";

export function PaymentPeriodsPage() {
  const now = new Date();
  const [params, setParams] = useSearchParams();
  const year = Number(params.get("year")) || now.getFullYear();
  const month = Number(params.get("month")) || now.getMonth() + 1;
  const yearOptions = Array.from(
    { length: 4 },
    (_, index) => now.getFullYear() - index,
  );

  const periods = [
    {
      month,
      state: "open",
      note: "Kỳ thanh toán hiện tại. Cần hoàn tất đối soát trước ngày 20.",
    },
    {
      month: month === 12 ? 1 : month + 1,
      state: "future",
      note: "Dự kiến bắt đầu vào đầu tháng. Dữ liệu hợp đồng mới đang chờ.",
    },
    {
      month: month === 1 ? 12 : month - 1,
      state: "closed",
      note: "Kỳ thanh toán trước. Đã hoàn tất phê duyệt và thanh toán.",
    },
    {
      month: month <= 2 ? 12 : month - 2,
      state: "closed",
      note: "Dữ liệu của kỳ thanh toán đã được lưu trữ.",
    },
  ];

  const changeYear = (event) => {
    const next = new URLSearchParams(params);
    next.set("year", event.target.value);
    setParams(next);
  };

  return (
    <>
      <PaymentBreadcrumb items={[{ label: "Lập bảng thanh toán" }]} />

      <section className="pay-period-banner">
        <strong>Danh sách kỳ thanh toán</strong>
        <p>
          Chọn một tháng cụ thể để tiếp tục đối soát sản lượng,
          chọn khách hàng và lập bảng thanh toán.
        </p>
      </section>

      <div className="pay-period-toolbar">
        <label>
          <span>Năm thanh toán</span>
          <select value={year} onChange={changeYear}>
            {yearOptions.map((option) => (
              <option key={option} value={option}>{option}</option>
            ))}
          </select>
        </label>
      </div>

      <section className="pay-period-grid">
        {periods.map((item, index) => (
          <article key={`${year}-${item.month}-${index}`}>
            <div className="period-card-top">
              <span className={`period-icon ${item.state}`}>
                {item.state === "future" ? (
                  <Clock3 />
                ) : item.state === "closed" ? (
                  <CheckCircle2 />
                ) : (
                  <CalendarDays />
                )}
              </span>
              <small>
                {item.state === "open"
                  ? "Đang mở"
                  : item.state === "future"
                    ? "Chưa mở"
                    : "Đã đóng"}
              </small>
            </div>

            <h3>Tháng {String(item.month).padStart(2, "0")}/{year}</h3>
            <p>{item.note}</p>

            <div className="period-progress">
              <span>Trạng thái:</span>
              <strong>
                {item.state === "closed" ? "Hoàn tất 100%" : "Chưa lập bảng"}
              </strong>
            </div>

            {item.state === "closed" ? (
              <button className="pay-button outline full">
                <RotateCcw size={15} />Xem lại
              </button>
            ) : (
              <Link
                className={`pay-button ${item.state === "open" ? "primary" : "outline"} full`}
                to={`/payments/periods/${year}-${item.month}/customers`}
              >
                Chọn kỳ →
              </Link>
            )}
          </article>
        ))}
      </section>

      <section className="pay-activity">
        <div><h3>Hoạt động gần đây</h3><a>Xem tất cả</a></div>
        <table className="pay-table">
          <thead>
            <tr><th>Hoạt động</th><th>Kỳ</th><th>Người thực hiện</th><th>Thời gian</th><th>Trạng thái</th></tr>
          </thead>
          <tbody>
            <tr><td>Khởi tạo bảng thanh toán</td><td>Tháng {month}/{year}</td><td>Nguyễn Văn A</td><td>09:30</td><td className="success">● Thành công</td></tr>
            <tr><td>Điều chỉnh sản lượng kỳ trước</td><td>Tháng {month === 1 ? 12 : month - 1}/{year}</td><td>Trần Thị B</td><td>16:45</td><td className="success">● Thành công</td></tr>
          </tbody>
        </table>
      </section>
    </>
  );
}
