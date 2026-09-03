export const CONTRACT_STATUS_OPTIONS = ["DRAFT", "SUBMITTED", "ACTIVE", "EXPIRED"];

const statusMeta = {
  DRAFT: {
    label: "DRAFT",
    detailLabel: "BẢN NHÁP",
    tone: "amber",
  },
  SUBMITTED: {
    label: "SUBMITTED",
    detailLabel: "CHỜ DUYỆT",
    tone: "blue",
  },
  ACTIVE: {
    label: "ACTIVE",
    detailLabel: "ĐANG HIỆU LỰC",
    tone: "green",
  },
  EXPIRED: {
    label: "EXPIRED",
    detailLabel: "HẾT HẠN",
    tone: "neutral",
  },
};

export function getStatusMeta(status) {
  return statusMeta[status] ?? {
    label: status || "UNKNOWN",
    detailLabel: status || "UNKNOWN",
    tone: "neutral",
  };
}

export function formatContractDate(value) {
  if (!value) {
    return "-";
  }

  return new Intl.DateTimeFormat("vi-VN", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
  }).format(new Date(value));
}

export function formatContractCurrency(value) {
  if (value === null || value === undefined || value === "") {
    return "-";
  }

  return new Intl.NumberFormat("vi-VN", {
    maximumFractionDigits: 0,
  }).format(Number(value));
}

export function formatCompactContractValue(value) {
  const amount = Number(value || 0);

  if (amount >= 1_000_000_000) {
    return `${new Intl.NumberFormat("vi-VN", {
      maximumFractionDigits: 1,
    }).format(amount / 1_000_000_000)}B`;
  }

  if (amount >= 1_000_000) {
    return `${new Intl.NumberFormat("vi-VN", {
      maximumFractionDigits: 1,
    }).format(amount / 1_000_000)}M`;
  }

  return formatContractCurrency(amount);
}

export function getContractLineTotal(service) {
  return Number(service.service_price || 0) * Number(service.quantity || 0);
}

export function formatUpdatedAt(value) {
  if (!value) {
    return "Chưa cập nhật";
  }

  const timestamp = new Date(value).getTime();
  if (Number.isNaN(timestamp)) {
    return "Chưa cập nhật";
  }

  const diffMinutes = Math.max(0, Math.round((Date.now() - timestamp) / 60000));
  if (diffMinutes < 1) {
    return "Vừa cập nhật";
  }

  if (diffMinutes < 60) {
    return `${diffMinutes} phút trước`;
  }

  const diffHours = Math.round(diffMinutes / 60);
  if (diffHours < 24) {
    return `${diffHours} giờ trước`;
  }

  return formatContractDate(value);
}
