import { paymentStatusClasses, paymentStatusLabels } from "../types/index.js";
export function PaymentStatus({ status }) { return <span className={`pay-status ${paymentStatusClasses[status] ?? ""}`}>{paymentStatusLabels[status] ?? status}</span>; }
