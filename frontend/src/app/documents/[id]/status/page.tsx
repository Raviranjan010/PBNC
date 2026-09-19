"use client";

import React, { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import {
  CheckCircle2,
  Clock,
  AlertCircle,
  FileText,
  ArrowRight,
  RefreshCw,
} from "lucide-react";
import { api } from "@/lib/api";
import { ProcessingStatus, DocumentDetail } from "@/lib/types";
import { Card, CardHeader } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { StatusBadge } from "@/components/ui/Badge";

export default function DocumentStatusPage() {
  const params = useParams();
  const router = useRouter();
  const docId = params.id as string;

  const [statusData, setStatusData] = useState<ProcessingStatus | null>(null);
  const [docDetail, setDocDetail] = useState<DocumentDetail | null>(null);
  const [loading, setLoading] = useState(true);

  // Poll real status every 2 seconds until terminal state (COMPLETED, PARTIAL, REVIEW_REQUIRED, FAILED)
  useEffect(() => {
    let interval: any = null;

    const fetchStatus = async () => {
      try {
        const [stat, doc] = await Promise.all([
          api.documents.getStatus(docId),
          api.documents.get(docId),
        ]);
        setStatusData(stat);
        setDocDetail(doc);

        const terminalStates = ["COMPLETED", "PARTIAL", "REVIEW_REQUIRED", "FAILED"];
        if (terminalStates.includes(stat.status.toUpperCase())) {
          clearInterval(interval);
        }
      } catch (err) {
        // error handling
      } finally {
        setLoading(false);
      }
    };

    fetchStatus();
    interval = setInterval(fetchStatus, 2000);
    return () => clearInterval(interval);
  }, [docId]);

  const pipelineStages = [
    { key: "INITIALIZING", label: "Document validated & queued" },
    { key: "EXTRACTING_TEXT", label: "Text extraction & page rendering" },
    { key: "OCR_PROCESSING", label: "Optical character recognition (OCR)" },
    { key: "EXTRACTING_QUESTIONS", label: "Structured question & option parsing" },
    { key: "MATCHING_ANSWERS", label: "Answer key detection & solution mapping" },
    { key: "VALIDATING", label: "Multi-signal confidence scoring & validation" },
  ];

  const currentStep = statusData?.current_step || "";
  const isTerminal = ["COMPLETED", "PARTIAL", "REVIEW_REQUIRED", "FAILED"].includes(
    statusData?.status?.toUpperCase() || ""
  );

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <div className="flex items-center gap-2">
            <Link
              href="/documents"
              className="text-xs text-text-muted hover:text-text"
            >
              Documents
            </Link>
            <span className="text-xs text-text-muted">/</span>
            <span className="text-xs font-medium text-text truncate max-w-[200px]">
              {docDetail?.original_filename || docId}
            </span>
          </div>
          <h1 className="text-xl font-bold text-text mt-1">Processing Status</h1>
        </div>
        {statusData && <StatusBadge status={statusData.status} />}
      </div>

      {/* Stage Progression Stepper */}
      <Card className="p-6">
        <CardHeader
          title="Live Pipeline Execution"
          subtitle={
            isTerminal
              ? "Document processing completed."
              : "Asynchronous worker actively processing stages..."
          }
          action={
            !isTerminal ? (
              <div className="flex items-center gap-1.5 text-xs text-primary font-medium">
                <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                Live Polling
              </div>
            ) : null
          }
        />

        <div className="space-y-4 my-6">
          {pipelineStages.map((stage, idx) => {
            // Determine stage state
            const hasCompleted = statusData?.step_details?.some(
              (d) => d.step === stage.key
            ) || isTerminal;
            const isCurrent = currentStep === stage.key && !isTerminal;

            return (
              <div key={stage.key} className="flex items-start gap-3.5">
                <div className="mt-0.5">
                  {hasCompleted ? (
                    <div className="w-5 h-5 rounded-full bg-success text-white flex items-center justify-center text-xs">
                      ✓
                    </div>
                  ) : isCurrent ? (
                    <div className="w-5 h-5 rounded-full border-2 border-primary bg-primary-light flex items-center justify-center">
                      <div className="w-2 h-2 rounded-full bg-primary animate-pulse" />
                    </div>
                  ) : (
                    <div className="w-5 h-5 rounded-full border-2 border-slate-300 bg-white" />
                  )}
                </div>
                <div className="flex-1">
                  <div
                    className={`text-xs font-semibold ${
                      hasCompleted
                        ? "text-text"
                        : isCurrent
                        ? "text-primary"
                        : "text-text-muted"
                    }`}
                  >
                    {stage.label}
                  </div>
                  {/* Detailed message from worker if executed */}
                  {statusData?.step_details?.find((d) => d.step === stage.key)?.message && (
                    <div className="text-[11px] text-text-muted mt-0.5">
                      {statusData.step_details.find((d) => d.step === stage.key)?.message}
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>

        {/* Action Button once completed */}
        {isTerminal && (
          <div className="mt-6 pt-4 border-t border-border flex items-center justify-between">
            <div className="text-xs text-text-muted">
              {docDetail?.questions_count} questions extracted
            </div>
            <div className="flex gap-2">
              <Link href={`/documents/${docId}`}>
                <Button variant="outline" size="sm">
                  Document Overview
                </Button>
              </Link>
              <Link href={`/documents/${docId}/questions`}>
                <Button size="sm">
                  View Questions <ArrowRight className="w-3.5 h-3.5 ml-1.5" />
                </Button>
              </Link>
            </div>
          </div>
        )}
      </Card>

      {/* Execution Logs */}
      {statusData?.step_details && statusData.step_details.length > 0 && (
        <Card className="p-4 bg-slate-900 text-slate-100 border-slate-800 font-mono text-[11px]">
          <div className="text-xs font-semibold text-slate-300 mb-2 font-sans flex items-center gap-1.5">
            <Clock className="w-3.5 h-3.5 text-primary" /> Execution Audit Trail
          </div>
          <div className="space-y-1 max-h-48 overflow-y-auto">
            {statusData.step_details.map((s, idx) => (
              <div key={idx} className="flex gap-3 text-slate-400">
                <span className="text-slate-500 shrink-0">
                  {new Date(s.timestamp).toLocaleTimeString()}
                </span>
                <span className="text-emerald-400 font-semibold shrink-0">[{s.step}]</span>
                <span className="text-slate-200">{s.message}</span>
              </div>
            ))}
          </div>
        </Card>
      )}
    </div>
  );
}
