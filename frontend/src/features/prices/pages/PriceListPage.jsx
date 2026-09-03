import { useMemo, useRef, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowLeft, CalendarDays, Check, ChevronDown, Eye, PackagePlus, Plus, Search, Send, Trash2, X } from "lucide-react";

import { DataState } from "../../../shared/components/DataState.jsx";
import { usePageTitle } from "../../../shared/hooks/usePageTitle";
import { ROLES } from "../../identity/constants/permissions";
import { useAuth } from "../../identity/hooks/useAuth";
import { priceApi } from "../api/priceApi";
import { usePriceLists } from "../hooks/usePriceLists";

const statusLabels = { DRAFT: "Bản nháp", SUBMITTED: "Chờ duyệt", APPROVED: "Đã duyệt", REJECTED: "Từ chối", EFFECTIVE: "Đang hiệu lực", SUPERSEDED: "Đã thay thế", EXPIRED: "Hết hiệu lực" };
const statusTones = { DRAFT: "is-draft", SUBMITTED: "is-warning", APPROVED: "is-success", REJECTED: "is-muted", EFFECTIVE: "is-success", SUPERSEDED: "is-muted", EXPIRED: "is-muted" };
const emptyPriceForm = { description: "", effective_from: "", effective_to: "", details: [{ service_id: "", unit_price: "" }] };
const emptyServiceForm = { name: "", description: "", unit: "" };

