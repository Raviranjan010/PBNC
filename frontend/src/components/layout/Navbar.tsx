"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { FileText, LogOut, User as UserIcon } from "lucide-react";
import { getUser, clearAuth, isAuthenticated } from "@/lib/auth";
import { User } from "@/lib/types";

export const Navbar: React.FC = () => {
  const router = useRouter();
  const [currentUser, setCurrentUser] = useState<User | null>(null);

  useEffect(() => {
    setCurrentUser(getUser());
    const handleAuthChange = () => setCurrentUser(getUser());
    window.addEventListener("papermind_auth_change", handleAuthChange);
    return () => window.removeEventListener("papermind_auth_change", handleAuthChange);
  }, []);

  const handleLogout = () => {
    clearAuth();
    router.push("/login");
  };

  return (
    <header className="h-14 border-b border-border bg-surface sticky top-0 z-30 px-4 md:px-6 flex items-center justify-between">
      {/* Brand */}
      <Link href="/dashboard" className="flex items-center gap-2.5">
        <div className="w-8 h-8 rounded bg-primary flex items-center justify-center text-white font-bold text-base shadow-sm">
          <span className="font-mono">P[M]</span>
        </div>
        <div>
          <span className="font-semibold text-text text-sm tracking-tight flex items-center gap-1.5">
            PaperMind
            <span className="text-[10px] uppercase font-bold tracking-wider px-1.5 py-0.2 bg-slate-100 text-text-muted rounded border border-border">
              v1.0
            </span>
          </span>
          <span className="hidden sm:block text-[10px] text-text-muted">
            From Documents to Structured Knowledge
          </span>
        </div>
      </Link>

      {/* User profile & actions */}
      <div className="flex items-center gap-3">
        {currentUser ? (
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2 text-xs text-text-muted bg-slate-50 px-2.5 py-1.5 rounded-md border border-border">
              <UserIcon className="w-3.5 h-3.5 text-primary" />
              <span className="font-medium text-text">{currentUser.email}</span>
            </div>
            <button
              onClick={handleLogout}
              className="p-1.5 text-text-muted hover:text-danger hover:bg-danger-light rounded-md transition-colors"
              title="Log out"
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        ) : (
          <div className="flex items-center gap-2">
            <Link
              href="/login"
              className="text-xs font-medium text-text px-3 py-1.5 rounded hover:bg-slate-100 transition-colors"
            >
              Sign In
            </Link>
            <Link
              href="/register"
              className="text-xs font-medium text-white bg-primary hover:bg-primary-dark px-3 py-1.5 rounded transition-colors"
            >
              Register
            </Link>
          </div>
        )}
      </div>
    </header>
  );
};
