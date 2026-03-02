import type { ButtonHTMLAttributes, InputHTMLAttributes } from "react";
import { createContext, useContext, useEffect } from "react";
import { X } from "lucide-react";
import toast, { Toaster } from "react-hot-toast";

// ---------------------------------------------------------------------------
// Button
// ---------------------------------------------------------------------------

export type ButtonVariant = "primary" | "secondary" | "danger";

export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  loading?: boolean;
}

export function Button({
  variant = "primary",
  loading = false,
  disabled,
  className = "",
  children,
  ...props
}: ButtonProps) {
  const variantStyles: Record<ButtonVariant, string> = {
    primary:
      "bg-primary hover:bg-primary-hover text-white border-transparent shadow-sm",
    secondary:
      "bg-transparent border-2 border-border text-text hover:bg-surface hover:border-text-muted",
    danger:
      "bg-danger hover:bg-danger-hover text-white border-transparent shadow-sm",
  };

  return (
    <button
      type="button"
      disabled={disabled || loading}
      className={`
        inline-flex items-center justify-center gap-2 h-9 px-4 rounded-md font-medium
        transition-colors duration-150 disabled:opacity-50 disabled:cursor-not-allowed
        ${variantStyles[variant]}
        ${className}
      `}
      {...props}
    >
      {loading ? (
        <span className="size-4 animate-spin rounded-full border-2 border-current border-t-transparent" />
      ) : (
        children
      )}
    </button>
  );
}

// ---------------------------------------------------------------------------
// Input
// ---------------------------------------------------------------------------

export interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
}