export function PriceListPage() {
  usePageTitle("Quản lý bảng giá");
  const { user } = useAuth();
  const queryClient = useQueryClient();
  const canManage = user.role === ROLES.SALE;
  const canApprove = user.role === ROLES.DIRECTOR;
  const [tab, setTab] = useState("prices");
  const [view, setView] = useState("list");
  const [query, setQuery] = useState("");
  const [status, setStatus] = useState("ALL");
  const [selectedPriceId, setSelectedPriceId] = useState(null);
  const [effectiveServiceId, setEffectiveServiceId] = useState("");
  const [showServiceModal, setShowServiceModal] = useState(false);
  const [priceForm, setPriceForm] = useState(emptyPriceForm);
  const [serviceForm, setServiceForm] = useState(emptyServiceForm);
  const [editPrice, setEditPrice] = useState(null);

  const priceListsQuery = usePriceLists({ limit: 100 });
  const servicesQuery = useQuery({ queryKey: ["prices", "services"], queryFn: () => priceApi.listServices({ limit: 100 }) });
  const detailQuery = useQuery({ queryKey: ["prices", "price-list", selectedPriceId], queryFn: () => priceApi.getPriceList(selectedPriceId), enabled: Boolean(selectedPriceId) });
  const effectiveQuery = useQuery({ queryKey: ["prices", "effective", effectiveServiceId], queryFn: () => priceApi.getEffectiveServicePrice(effectiveServiceId), enabled: Boolean(effectiveServiceId), retry: false });
  const priceLists = useMemo(() => priceListsQuery.data ?? [], [priceListsQuery.data]);
  const services = useMemo(() => servicesQuery.data ?? [], [servicesQuery.data]);
  const serviceMap = useMemo(() => Object.fromEntries(services.map((service) => [service.id, service])), [services]);
  const rows = useMemo(() => priceLists.filter((item) => `${item.id} ${item.description}`.toLowerCase().includes(query.toLowerCase()) && (status === "ALL" || item.status === status)), [priceLists, query, status]);
  const refresh = () => queryClient.invalidateQueries({ queryKey: ["prices"] });
  const mutation = (fn, onSuccess = refresh) => ({ mutationFn: fn, onSuccess });
  const createPrice = useMutation(mutation(priceApi.createPriceList, () => { refresh(); setPriceForm(emptyPriceForm); setView("list"); }));
  const updatePrice = useMutation(mutation(({ id, payload }) => priceApi.updatePriceList(id, { ...payload, effective_from: toIsoDate(payload.effective_from), effective_to: toIsoDate(payload.effective_to) }), (data) => { refresh(); queryClient.setQueryData(["prices", "price-list", data.id], data); setEditPrice(null); }));
  const deletePrice = useMutation(mutation(priceApi.deletePriceList, () => { refresh(); setSelectedPriceId(null); }));
  const submitPrice = useMutation(mutation(priceApi.submitPriceList));
  const approvePrice = useMutation(mutation(priceApi.approvePriceList));
  const rejectPrice = useMutation(mutation(priceApi.rejectPriceList));
  const createService = useMutation(mutation(priceApi.createService, () => { queryClient.invalidateQueries({ queryKey: ["prices", "services"] }); setServiceForm(emptyServiceForm); setShowServiceModal(false); }));
  const deactivateService = useMutation(mutation(priceApi.deactivateService, () => queryClient.invalidateQueries({ queryKey: ["prices", "services"] })));

  function updateDetail(index, field, value) { setPriceForm({ ...priceForm, details: priceForm.details.map((detail, i) => i === index ? { ...detail, [field]: value } : detail) }); }
  function submitNewPrice(event) { event.preventDefault(); createPrice.mutate({ ...priceForm, effective_from: toIsoDate(priceForm.effective_from), effective_to: toIsoDate(priceForm.effective_to), details: priceForm.details.map((detail) => ({ service_id: Number(detail.service_id), unit_price: Number(detail.unit_price) })) }); }
  function openPrice(item) { setSelectedPriceId(item.id); setEditPrice({ description: item.description, effective_from: dateText(item.effective_from), effective_to: dateText(item.effective_to) }); }

  if (priceListsQuery.isLoading || servicesQuery.isLoading) return <section className="workspace"><DataState title="Đang tải dữ liệu Price Service..." /></section>;
  if (priceListsQuery.isError || servicesQuery.isError) return <section className="workspace"><DataState title="Không tải được dữ liệu Price Service" description="Kiểm tra service và quyền tài khoản." /></section>;

  if (view === "create" && canManage) return <PriceCreateForm form={priceForm} setForm={setPriceForm} services={services} serviceMap={serviceMap} updateDetail={updateDetail} mutation={createPrice} submit={submitNewPrice} close={() => setView("list")} />;

  return <section className="workspace">
    <div className="workspace-title"><div><span className="breadcrumb">Price Service / Quản lý giá</span><h1>Danh mục dịch vụ & bảng giá</h1><p>Toàn bộ dữ liệu được đọc và ghi qua API Price Service.</p></div>{canManage && <div className="page-actions"><button className="button outline" type="button" onClick={() => setShowServiceModal(true)}><PackagePlus size={18} /> Thêm dịch vụ</button><button className="button primary" type="button" onClick={() => setView("create")}><Plus size={18} /> Tạo bảng giá</button></div>}</div>
    <div className="segmented-tabs"><button className={tab === "prices" ? "is-active" : ""} type="button" onClick={() => setTab("prices")}>Bảng giá ({priceLists.length})</button><button className={tab === "services" ? "is-active" : ""} type="button" onClick={() => setTab("services")}>Danh mục dịch vụ ({services.length})</button><button className={tab === "effective" ? "is-active" : ""} type="button" onClick={() => setTab("effective")}>Tra cứu giá hiệu lực</button></div>
    {tab === "prices" && <PriceListTab rows={rows} query={query} setQuery={setQuery} status={status} setStatus={setStatus} canManage={canManage} canApprove={canApprove} openPrice={openPrice} submitPrice={submitPrice} approvePrice={approvePrice} rejectPrice={rejectPrice} />}
    {tab === "services" && <ServiceTab services={services} canManage={canManage} deactivate={deactivateService} openCreate={() => setShowServiceModal(true)} />}
    {tab === "effective" && <EffectiveTab services={services} value={effectiveServiceId} setValue={setEffectiveServiceId} query={effectiveQuery} />}

    {showServiceModal && <ServiceModal form={serviceForm} setForm={setServiceForm} mutation={createService} close={() => setShowServiceModal(false)} />}
    {selectedPriceId && <PriceDetailModal query={detailQuery} edit={editPrice} setEdit={setEditPrice} services={serviceMap} canManage={canManage} update={updatePrice} remove={deletePrice} close={() => setSelectedPriceId(null)} />}
  </section>;
}

