export function PaymentState({ title, description }) { return <div className="pay-state"><strong>{title}</strong>{description ? <p>{description}</p> : null}</div>; }
