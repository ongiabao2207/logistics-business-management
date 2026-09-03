import {
  CalendarDays,
  FileText,
  Pencil,
  PlusCircle,
  Save,
  Send,
  UserRound,
} from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";

import { PaymentBreadcrumb } from "../components/PaymentBreadcrumb.jsx";
import { PaymentLines } from "../components/PaymentLines.jsx";
import { PaymentTotals } from "../components/PaymentTotals.jsx";
import { usePaymentContracts } from "../hooks/usePaymentContracts.js";
import {
  useCreatePayment,
  usePayments,
  usePreviewPayment,
  useSubmitPayment,
} from "../hooks/usePayments.js";

function datesFromPeriod(period) {
  if (!period) return { period_start: "", period_end: "" };
  const [year, month] = period.split("-").map(Number);
  return {
    period_start: `${year}-${String(month).padStart(2, "0")}-01`,
    period_end: `${year}-${String(month).padStart(2, "0")}-${new Date(year, month, 0).getDate()}`,
  };
}

export function PaymentCreatePage() {
  const [params] = useSearchParams();
  const navigate = useNavigate();
  const periodDates = datesFromPeriod(params.get("period"));
  const [form, setForm] = useState({
    customer_id: params.get("customer_id") ?? "",
    contract_id: params.get("contract_id") ?? "",
    ...periodDates,
    tax_rate: "0.10",
  });
  const { getCustomerName } = usePaymentContracts();
  const preview = usePreviewPayment();
  const create = useCreatePayment();
  const submit = useSubmitPayment();
  const paymentsQuery = usePayments({
    offset: 0,
    limit: 200,
    contract_id: form.contract_id,
    period_start: form.period_start,
    period_end: form.period_end,
  });
  const [values, setValues] = useState({});
  const [visibleIds, setVisibleIds] = useState([]);
  const [showAddItems, setShowAddItems] = useState(false);
  const [saving, setSaving] = useState(false);
  const [localError, setLocalError] = useState("");
  const customerName = getCustomerName(form.contract_id, form.customer_id);
  const payload = { ...form, tax_rate: Number(form.tax_rate) };
  const error = preview.error ?? create.error ?? submit.error;

  const existingPayment = (paymentsQuery.data ?? []).find((payment) => (
    payment.contract_id === form.contract_id
    && payment.period_start === form.period_start
    && payment.period_end === form.period_end
  ));

  useEffect(() => {
    if (existingPayment) {
      navigate(`/payments/${existingPayment.id}`, { replace: true });
    }
  }, [existingPayment, navigate]);

  const displayedPayment = useMemo(() => {
    if (!preview.data) return null;
    const lines = preview.data.lines.filter((line) => visibleIds.includes(line.service_id)).map((line) => {
      const billingQuantity = Number(values[line.service_id] ?? line.billing_quantity);
      const validQuantity = Number.isFinite(billingQuantity) && billingQuantity > 0 && billingQuantity <= Number(line.confirmed_quantity)
        ? billingQuantity
        : 0;
      const lineAmount = validQuantity * Number(line.unit_price_snapshot);
      const taxAmount = lineAmount * Number(line.tax_rate);
      return { ...line, billing_quantity: billingQuantity, line_amount: lineAmount, tax_amount: taxAmount };
    });
    const subtotal = lines.reduce((sum, line) => sum + line.line_amount, 0);
    const taxAmount = lines.reduce((sum, line) => sum + line.tax_amount, 0);
    return { ...preview.data, lines, subtotal, tax_amount: taxAmount, total_amount: subtotal + taxAmount };
  }, [preview.data, values, visibleIds]);

  const removedLines = preview.data?.lines.filter(
    (line) => !visibleIds.includes(line.service_id),
  ) ?? [];

  const change = (event) => setForm((current) => ({
    ...current,
    [event.target.name]: event.target.value,
  }));

  const calculate = () => preview.mutate(payload, {
    onSuccess(data) {
      setValues(Object.fromEntries(data.lines.map((line) => [line.service_id, line.billing_quantity])));
      setVisibleIds(data.lines.map((line) => line.service_id));
      setShowAddItems(false);
      setLocalError("");
    },
  });

  const changeQuantity = (serviceId, value) => {
    setValues((current) => ({ ...current, [serviceId]: value }));
    const line = preview.data?.lines.find((item) => item.service_id === serviceId);
    const quantity = Number(value);
    if (!Number.isFinite(quantity) || quantity <= 0) {
      setLocalError(`Sản lượng thanh toán của “${line?.description ?? "hạng mục"}” phải lớn hơn 0.`);
    } else if (line && quantity > Number(line.confirmed_quantity)) {
      setLocalError(`Sản lượng thanh toán của “${line.description}” không được lớn hơn sản lượng xác nhận.`);
    } else {
      setLocalError("");
    }
  };

  const save = async (andSubmit) => {
    if (!displayedPayment || saving) return;
    const nonPositiveLine = displayedPayment.lines.find(
      (line) => !Number.isFinite(Number(line.billing_quantity)) || Number(line.billing_quantity) <= 0,
    );
    if (nonPositiveLine) {
      setLocalError(`Sản lượng thanh toán của “${nonPositiveLine.description}” phải lớn hơn 0.`);
      return;
    }
    const invalidLine = displayedPayment.lines.find(
      (line) => Number(line.billing_quantity) > Number(line.confirmed_quantity),
    );
    if (invalidLine) {
      setLocalError(`Sản lượng thanh toán của “${invalidLine.description}” không được lớn hơn sản lượng xác nhận.`);
      return;
    }
    setLocalError("");
    setSaving(true);
    try {
      let payment = await create.mutateAsync({
        ...payload,
        lines: displayedPayment.lines.map((line) => ({
          service_id: line.service_id,
          billing_quantity: Number(line.billing_quantity),
        })),
      });
      if (andSubmit) {
        payment = await submit.mutateAsync(payment.id);
        navigate(`/payments/${payment.id}/approval`);
      } else {
        navigate(`/payments/${payment.id}/edit`);
      }
    } catch {
      // Mutation state renders the API error above the table.
    } finally {
      setSaving(false);
    }
  };

  return <>
    <PaymentBreadcrumb items={[{ label: "Lập mới" }]} />
    <h2 className="pay-page-title">Lập bảng thanh toán chi tiết</h2>
    <section className="pay-info-cards">
      <article>
        <span><UserRound /></span>
        <div>
          <small>Khách hàng</small>
          <input value={customerName} readOnly />
        </div>
      </article>
      <article>
        <span><CalendarDays /></span>
        <div>
          <small>Kỳ thanh toán</small>
          <div className="date-pair">
            <input type="date" name="period_start" value={form.period_start} onChange={change} />
            <input type="date" name="period_end" value={form.period_end} onChange={change} />
          </div>
        </div>
      </article>
      <article>
        <span><FileText /></span>
        <div>
          <small>Hợp đồng gốc</small>
          <input value={form.contract_id} readOnly />
        </div>
      </article>
    </section>
    <div className="pay-preview-action">
      <button className="pay-button outline" type="button" onClick={calculate} disabled={!form.customer_id || !form.contract_id || preview.isPending}>
        <Pencil size={16} />
        {preview.isPending ? "Đang lấy dữ liệu..." : "Tính bảng thanh toán"}
      </button>
    </div>
    {localError || error ? <div className="pay-alert error">{localError || error.message}</div> : null}
    {preview.data ? <section className="pay-panel create-detail">
      <header>
        <div>
          <button className="pay-text-action" type="button" onClick={() => setShowAddItems((current) => !current)}><PlusCircle size={15} />Thêm hạng mục</button>
        </div>
        <strong>Chi tiết các hạng mục thanh toán</strong>
      </header>
      {showAddItems ? <div className="pay-alert info">{removedLines.length ? <><strong>Chọn hạng mục muốn thêm lại: </strong>{removedLines.map((line) => <button className="pay-text-action" type="button" key={line.service_id} onClick={() => setVisibleIds((current) => [...current, line.service_id])}>{line.description}</button>)}</> : "Tất cả hạng mục có sản lượng hợp lệ từ Production đã nằm trong bảng."}</div> : null}
      <PaymentLines lines={displayedPayment.lines} editable values={values} onChange={changeQuantity} onRemove={(id) => setVisibleIds((current) => current.filter((item) => item !== id))} />
      <PaymentTotals payment={displayedPayment} />
    </section> : <div className="pay-empty-preview">
      <FileText size={30} />
      <strong>Chưa có dữ liệu xem trước</strong>
      <p>Chọn khách hàng, hợp đồng và kỳ rồi bấm “Tính bảng thanh toán”.</p>
    </div>}
    {preview.data ? <div className="pay-bottom-bar">
      <span>ⓘ Dữ liệu được tổng hợp từ hợp đồng, bảng giá và sản lượng.</span>
      <div>
        <Link className="pay-button outline" to="/payments">Hủy</Link>
        <button className="pay-button outline" type="button" disabled={saving} onClick={() => save(false)}><Save size={16} />{saving ? "Đang lưu..." : "Lưu nháp"}</button>
        <button className="pay-button primary" type="button" disabled={saving} onClick={() => save(true)}><Send size={16} />{saving ? "Đang lưu..." : "Lưu và gửi phê duyệt"}</button>
      </div>
    </div> : null}
  </>;
}