export function Input({
  label,
  error,
  id,
  className = "",
  ...props
}: InputProps) {
  const inputId = id ?? `input-${Math.random().toString(36).slice(2, 9)}`;

  return (
    <div className="w-full">
      {label && (
        <label
          htmlFor={inputId}
          className="block text-sm font-medium text-text mb-1.5"
        >
          {label}
        </label>
      )}
      <input
        id={inputId}
        className={`
          w-full h-10 px-3 rounded-lg border border-border
          bg-bg text-text placeholder:text-text-muted
          focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-1
          disabled:opacity-50 disabled:cursor-not-allowed
          ${error ? "border-danger focus:ring-danger" : ""}
          ${className}
        `}
        aria-invalid={!!error}
        aria-describedby={error ? `${inputId}-error` : undefined}
        {...props}
      />
      {error && (
        <p id={`${inputId}-error`} className="mt-1.5 text-sm text-danger" role="alert">
          {error}
        </p>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Card
// ---------------------------------------------------------------------------

export interface CardProps {
  children: React.ReactNode;
  className?: string;
}

export function Card({ children, className = "" }: CardProps) {
  return (
    <div
      className={`
        bg-white border border-border rounded-lg p-6
        shadow-[0_1px_3px_rgba(0,0,0,0.1)]
        ${className}
      `}
    >
      {children}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Badge
// ---------------------------------------------------------------------------

export type BadgeVariant = "success" | "warning" | "danger" | "default" | "info";

export interface BadgeProps {
  children: React.ReactNode;
  variant?: BadgeVariant;
  className?: string;
}

export function Badge({
  children,
  variant = "default",
  className = "",
}: BadgeProps) {
  const variantStyles: Record<BadgeVariant, string> = {
    success: "bg-success/10 text-success border-success/30",
    warning: "bg-warning/10 text-warning border-warning/30",
    danger: "bg-danger/10 text-danger border-danger/30",
    default: "bg-surface text-text-muted border-border",
    info: "bg-primary/10 text-primary border-primary/30",
  };

  return (
    <span
      className={`
        inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-medium
        ${variantStyles[variant]}
        ${className}
      `}
    >
      {children}
    </span>
  );
}

// ---------------------------------------------------------------------------
// Modal
// ---------------------------------------------------------------------------

const ModalContext = createContext<{ onClose: () => void } | null>(null);

export interface ModalProps {
  open: boolean;
  onClose: () => void;
  title?: string;
  children: React.ReactNode;
  className?: string;
}

export function Modal({ open, onClose, title, children, className = "" }: ModalProps) {
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    if (open) {
      document.addEventListener("keydown", handleEscape);
      document.body.style.overflow = "hidden";
    }
    return () => {
      document.removeEventListener("keydown", handleEscape);
      document.body.style.overflow = "";
    };
  }, [open, onClose]);

  if (!open) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4"
      role="dialog"
      aria-modal="true"
      aria-labelledby={title ? "modal-title" : undefined}
    >
      {/* Backdrop */}
      <div
        className="modal-backdrop absolute inset-0 bg-black/40 backdrop-blur-sm"
        onClick={onClose}
        aria-hidden="true"
      />

      {/* Panel */}
      <div
        className={`modal-panel relative w-full max-w-[480px] max-h-[90vh] overflow-auto bg-white rounded-lg shadow-xl ${className}`}
      >
        <ModalContext.Provider value={{ onClose }}>
          <div className="flex items-center justify-between px-6 pt-6 pb-4 border-b border-border">
            {title ? (
              <h2 id="modal-title" className="text-lg font-semibold text-text">
                {title}
              </h2>
            ) : (
              <span />
            )}
            <button
              type="button"
              onClick={onClose}
              className="p-1.5 rounded-md text-text-muted hover:text-text hover:bg-surface transition-colors ml-auto"
              aria-label="Close modal"
            >
              <X className="size-5" />
            </button>
          </div>
          <div className="px-6 py-6">{children}</div>
        </ModalContext.Provider>
      </div>
    </div>
  );
}

export function useModal() {
  const ctx = useContext(ModalContext);
  return ctx;
}

// ---------------------------------------------------------------------------
// Toast (react-hot-toast wrapper)
// ---------------------------------------------------------------------------

export { Toaster };

export type ToastVariant = "success" | "error" | "info";

export interface ShowToastOptions {
  duration?: number;
}

export function showToast(
  message: string,
  variant: ToastVariant = "info",
  options?: ShowToastOptions
) {
  const opts = { duration: options?.duration ?? 4000 };

  switch (variant) {
    case "success":
      return toast.success(message, opts);
    case "error":
      return toast.error(message, opts);
    case "info":
    default:
      return toast(message, opts);
  }
}

// ---------------------------------------------------------------------------
// Skeleton
// ---------------------------------------------------------------------------

export interface SkeletonProps {
  width?: string | number;
  height?: string | number;
  className?: string;
}

export function Skeleton({
  width,
  height,
  className = "",
}: SkeletonProps) {
  const style: React.CSSProperties = {};
  if (width !== undefined) style.width = typeof width === "number" ? `${width}px` : width;
  if (height !== undefined) style.height = typeof height === "number" ? `${height}px` : height;

  return (
    <div
      className={`skeleton ${className}`}
      style={Object.keys(style).length ? style : undefined}
      role="status"
      aria-label="Loading"
    />
  );
}

// ---------------------------------------------------------------------------
// Table
// ---------------------------------------------------------------------------

export interface TableProps {
  children: React.ReactNode;
  className?: string;
}

export function Table({ children, className = "" }: TableProps) {
  return (
    <div className="w-full overflow-x-auto">
      <table className={`w-full text-left ${className}`}>{children}</table>
    </div>
  );
}

export function TableHeader({ children, className = "" }: { children: React.ReactNode; className?: string }) {
  return (
    <thead>
      <tr className={className}>{children}</tr>
    </thead>
  );
}

export function TableRow({
  children,
  className = "",
  ...props
}: React.HTMLAttributes<HTMLTableRowElement> & { children: React.ReactNode; className?: string }) {
  return (
    <tr
      className={`
        border-b border-border last:border-b-0
        hover:bg-surface transition-colors
        ${className}
      `}
      {...props}
    >
      {children}
    </tr>
  );
}

export function TableCell({
  children,
  className = "",
  header,
  ...props
}: React.TdHTMLAttributes<HTMLTableCellElement> & {
  children: React.ReactNode;
  className?: string;
  header?: boolean;
}) {
  const base = "px-4 py-3 text-sm text-text";

  if (header) {
    return (
      <th className={`${base} font-medium text-text-muted ${className}`}>
        {children}
      </th>
    );
  }

  return <td className={`${base} ${className}`} {...props}>{children}</td>;
}