function PriceListTab({ rows, query, setQuery, status, setStatus, canManage, canApprove, openPrice, submitPrice, approvePrice, rejectPrice }) {
  return <><div className="filter-card identity-filters"><label className="field-wide"><span>Tìm kiếm</span><div className="input-with-icon"><Search size={18} /><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Mã hoặc tên bảng giá..." /></div></label><label><span>Trạng thái</span><select value={status} onChange={(event) => setStatus(event.target.value)}><option value="ALL">Tất cả</option>{Object.entries(statusLabels).map(([value, label]) => <option value={value} key={value}>{label}</option>)}</select></label></div><div className="table-card"><div className="card-heading"><div><h2>Bảng giá trong database</h2><p>{rows.length} kết quả</p></div></div><div className="table-scroll"><table className="business-table"><thead><tr><th>Mã</th><th>Tên bảng giá</th><th>Số dịch vụ</th><th>Hiệu lực</th><th>Trạng thái</th><th>Thao tác</th></tr></thead><tbody>{rows.map((item) => <tr key={item.id}><td><strong className="code-text">{item.id}</strong></td><td><strong>{item.description}</strong></td><td>{item.details.length}</td><td>{dateText(item.effective_from)} – {dateText(item.effective_to)}</td><td><Status status={item.status} /></td><td><div className="row-actions"><Action icon={<Eye size={19} />} title="Chi tiết" click={() => openPrice(item)} />{canManage && item.status === "DRAFT" && <Action icon={<Send size={18} />} title="Gửi duyệt" click={() => submitPrice.mutate(item.id)} />}{canApprove && item.status === "SUBMITTED" && <><Action className="approve" icon={<Check size={19} />} title="Phê duyệt" click={() => approvePrice.mutate(item.id)} /><Action className="danger" icon={<X size={19} />} title="Từ chối" click={() => rejectPrice.mutate(item.id)} /></>}</div></td></tr>)}</tbody></table></div></div></>;
}

function ServiceTab({ services, canManage, deactivate, openCreate }) {
  return <div className="table-card"><div className="card-heading"><div><h2>Danh mục dịch vụ</h2><p>GET /api/v1/services</p></div>{canManage && <button className="button primary" type="button" onClick={openCreate}><Plus size={17} /> Thêm dịch vụ</button>}</div>{deactivate.isError && <p className="inline-api-error">{deactivate.error.message}</p>}<div className="table-scroll"><table className="business-table"><thead><tr><th>ID</th><th>Tên dịch vụ</th><th>Mã/Mô tả</th><th>Đơn vị</th><th>Trạng thái</th><th>Thao tác</th></tr></thead><tbody>{services.map((service) => <tr key={service.id}><td>{service.id}</td><td><strong>{service.name}</strong></td><td>{service.description}</td><td>{service.unit}</td><td><span className={`pill ${service.is_active ? "is-success" : "is-muted"}`}>{service.is_active ? "Hoạt động" : "Ngừng hoạt động"}</span></td><td>{canManage && service.is_active && <button className="button danger-button" type="button" disabled={deactivate.isPending} onClick={() => deactivate.mutate(service.id)}>Ngừng sử dụng</button>}</td></tr>)}</tbody></table></div></div>;
}

function EffectiveTab({ services, value, setValue, query }) {
  return <div className="lookup-grid"><div className="form-card"><h2>Tra cứu giá dịch vụ đang hiệu lực</h2><div className="form-grid"><label><span>Dịch vụ</span><select value={value} onChange={(event) => setValue(event.target.value)}><option value="">Chọn dịch vụ</option>{services.filter((service) => service.is_active).map((service) => <option value={service.id} key={service.id}>{service.name}</option>)}</select></label></div></div>{value && (query.isLoading ? <DataState title="Đang tra cứu..." /> : query.isError ? <DataState title="Không có giá hiệu lực" description={query.error.message} /> : <div className="effective-result"><small>Bảng giá {query.data.price_list_id}</small><h2>{query.data.service_name}</h2><strong>{Number(query.data.unit_price).toLocaleString("vi-VN")} VNĐ / {query.data.unit}</strong><p>Hiệu lực: {dateText(query.data.effective_from)} – {dateText(query.data.effective_to)}</p></div>)}</div>;
}

