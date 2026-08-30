export function DataState({ title = "No records yet", description }) {
  return (
    <div className="data-state">
      <strong>{title}</strong>
      {description ? <p>{description}</p> : null}
    </div>
  );
}
