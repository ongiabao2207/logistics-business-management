import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Eye, KeyRound, LockKeyhole, Plus, Search, ShieldCheck, UserRoundCheck, UsersRound } from "lucide-react";

import { DataState } from "../../../shared/components/DataState.jsx";
import { usePageTitle } from "../../../shared/hooks/usePageTitle";
import { identityApi } from "../api/identityApi";
import { ROLE_LABELS } from "../constants/permissions";

const emptyForm = { username: "", email: "", password: "", role_id: "" };

export function IdentityLoginPage() {
  usePageTitle("Quản lý định danh");
  const queryClient = useQueryClient();
  const [query, setQuery] = useState("");
  const [tab, setTab] = useState("users");
  const [showCreate, setShowCreate] = useState(false);
  const [selectedId, setSelectedId] = useState(null);
  const [form, setForm] = useState(emptyForm);
  const [editEmail, setEditEmail] = useState("");
  const accountsQuery = useQuery({ queryKey: ["identity", "accounts"], queryFn: identityApi.listAccounts });
  const rolesQuery = useQuery({ queryKey: ["identity", "roles"], queryFn: identityApi.listRoles });
  const detailQuery = useQuery({ queryKey: ["identity", "account", selectedId], queryFn: () => identityApi.getAccount(selectedId), enabled: Boolean(selectedId) });
  const refreshAccounts = () => queryClient.invalidateQueries({ queryKey: ["identity", "accounts"] });
  const createMutation = useMutation({ mutationFn: identityApi.createAccount, onSuccess: () => { refreshAccounts(); setShowCreate(false); setForm(emptyForm); } });
  const emailMutation = useMutation({ mutationFn: ({ id, email }) => identityApi.updateAccount(id, { email }), onSuccess: (account) => { refreshAccounts(); queryClient.setQueryData(["identity", "account", account.id], account); } });
  const roleMutation = useMutation({ mutationFn: ({ id, roleId }) => identityApi.updateAccountRole(id, roleId), onSuccess: (account) => { refreshAccounts(); queryClient.setQueryData(["identity", "account", account.id], account); } });
  const statusMutation = useMutation({ mutationFn: ({ id, active }) => identityApi.updateAccountStatus(id, active), onSuccess: (account) => { refreshAccounts(); queryClient.setQueryData(["identity", "account", account.id], account); } });

  const accounts = useMemo(() => accountsQuery.data ?? [], [accountsQuery.data]);
  const roles = useMemo(() => rolesQuery.data ?? [], [rolesQuery.data]);
  const filtered = useMemo(() => accounts.filter((account) => `${account.username} ${account.email} ${account.role.name}`.toLowerCase().includes(query.toLowerCase())), [accounts, query]);
  const activeCount = accounts.filter((account) => account.is_active).length;
  const selected = detailQuery.data;

  function openDetail(account) { setSelectedId(account.id); setEditEmail(account.email); }
  function submitAccount(event) { event.preventDefault(); createMutation.mutate({ ...form, role_id: Number(form.role_id) }); }

  if (accountsQuery.isLoading || rolesQuery.isLoading) return <section className="workspace"><DataState title="Đang tải dữ liệu Identity từ database..." /></section>;
  if (accountsQuery.isError || rolesQuery.isError) return <section className="workspace"><DataState title="Không tải được dữ liệu Identity" description="Kiểm tra Identity Service và quyền ROLE_ADMIN." /></section>;

  return <section className="workspace identity-page">
    <div className="workspace-title"><div><span className="breadcrumb">Identity Service / Quản trị hệ thống</span><h1>Người dùng & phân quyền</h1><p>Quản lý đầy đủ tài khoản, trạng thái và vai trò từ Identity DB.</p></div><button className="button primary" type="button" onClick={() => { setForm({ ...emptyForm, role_id: String(roles[0]?.id ?? "") }); setShowCreate(true); }}><Plus size={18} /> Thêm người dùng</button></div>
    <div className="metric-grid"><article className="metric-card"><span className="metric-icon blue"><UsersRound size={21} /></span><div><small>Tổng người dùng</small><strong>{accounts.length}</strong><em>Dữ liệu database</em></div></article><article className="metric-card"><span className="metric-icon green"><UserRoundCheck size={21} /></span><div><small>Đang hoạt động</small><strong>{activeCount}</strong><em>{accounts.length ? Math.round(activeCount / accounts.length * 100) : 0}% tài khoản</em></div></article><article className="metric-card"><span className="metric-icon amber"><LockKeyhole size={21} /></span><div><small>Tạm khóa</small><strong>{accounts.length - activeCount}</strong><em>Tài khoản</em></div></article><article className="metric-card"><span className="metric-icon violet"><ShieldCheck size={21} /></span><div><small>Vai trò</small><strong>{roles.length}</strong><em>Trong database</em></div></article></div>
    <div className="segmented-tabs"><button className={tab === "users" ? "is-active" : ""} type="button" onClick={() => setTab("users")}><UsersRound size={17} /> Danh sách người dùng</button><button className={tab === "roles" ? "is-active" : ""} type="button" onClick={() => setTab("roles")}><ShieldCheck size={17} /> Vai trò & quyền hạn</button></div>
    {tab === "users" ? <><div className="filter-card identity-filters"><label className="field-wide"><span>Tìm kiếm</span><div className="input-with-icon"><Search size={18} /><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Email hoặc tên đăng nhập..." /></div></label></div><div className="table-card"><div className="card-heading"><div><h2>Danh sách tài khoản</h2><p>{filtered.length} kết quả</p></div></div><div className="table-scroll"><table className="business-table"><thead><tr><th>Người dùng</th><th>Vai trò</th><th>Ngày tạo</th><th>Trạng thái</th><th>Thao tác</th></tr></thead><tbody>{filtered.map((account) => <tr key={account.id}><td><div className="person-cell"><span>{account.username.slice(0, 2).toUpperCase()}</span><div><strong>{account.username}</strong><small>{account.email}</small></div></div></td><td><span className="role-tag">{ROLE_LABELS[account.role.name] ?? account.role.name}</span></td><td>{new Date(account.created_at).toLocaleDateString("vi-VN")}</td><td><span className={`pill ${account.is_active ? "is-success" : "is-muted"}`}>{account.is_active ? "Đang hoạt động" : "Tạm khóa"}</span></td><td><div className="row-actions"><button className="icon-button" type="button" title="Xem và chỉnh sửa" onClick={() => openDetail(account)}><Eye size={19} /></button><button className={`icon-button ${account.is_active ? "danger" : "approve"}`} type="button" title={account.is_active ? "Khóa tài khoản" : "Mở tài khoản"} onClick={() => statusMutation.mutate({ id: account.id, active: !account.is_active })}><LockKeyhole size={18} /></button></div></td></tr>)}</tbody></table></div></div></> : <div className="roles-grid">{roles.map((role) => <article className="role-card" key={role.id}><span className="metric-icon violet"><ShieldCheck size={20} /></span><div><h3>{ROLE_LABELS[role.name] ?? role.name}</h3><p>{role.description}</p><small>{accounts.filter((account) => account.role.id === role.id).length} người dùng</small></div></article>)}</div>}

    {showCreate && <div className="modal-backdrop" onMouseDown={() => setShowCreate(false)}><form className="modal-card" onSubmit={submitAccount} onMouseDown={(event) => event.stopPropagation()}><ModalHeader icon={<KeyRound size={20} />} title="Tạo tài khoản" description="Lưu tài khoản mới vào Identity DB." close={() => setShowCreate(false)} /><div className="form-grid two-columns"><Field label="Tên đăng nhập" value={form.username} change={(value) => setForm({ ...form, username: value })} /><Field label="Email" type="email" value={form.email} change={(value) => setForm({ ...form, email: value })} /><Field label="Mật khẩu" type="password" value={form.password} change={(value) => setForm({ ...form, password: value })} /><RoleSelect roles={roles} value={form.role_id} change={(value) => setForm({ ...form, role_id: value })} /></div><MutationError mutation={createMutation} /><ModalActions close={() => setShowCreate(false)} pending={createMutation.isPending} label="Tạo tài khoản" /></form></div>}

    {selectedId && <div className="modal-backdrop" onMouseDown={() => setSelectedId(null)}><div className="modal-card" onMouseDown={(event) => event.stopPropagation()}><ModalHeader icon={<UsersRound size={20} />} title="Chi tiết tài khoản" description="Xem và cập nhật dữ liệu tài khoản." close={() => setSelectedId(null)} />{detailQuery.isLoading ? <DataState title="Đang tải tài khoản..." /> : selected && <><div className="account-detail-summary"><div><small>Tên đăng nhập</small><strong>{selected.username}</strong></div><div><small>Trạng thái</small><span className={`pill ${selected.is_active ? "is-success" : "is-muted"}`}>{selected.is_active ? "Đang hoạt động" : "Tạm khóa"}</span></div></div><div className="form-grid two-columns"><label><span>Email</span><input type="email" value={editEmail} onChange={(event) => setEditEmail(event.target.value)} /></label><RoleSelect roles={roles} value={String(selected.role.id)} change={(value) => roleMutation.mutate({ id: selected.id, roleId: Number(value) })} /></div><MutationError mutation={emailMutation} /><MutationError mutation={roleMutation} /><div className="modal-actions"><button className={`button ${selected.is_active ? "danger-button" : "outline"}`} type="button" onClick={() => statusMutation.mutate({ id: selected.id, active: !selected.is_active })}>{selected.is_active ? "Khóa tài khoản" : "Mở tài khoản"}</button><button className="button navy" type="button" onClick={() => emailMutation.mutate({ id: selected.id, email: editEmail })}>Lưu email</button></div></>}</div></div>}
  </section>;
}

function ModalHeader({ icon, title, description, close }) { return <div className="modal-heading"><div><span className="metric-icon blue">{icon}</span><div><h2>{title}</h2><p>{description}</p></div></div><button className="modal-close" type="button" onClick={close}>×</button></div>; }
function Field({ label, type = "text", value, change }) {
  const isPassword = type === "password";
  const isUsername = label === "Tên đăng nhập";
  return <label><span>{label} <em>*</em></span><input type={type} minLength={isPassword ? 8 : isUsername ? 3 : undefined} maxLength={isPassword ? 128 : isUsername ? 100 : undefined} pattern={isUsername ? "[a-zA-Z0-9._-]+" : undefined} title={isUsername ? "Chỉ dùng chữ cái không dấu, số, dấu chấm, gạch dưới hoặc gạch ngang" : undefined} value={value} onChange={(event) => change(event.target.value)} required /></label>;
}
function RoleSelect({ roles, value, change }) { return <label><span>Vai trò <em>*</em></span><select value={value} onChange={(event) => change(event.target.value)} required>{roles.map((role) => <option value={role.id} key={role.id}>{ROLE_LABELS[role.name] ?? role.name}</option>)}</select></label>; }
function MutationError({ mutation }) { return mutation.isError ? <p className="form-error">{mutation.error.message}</p> : null; }
function ModalActions({ close, pending, label }) { return <div className="modal-actions"><button className="button ghost" type="button" onClick={close}>Hủy</button><button className="button navy" type="submit" disabled={pending}>{pending ? "Đang lưu..." : label}</button></div>; }

