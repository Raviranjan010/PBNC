import React from "react";

interface BadgeProps {
  children: React.ReactNode;
  variant?: "default" | "success" | "warning" | "danger" | "info" | "neutral";
  size?: "sm" | "md";
}

export const Badge: React.FC<BadgeProps> = ({
  children,
  variant = "default",
  size = "sm",
}) => {
  const sizeClasses = size === "sm" ? "px-2 py-0.5 text-xs" : "px-2.5 py-1 text-sm";

  const variantClasses = {
    default: "bg-primary-light text-primary border border-primary/20",
    success: "bg-success-light text-success border border-success/20",
    warning: "bg-warning-light text-warning border border-warning/20",
    danger: "bg-danger-light text-danger border border-danger/20",
    info: "bg-blue-50 text-blue-700 border border-blue-200",
    neutral: "bg-slate-100 text-slate-700 border border-slate-200",
  }[variant];

  return (
    <span
      className={`inline-flex items-center font-medium rounded-full ${sizeClasses} ${variantClasses}`}
    >
      {children}
    </span>
  );
};

export const StatusBadge: React.FC<{ status: string }> = ({ status }) => {
  const s = status.toUpperCase();
  if (s === "VERIFIED" || s === "COMPLETED") {
    return <Badge variant="success">{s}</Badge>;
  }
  if (s === "PARTIAL") {
    return <Badge variant="warning">PARTIAL</Badge>;
  }
  if (s === "REVIEW_REQUIRED" || s === "FAILED") {
    return <Badge variant="danger">{s.replace("_", " ")}</Badge>;
  }
  if (s === "PROCESSING" || s.startsWith("EXTRACTING") || s === "OCR_PROCESSING") {
    return <Badge variant="info">PROCESSING</Badge>;
  }
  return <Badge variant="neutral">{s}</Badge>;
};
