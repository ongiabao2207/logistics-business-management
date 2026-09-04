import axios from "axios";

import { clearAuthToken, getAuthToken } from "./authToken";

function translateApiMessage(message) {
  if (typeof message !== "string") return message;
  const exact = {
    "Contract is not valid for the payment period": "Hợp đồng không còn hiệu lực trong kỳ thanh toán đã chọn.",
    "No production data exists for the payment period": "Không có dữ liệu sản lượng trong kỳ thanh toán đã chọn.",
    "Production data does not belong to the payment period": "Dữ liệu sản lượng không thuộc kỳ thanh toán đã chọn.",
    "Production data must be confirmed or reconciled": "Dữ liệu sản lượng phải được khóa hoặc phê duyệt.",
    "Confirmed production quantity must be positive": "Sản lượng xác nhận phải lớn hơn 0.",
    "Applicable unit price must not be negative": "Đơn giá áp dụng không được là số âm.",
    "A payment statement already exists for this contract and payment period": "Đã tồn tại bảng thanh toán cho hợp đồng và kỳ này.",
    "Payment statement was not found": "Không tìm thấy bảng thanh toán.",
    "Payment must contain at least one service line": "Bảng thanh toán phải có ít nhất một hạng mục.",
    "Payment must retain at least one service line": "Bảng thanh toán phải giữ lại ít nhất một hạng mục.",
    "Adjustment must change at least one payment line": "Điều chỉnh phải làm thay đổi ít nhất một hạng mục.",
    "Adjustment must change the tax rate": "Thuế suất mới phải khác thuế suất hiện tại.",
    "Only pending payments can be reviewed": "Chỉ bảng thanh toán đang chờ duyệt mới được phê duyệt.",
    "Payment can only be adjusted after rejection or a revision request": "Chỉ được điều chỉnh khi bảng thanh toán bị từ chối hoặc được yêu cầu chỉnh sửa.",
    "This approval revision request has already been applied": "Yêu cầu chỉnh sửa này đã được áp dụng trước đó.",
  };
  if (exact[message]) return exact[message];

  let match = message.match(/^Billing quantity for (.+) must not exceed the confirmed production quantity$/);
  if (match) return `Sản lượng thanh toán của dịch vụ ${match[1]} không được lớn hơn sản lượng xác nhận.`;
  match = message.match(/^Payment in (.+) cannot be edited$/);
  if (match) return `Không thể chỉnh sửa bảng thanh toán ở trạng thái ${match[1]}.`;
  match = message.match(/^Payment in (.+) cannot be submitted$/);
  if (match) return `Không thể gửi duyệt bảng thanh toán ở trạng thái ${match[1]}.`;
  match = message.match(/^No applicable price for service (.+)$/);
  if (match) return `Không có đơn giá phù hợp cho dịch vụ ${match[1]}.`;
  if (/[À-ỹ]/u.test(message)) return message;
  return "Yêu cầu không thể thực hiện. Vui lòng kiểm tra dữ liệu và thử lại.";
}

function translateValidationError(item) {
  const field = item.loc?.at(-1);
  const labels = {
    username: "Tên đăng nhập",
    email: "Email",
    password: "Mật khẩu",
    role_id: "Vai trò",
    customer_id: "Khách hàng",
    contract_id: "Hợp đồng",
    period_start: "Ngày bắt đầu",
    period_end: "Ngày kết thúc",
    tax_rate: "Thuế suất",
    service_id: "Dịch vụ",
    billing_quantity: "Sản lượng thanh toán",
    revision_request_id: "Mã yêu cầu chỉnh sửa",
    adjustment_note: "Ghi chú điều chỉnh",
    reason: "Lý do điều chỉnh",
  };
  const label = labels[field] ?? "Dữ liệu";
  const type = item.type ?? "";

  if (type === "missing") return `${label}: không được để trống`;
  if (type === "greater_than") return `${label}: phải lớn hơn ${item.ctx?.gt ?? 0}`;
  if (type === "greater_than_equal") return `${label}: phải lớn hơn hoặc bằng ${item.ctx?.ge}`;
  if (type === "less_than_equal") return `${label}: không được lớn hơn ${item.ctx?.le}`;
  if (type === "string_too_short") return `${label}: nội dung quá ngắn`;
  if (type === "string_too_long") return `${label}: nội dung quá dài`;
  if (type.includes("date")) return `${label}: ngày không hợp lệ`;
  if (type.includes("decimal") || type.includes("number") || type.includes("float") || type.includes("int")) {
    return `${label}: phải là một số hợp lệ`;
  }
  return `${label}: dữ liệu không hợp lệ`;
}

export const httpClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? "",
  headers: {
    "Content-Type": "application/json",
  },
});

httpClient.interceptors.request.use((config) => {
  const token = getAuthToken();

  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }

  return config;
});

httpClient.interceptors.response.use(
  (response) => response.data,
  (error) => {
    const status = error.response?.status;
    const requestUrl = error.config?.url ?? "";
    if (status === 401 && !requestUrl.endsWith("/api/v1/auth/login")) {
      clearAuthToken();
      const returnTo = `${window.location.pathname}${window.location.search}`;
      window.location.assign(`/login?expired=1&returnTo=${encodeURIComponent(returnTo)}`);
    }
    const detail = error.response?.data?.detail;
    const message = typeof detail === "string"
      ? detail
      : Array.isArray(detail)
        ? detail.map(translateValidationError).join(". ")
        : "Không thể kết nối đến hệ thống. Vui lòng thử lại.";

    return Promise.reject({
      status,
      message: status === 401 ? "Phiên đăng nhập đã hết hạn. Vui lòng đăng nhập lại." : translateApiMessage(message),
      originalError: error,
    });
  },
);
