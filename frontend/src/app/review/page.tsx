"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  CheckSquare,
  AlertTriangle,
  ArrowRight,
  RefreshCw,
  Eye,
  CheckCircle2,
  FileText,
} from "lucide-react";
import { api } from "@/lib/api";
import { Question } from "@/lib/types";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { StatusBadge } from "@/components/ui/Badge";
import { EmptyState } from "@/components/ui/EmptyState";

export default function GlobalReviewQueuePage() {
  const router = useRouter();
  const [questions, setQuestions] = useState<Question[]>([]);
  const [loading, setLoading] = useState(true);
  const [approvingId, setApprovingId] = useState<string | null>(null);

  const fetchReviewQueue = async () => {
    setLoading(true);
    try {
      const data = await api.review.getQueue();
      setQuestions(data);
    } catch (err: any) {
      if (err.status === 401) router.push("/login");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchReviewQueue();
  }, []);

  const handleQuickApprove = async (q: Question) => {
    setApprovingId(q.id);
    try {
      await api.questions.patch(q.id, {
        status: "VERIFIED",
        review_required: false,
        is_reviewed: true,
      });
      // Remove from queue
      setQuestions((prev) => prev.filter((item) => item.id !== q.id));
    } catch (err: any) {
      alert(err.message || "Failed to approve question.");
    } finally {
      setApprovingId(null);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-text flex items-center gap-2">
            Human Review Queue
            <span className="text-xs font-semibold px-2 py-0.5 bg-warning-light text-warning border border-warning/20 rounded-full">
              {questions.length} pending
            </span>
          </h1>
          <p className="text-xs text-text-muted mt-0.5">
            Questions flagged with low confidence, ambiguous boundaries, or uncertain answers
          </p>
        </div>
        <Button variant="outline" size="sm" onClick={fetchReviewQueue} disabled={loading}>
          <RefreshCw className={`w-3.5 h-3.5 mr-1.5 ${loading ? "animate-spin" : ""}`} />
          Refresh
        </Button>
      </div>

      {/* Queue List */}
      {questions.length === 0 ? (
        <Card className="p-8">
          <EmptyState
            icon={<CheckCircle2 className="w-8 h-8 text-success" />}
            title="Review Queue is Clean"
            description="Nothing requires human review. All extracted questions meet high confidence thresholds or have already been approved."
          />
        </Card>
      ) : (
        <div className="space-y-3">
          {questions.map((q) => (
            <Card
              key={q.id}
              className="p-5 border-l-4 border-l-warning hover:border-slate-300 transition-colors"
            >
              <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-2">
                    <span className="font-mono text-xs font-bold text-primary bg-primary-light px-2 py-0.5 rounded">
                      Q{q.question_number}
                    </span>
                    <StatusBadge status={q.status} />
                    <span className="text-[11px] font-mono font-medium text-warning">
                      Confidence: {(q.confidence * 100).toFixed(0)}%
                    </span>
                    <span className="text-[11px] text-text-muted">
                      Source pages: [{q.source_pages.join(", ")}]
                    </span>
                  </div>

                  <p className="text-xs font-medium text-text mb-3">
                    {q.question_text}
                  </p>

                  {/* Issues notice */}
                  <div className="p-2.5 bg-warning-light/50 border border-warning/20 rounded text-[11px] text-text-muted flex items-start gap-2">
                    <AlertTriangle className="w-3.5 h-3.5 text-warning shrink-0 mt-0.5" />
                    <span>
                      {q.answer_status === "INVALID"
                        ? "Invalid answer key mapping: key does not match any extracted question options."
                        : q.answer_status === "UNCERTAIN"
                        ? "Uncertain answer key mapping. Review question prompt and options against source document."
                        : "Extraction confidence is below automated verification threshold (0.90)."}
                    </span>
                  </div>
                </div>

                <div className="shrink-0 flex sm:flex-col gap-2">
                  <Link href={`/questions/${q.id}`}>
                    <Button size="sm" variant="outline" className="w-full">
                      <Eye className="w-3.5 h-3.5 mr-1" /> Inspect & Edit
                    </Button>
                  </Link>
                  <Button
                    size="sm"
                    variant="primary"
                    isLoading={approvingId === q.id}
                    onClick={() => handleQuickApprove(q)}
                    className="w-full"
                  >
                    <CheckCircle2 className="w-3.5 h-3.5 mr-1" /> Approve
                  </Button>
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
