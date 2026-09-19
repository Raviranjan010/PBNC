"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  Files,
  HelpCircle,
  CheckSquare,
  BarChart3,
  FileCode2,
  Settings as SettingsIcon,
} from "lucide-react";

export const Sidebar: React.FC = () => {
  const pathname = usePathname();

  const navItems = [
    { label: "Dashboard", href: "/dashboard", icon: LayoutDashboard },
    { label: "Documents", href: "/documents", icon: Files },
    { label: "Review Queue", href: "/review", icon: CheckSquare },
    { label: "Questions", href: "/questions", icon: HelpCircle },
    { label: "Analytics", href: "/analytics", icon: BarChart3 },
    { label: "API Docs", href: "/api-docs", icon: FileCode2 },
    { label: "Settings", href: "/settings", icon: SettingsIcon },
  ];

  return (
    <aside className="w-56 border-r border-border bg-surface flex flex-col shrink-0 min-h-[calc(100vh-3.5rem)]">
      <div className="p-3">
        <div className="text-[11px] font-semibold uppercase tracking-wider text-text-muted px-2.5 py-1.5">
          Workspace
        </div>
        <nav className="space-y-0.5">
          {navItems.map((item) => {
            const isActive = pathname === item.href || pathname.startsWith(`${item.href}/`);
            const Icon = item.icon;
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`flex items-center gap-2.5 px-3 py-2 rounded-md text-xs font-medium transition-colors ${
                  isActive
                    ? "bg-primary-light text-primary font-semibold"
                    : "text-text-muted hover:text-text hover:bg-slate-50"
                }`}
              >
                <Icon className={`w-4 h-4 ${isActive ? "text-primary" : "text-text-muted"}`} />
                <span>{item.label}</span>
              </Link>
            );
          })}
        </nav>
      </div>

      <div className="mt-auto p-4 border-t border-border bg-slate-50/50">
        <div className="text-[11px] font-medium text-text">Pipeline Status</div>
        <div className="flex items-center gap-2 mt-1.5">
          <div className="w-2 h-2 rounded-full bg-success animate-pulse" />
          <span className="text-[10px] text-text-muted">Workers Ready</span>
        </div>
      </div>
    </aside>
  );
};
