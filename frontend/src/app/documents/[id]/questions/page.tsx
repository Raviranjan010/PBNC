"use client";

import React, { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import {
  HelpCircle,
  Search,
  Filter,
  CheckCircle2,
  AlertTriangle,
  ArrowLeft,
  ArrowRight,
  RefreshCw,
  Eye,
} from "lucide-react";
import { api } from "@/lib/api";
import { Question, DocumentDetail } from "@/lib/types";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { StatusBadge } from "@/components/ui/Badge";
import { EmptyState } from "@/components/ui/EmptyState";

export default function DocumentQuestionsPage() {
  const params = useParams();
  const router = useRouter();
  const docId = params.id as string;

  const [doc, setDoc] = useState<DocumentDetail | null>(null);
  const [questions, setQuestions] = useState<Question[]>([]);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState<string>("ALL");
  const [loading, setLoading] = useState(true);

  const fetchQuestions = async () => {
    setLoading(true);
    try {
      const [docData, qData] = await Promise.all([
        api.documents.get(docId),
        api.questions.listForDoc(docId, {
          status: statusFilter !== "ALL" ? statusFilter : undefined,
          search: search || undefined,
        }),
      ]);
      setDoc(docData);
      setQuestions(qData.items);
    } catch (err: any) {
      if (err.status === 401) router.push("/login");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchQuestions();
  }, [docId, statusFilter]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    fetchQuestions();
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 text-xs text-text-muted">
            <Link href="/documents" className="hover:text-text">
              Documents
            </Link>
            <span>/</span>
            <Link href={`/documents/${docId}`} className="hover:text-text">
              {doc?.original_filename || "Details"}
            </Link>
            <span>/</span>
            <span className="text-text font-medium">Questions</span>
          </div>
          <h1 className="text-xl font-bold text-text mt-1 flex items-center gap-2">
            Extracted Questions
            <span className="text-xs font-normal px-2 py-0.5 bg-slate-100 border border-border rounded text-text-muted">
              {questions.length} items
            </span>
          </h1>
        </div>

        <div className="flex items-center gap-2">
          <Link href={`/documents/${docId}/viewer`}>
            <Button variant="outline" size="sm">
              <Eye className="w-3.5 h-3.5 mr-1.5" />
              Source Viewer
            </Button>
          </Link>
          <Button variant="outline" size="sm" onClick={fetchQuestions} disabled={loading}>
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
          </Button>
        </div>
      </div>

      {/* Filters Bar */}
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3">
        <form onSubmit={handleSearchSubmit} className="relative flex-1 max-w-sm">
          <Search className="w-3.5 h-3.5 text-text-muted absolute left-3 top-2.5" />
          <input
            type="text"
            placeholder="Search questions by text..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-8 pr-3 py-1.5 text-xs rounded-md border border-border bg-surface text-text focus:outline-none focus:ring-2 focus:ring-primary/30"
          />
        </form>

        <div className="flex items-center gap-1.5 overflow-x-auto pb-1 sm:pb-0 text-xs">
          {["ALL", "VERIFIED", "PARTIAL", "REVIEW_REQUIRED"].map((st) => (
            <button
              key={st}
              onClick={() => setStatusFilter(st)}
              className={`px-2.5 py-1 rounded font-medium transition-colors ${
                statusFilter === st
                  ? "bg-primary text-white"
                  : "bg-surface text-text-muted hover:text-text border border-border"
              }`}
            >
              {st.replace("_", " ")}
            </button>
          ))}
        </div>
      </div>

      {/* Questions List */}
      {questions.length === 0 ? (
        <EmptyState
          title="No questions found"
          description="No questions match your current query or document extraction returned zero results."
        />
      ) : (
        <div className="space-y-3">
          {questions.map((q) => (
            <Card
              key={q.id}
              className="p-5 hover:border-slate-300 transition-colors"
            >
              <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-3">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-2">
                    <span className="font-mono text-xs font-bold text-primary bg-primary-light px-2 py-0.5 rounded">
                      Q{q.question_number}
                    </span>
                    <StatusBadge status={q.status} />
                    <span className="text-[11px] text-text-muted">
                      Source pages: [{q.source_pages.join(", ")}]
                    </span>
                    <span className="text-[11px] font-mono text-text-muted">
                      Confidence: {(q.confidence * 100).toFixed(0)}%
                    </span>
                  </div>

                  <p className="text-sm font-medium text-text mb-3">
                    {q.question_text}
                  </p>

                  {/* Options */}
                  {q.options && q.options.length > 0 && (
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 my-2">
                      {q.options.map((opt) => {
                        const isAnswer = q.answer === opt.option_key;
                        return (
                          <div
                            key={opt.option_key}
                            className={`px-3 py-2 text-xs rounded border flex items-start gap-2 ${
                              isAnswer
                                ? "bg-success-light border-success/30 font-medium text-success"
                                : "bg-slate-50 border-border text-text"
                            }`}
                          >
                            <span className="font-mono font-bold shrink-0">
                              ({opt.option_key})
                            </span>
                            <span>{opt.option_text}</span>
                          </div>
                        );
                      })}
                    </div>
                  )}

                  {/* Answer Provenance */}
                  <div className="mt-3 flex items-center gap-3 text-xs">
                    <span className="text-text-muted">
                      Answer:{" "}
                      <strong className="text-text font-mono">
                        {q.answer || "None"}
                      </strong>
                    </span>
                    {q.answer_status === "UNCERTAIN" && (
                      <span className="text-warning text-[11px] font-medium flex items-center gap-1">
                        <AlertTriangle className="w-3 h-3" /> Uncertain solution
                      </span>
                    )}
                  </div>
                </div>

                <div className="shrink-0 flex sm:flex-col gap-2">
                  <Link href={`/questions/${q.id}`}>
                    <Button size="sm" variant="outline">
                      Inspect & Edit <ArrowRight className="w-3.5 h-3.5 ml-1" />
                    </Button>
                  </Link>
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