function PriceCreateForm({ form, setForm, services, serviceMap, updateDetail, mutation, submit, close }) {
  const selectedIds = form.details.map((detail) => String(detail.service_id)).filter(Boolean);
  return <section className="workspace price-editor"><div className="workspace-title compact-title"><button className="icon-button back-button" type="button" onClick={close}><ArrowLeft size={20} /></button><div><span className="breadcrumb">Bảng giá / Tạo mới</span><h1>Tạo bảng giá mới</h1><p>POST /api/v1/price-lists</p></div></div><form onSubmit={submit}><div className="form-card"><h2>Thông tin bảng giá</h2><div className="form-grid three-columns"><Field label="Tên bảng giá" value={form.description} change={(value) => setForm({ ...form, description: value })} /><Field label="Ngày bắt đầu" type="date" value={form.effective_from} change={(value) => setForm({ ...form, effective_from: value })} /><Field label="Ngày kết thúc" type="date" value={form.effective_to} change={(value) => setForm({ ...form, effective_to: value })} /></div></div><div className="table-card"><div className="card-heading"><div><h2>Chi tiết đơn giá</h2><p>Chọn dịch vụ và nhập đơn giá áp dụng</p></div><button className="button primary" type="button" onClick={() => setForm({ ...form, details: [...form.details, { service_id: "", unit_price: "" }] })}><Plus size={17} /> Thêm dòng</button></div><div className="table-scroll"><table className="business-table"><thead><tr><th>Dịch vụ</th><th>Đơn vị</th><th>Đơn giá</th><th></th></tr></thead><tbody>{form.details.map((detail, index) => <tr key={index}><td><ServiceSelect services={services} value={detail.service_id} selectedIds={selectedIds} onChange={(value) => updateDetail(index, "service_id", value)} /></td><td>{serviceMap[detail.service_id]?.unit ?? "—"}</td><td><input className="price-input" type="number" min="0" value={detail.unit_price} onChange={(event) => updateDetail(index, "unit_price", event.target.value)} required /></td><td><Action className="danger" icon={<Trash2 size={18} />} title="Xóa" click={() => form.details.length > 1 && setForm({ ...form, details: form.details.filter((_, i) => i !== index) })} /></td></tr>)}</tbody></table></div></div><Error mutation={mutation} /><div className="sticky-actions"><span>{form.details.length} dịch vụ</span><div><button className="button ghost" type="button" onClick={close}>Hủy</button><button className="button navy" type="submit"><Send size={17} /> Lưu bảng giá</button></div></div></form></section>;
}

function ServiceSelect({ services, value, selectedIds, onChange }) {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const rootRef = useRef(null);
  const selected = services.find((service) => String(service.id) === String(value));
  const activeServices = services.filter((service) => service.is_active);
  const normalizedQuery = query.trim().toLowerCase();
  const filtered = activeServices.filter((service) => `${service.name} ${service.description} ${service.unit}`.toLowerCase().includes(normalizedQuery));

  function choose(serviceId) {
    onChange(String(serviceId));
    setOpen(false);
    setQuery("");
  }

  return <div className={`service-select ${open ? "is-open" : ""}`} ref={rootRef} onBlur={(event) => { if (!rootRef.current?.contains(event.relatedTarget)) setOpen(false); }}>
    <button className="service-select-trigger" type="button" aria-haspopup="listbox" aria-expanded={open} onClick={() => setOpen(!open)}>
      <span>{selected ? <strong>{selected.name}</strong> : <em>Chọn dịch vụ</em>}</span><ChevronDown size={18} />
    </button>
    <input className="service-select-required" value={value} onChange={() => {}} tabIndex="-1" aria-hidden="true" required />
    {open && <div className="service-select-menu">
      <div className="service-select-search"><Search size={17} /><input autoFocus value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Tìm tên, mô tả hoặc đơn vị..." /></div>
      <div className="service-select-options" role="listbox">
        {filtered.map((service) => {
          const isSelected = String(service.id) === String(value);
          const isUsed = !isSelected && selectedIds.includes(String(service.id));
          return <button type="button" role="option" aria-selected={isSelected} disabled={isUsed} className={isSelected ? "is-selected" : ""} key={service.id} onClick={() => choose(service.id)}><span><strong>{service.name}</strong><small>{service.description || "Không có mô tả"}</small></span>{isSelected && <Check size={17} />}</button>;
        })}
        {!filtered.length && <p className="service-select-empty">Không tìm thấy dịch vụ phù hợp.</p>}
      </div>
    </div>}
  </div>;
}

