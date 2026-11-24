// Shows a loading, error or empty message in a consistent way.
export default function StatusMessage({ type, title, text, actionLabel, onAction }) {
  const isError = type === "error";
  return (
    <div
      className={`status status-${type}`}
      role={isError ? "alert" : "status"}
      aria-live={isError ? "assertive" : "polite"}
    >
      {title && <strong>{title}</strong>}
      {text && <p>{text}</p>}
      {actionLabel && onAction && (
        <button type="button" className="button" onClick={onAction}>
          {actionLabel}
        </button>
      )}
    </div>
  );
}