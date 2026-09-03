import { StatusBadge } from "../../../shared/components/StatusBadge.jsx";
import { paymentStatusLabels, paymentStatusTones } from "../types/index.js";
export function PaymentStatusBadge({ status }) { return <StatusBadge tone={paymentStatusTones[status] ?? "neutral"}>{paymentStatusLabels[status] ?? status}</StatusBadge>; }