function PriceDetailModal({ query, edit, setEdit, services, canManage, update, remove, close }) {
  const item = query.data;
  return <div className="modal-backdrop" onMouseDown={close}><div className="modal-card modal-wide" onMouseDown={(event) => event.stopPropagation()}><ModalHeader title="Chi tiết bảng giá" description="GET /api/v1/price-lists/{id}" close={close} />{query.isLoading ? <DataState title="Đang tải chi tiết..." /> : item && <><div className="account-detail-summary"><div><small>Mã bảng giá</small><strong>{item.id}</strong></div><Status status={item.status} /></div><div className="form-grid three-columns"><Field label="Tên bảng giá" value={edit.description} change={(value) => setEdit({ ...edit, description: value })} disabled={!canManage || !["DRAFT", "REJECTED"].includes(item.status)} /><Field label="Ngày bắt đầu" type="date" value={edit.effective_from} change={(value) => setEdit({ ...edit, effective_from: value })} disabled={!canManage || !["DRAFT", "REJECTED"].includes(item.status)} /><Field label="Ngày kết thúc" type="date" value={edit.effective_to} change={(value) => setEdit({ ...edit, effective_to: value })} disabled={!canManage || !["DRAFT", "REJECTED"].includes(item.status)} /></div><div className="detail-lines">{item.details.map((detail) => <div key={detail.id}><span>{services[detail.service_id]?.name ?? `Dịch vụ #${detail.service_id}`}</span><strong>{Number(detail.unit_price).toLocaleString("vi-VN")} VNĐ</strong></div>)}</div><Error mutation={update} /><div className="modal-actions">{canManage && item.status === "DRAFT" && <button className="button danger-button" type="button" onClick={() => remove.mutate(item.id)}>Xóa bảng giá</button>}{canManage && ["DRAFT", "REJECTED"].includes(item.status) && <button className="button navy" type="button" onClick={() => update.mutate({ id: item.id, payload: edit })}>Lưu thay đổi</button>}</div></>}</div></div>;
}

function ServiceModal({ form, setForm, mutation, close }) { return <div className="modal-backdrop" onMouseDown={close}><form className="modal-card" onSubmit={(event) => { event.preventDefault(); mutation.mutate(form); }} onMouseDown={(event) => event.stopPropagation()}><ModalHeader title="Thêm dịch vụ mới" description="POST /api/v1/services" close={close} /><div className="form-grid two-columns"><Field label="Tên dịch vụ" value={form.name} change={(value) => setForm({ ...form, name: value })} /><Field label="Đơn vị tính" value={form.unit} change={(value) => setForm({ ...form, unit: value })} /><label className="span-two"><span>Mã hoặc mô tả <em>*</em></span><input value={form.description} onChange={(event) => setForm({ ...form, description: event.target.value })} required /></label></div><Error mutation={mutation} /><div className="modal-actions"><button className="button ghost" type="button" onClick={close}>Hủy</button><button className="button navy" type="submit">Thêm dịch vụ</button></div></form></div>; }
function ModalHeader({ title, description, close }) { return <div className="modal-heading"><div><span className="metric-icon blue"><PackagePlus size={20} /></span><div><h2>{title}</h2><p>{description}</p></div></div><button className="modal-close" type="button" onClick={close}>×</button></div>; }
function Field({ label, type = "text", value, change, disabled = false }) {
  const calendarRef = useRef(null);
  const isDate = type === "date";
  if (!isDate) return <label><span>{label} <em>*</em></span><input type={type} value={value} onChange={(event) => change(event.target.value)} disabled={disabled} required /></label>;
  function openCalendar() { if (calendarRef.current?.showPicker) calendarRef.current.showPicker(); else calendarRef.current?.click(); }
  return <label><span>{label} <em>*</em></span><div className="date-picker-control"><input type="text" inputMode="numeric" placeholder="dd/mm/yyyy" pattern="\d{2}/\d{2}/\d{4}" value={value} onChange={(event) => change(event.target.value)} disabled={disabled} required /><button type="button" onClick={openCalendar} disabled={disabled} aria-label={`Chọn ${label.toLowerCase()}`}><CalendarDays size={18} /></button><input ref={calendarRef} className="native-date-picker" type="date" value={toIsoDate(value)} onChange={(event) => change(dateText(event.target.value))} tabIndex="-1" aria-hidden="true" /></div></label>;
}
function Status({ status }) { return <span className={`pill ${statusTones[status]}`}>{statusLabels[status] ?? status}</span>; }
function Action({ icon, title, click, className = "" }) { return <button className={`icon-button ${className}`} type="button" title={title} onClick={click}>{icon}</button>; }
function Error({ mutation }) { return mutation.isError ? <p className="form-error">{mutation.error.message}</p> : null; }
function dateText(value) { const [year, month, day] = String(value).slice(0, 10).split("-"); return `${day}/${month}/${year}`; }
function toIsoDate(value) { if (/^\d{4}-\d{2}-\d{2}$/.test(String(value))) return value; const match = String(value).match(/^(\d{2})\/(\d{2})\/(\d{4})$/); return match ? `${match[3]}-${match[2]}-${match[1]}` : ""; }
