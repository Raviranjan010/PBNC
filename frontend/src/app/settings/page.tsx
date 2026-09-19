"use client";

import React, { useEffect, useState } from "react";
import { Settings as SettingsIcon, Cpu, ShieldCheck, Database, CheckCircle2 } from "lucide-react";
import { Card, CardHeader } from "@/components/ui/Card";
import { getUser } from "@/lib/auth";
import { User } from "@/lib/types";

export default function SettingsPage() {
  const [user, setUser] = useState<User | null>(null);

  useEffect(() => {
    setUser(getUser());
  }, []);

  return (
    <div className="space-y-6 max-w-3xl">
      <div>
        <h1 className="text-xl font-bold text-text">Workspace Settings</h1>
        <p className="text-xs text-text-muted mt-0.5">
          System environment, AI providers, and extraction thresholds
        </p>
      </div>

      <Card className="p-5">
        <CardHeader title="User Profile" subtitle="Account details for the active session" />
        <dl className="space-y-2.5 text-xs mt-2">
          <div className="flex justify-between py-1.5 border-b border-border/50">
            <dt className="text-text-muted">Account Email</dt>
            <dd className="font-medium text-text">{user?.email || "—"}</dd>
          </div>
          <div className="flex justify-between py-1.5 border-b border-border/50">
            <dt className="text-text-muted">Account ID</dt>
            <dd className="font-mono text-text">{user?.id || "—"}</dd>
          </div>
          <div className="flex justify-between py-1.5 border-b border-border/50">
            <dt className="text-text-muted">Session Status</dt>
            <dd className="text-success font-medium flex items-center gap-1">
              <CheckCircle2 className="w-3.5 h-3.5" /> Authenticated
            </dd>
          </div>
        </dl>
      </Card>

      <Card className="p-5">
        <CardHeader
          title="AI & Intelligence Configuration"
          subtitle="Provider abstraction settings configured on backend"
        />
        <div className="space-y-3 text-xs mt-2">
          <div className="p-3 bg-slate-50 border border-border rounded-md flex items-center justify-between">
            <div className="flex items-center gap-2.5">
              <Cpu className="w-4 h-4 text-primary" />
              <div>
                <div className="font-semibold text-text">Active AI Provider</div>
                <div className="text-[11px] text-text-muted">Configurable via AI_PROVIDER env var</div>
              </div>
            </div>
            <span className="font-mono bg-white px-2.5 py-1 border border-border rounded font-bold text-primary">
              GEMINI / OPENAI / HEURISTIC
            </span>
          </div>

          <div className="p-3 bg-slate-50 border border-border rounded-md flex items-center justify-between">
            <div className="flex items-center gap-2.5">
              <ShieldCheck className="w-4 h-4 text-success" />
              <div>
                <div className="font-semibold text-text">Confidence Verification Threshold</div>
                <div className="text-[11px] text-text-muted">Questions scoring ≥ 0.90 are automatically verified</div>
              </div>
            </div>
            <span className="font-mono bg-white px-2.5 py-1 border border-border rounded font-bold text-success">
              0.90 (90%)
            </span>
          </div>

          <div className="p-3 bg-slate-50 border border-border rounded-md flex items-center justify-between">
            <div className="flex items-center gap-2.5">
              <Database className="w-4 h-4 text-warning" />
              <div>
                <div className="font-semibold text-text">Review Requirement Threshold</div>
                <div className="text-[11px] text-text-muted">Questions scoring &lt; 0.70 are flagged for human review</div>
              </div>
            </div>
            <span className="font-mono bg-white px-2.5 py-1 border border-border rounded font-bold text-warning">
              0.70 (70%)
            </span>
          </div>
        </div>
      </Card>
    </div>
  );
}
