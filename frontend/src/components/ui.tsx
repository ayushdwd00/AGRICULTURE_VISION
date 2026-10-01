import type { ButtonHTMLAttributes, ReactNode } from "react";
import { LoaderCircle } from "lucide-react";

export function PageHeader({
  eyebrow,
  title,
  description,
  action,
}: {
  eyebrow: string;
  title: string;
  description: string;
  action?: ReactNode;
}) {
  return (
    <header className="page-heading">
      <div>
        <div className="eyebrow">{eyebrow}</div>
        <h1>{title}</h1>
        <p>{description}</p>
      </div>
      {action}
    </header>
  );
}

export function Card({
  children,
  className = "",
  padded = true,
}: {
  children: ReactNode;
  className?: string;
  padded?: boolean;
}) {
  return <section className={`card${padded ? " card-pad" : ""} ${className}`}>{children}</section>;
}

export function Field({
  label,
  id,
  children,
}: {
  label: string;
  id?: string;
  children: ReactNode;
}) {
  return (
    <label className="field-label" htmlFor={id}>
      <span className="label">{label}</span>
      {children}
    </label>
  );
}

export function Button({
  children,
  variant = "primary",
  loading = false,
  className = "",
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement> & {
  children: ReactNode;
  variant?: "primary" | "secondary" | "soft";
  loading?: boolean;
}) {
  const variantClass =
    variant === "secondary"
      ? "button-secondary"
      : variant === "soft"
        ? "button-soft"
        : "";
  return (
    <button
      {...props}
      className={`button ${variantClass} ${className}`}
      disabled={props.disabled || loading}
    >
      {loading ? <LoaderCircle size={15} className="spin-icon" /> : null}
      {children}
    </button>
  );
}

export function Alert({
  children,
  tone = "info",
}: {
  children: ReactNode;
  tone?: "info" | "success" | "error";
}) {
  return <div className={`alert alert-${tone}`} role={tone === "error" ? "alert" : "status"}>{children}</div>;
}

export function EmptyState({
  children,
  icon,
}: {
  children: ReactNode;
  icon?: ReactNode;
}) {
  return (
    <div className="empty-state">
      {icon}
      <div>{children}</div>
    </div>
  );
}
