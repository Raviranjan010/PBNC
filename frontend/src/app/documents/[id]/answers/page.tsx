"use client";

import React, { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import {
  KeyRound,
  FileText,
  AlertTriangle,
  CheckCircle2,
  HelpCircle,
  ArrowLeft,
  ArrowRight,
  RefreshCw,
  Link2,
} from "lucide-react";
import { api } from "@/lib/api";
import { AnswerKey, Question, DocumentDetail } from "@/lib/types";
import { Card, CardHeader } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { StatusBadge } from "@/components/ui/Badge";
import { EmptyState } from "@/components/ui/EmptyState";

export default function DocumentAnswersPage() {
  const params = useParams();
  const router = useRouter();
  const docId = params.id as string;

  const [doc, setDoc] = useState<DocumentDetail | null>(null);
  const [answerKeys, setAnswerKeys] = useState<AnswerKey[]>([]);
  const [questions, setQuestions] = useState<Question[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [docRes, ansRes, qRes] = await Promise.all([
        api.documents.get(docId),
        api.answers.getForDoc(docId),
        api.questions.listForDoc(docId),
      ]);
      setDoc(docRes);
      setAnswerKeys(ansRes);
      setQuestions(qRes.items);
    } catch (err: any) {
      if (err.status === 401) router.push("/login");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [docId]);

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
            <span className="text-text font-medium">Answer Keys</span>
          </div>
          <h1 className="text-xl font-bold text-text mt-1 flex items-center gap-2">
            <KeyRound className="w-5 h-5 text-primary" />
            Detected Solutions & Answer Keys
          </h1>
        </div>
        <Button variant="outline" size="sm" onClick={fetchData} disabled={loading}>
          <RefreshCw className={`w-3.5 h-3.5 mr-1.5 ${loading ? "animate-spin" : ""}`} />
          Refresh
        </Button>
      </div>

      {/* Answer Key Origin Panel */}
      {answerKeys.length > 0 && (
        <Card className="p-5 bg-slate-50 border-border">
          <CardHeader
            title="Detected Answer Key Meta"
            subtitle="Extracted directly from document content"
          />
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs mt-2">
            <div className="p-3 bg-white rounded border border-border">
              <span className="text-text-muted block text-[11px]">Key Format</span>
              <span className="font-bold text-text uppercase">
                {answerKeys[0].detected_format || "INLINE"}
              </span>
            </div>
            <div className="p-3 bg-white rounded border border-border">
              <span className="text-text-muted block text-[11px]">Source Page</span>
              <span className="font-bold text-text">
                Page {answerKeys[0].source_page || "1"}
              </span>
            </div>
            <div className="p-3 bg-white rounded border border-border">
              <span className="text-text-muted block text-[11px]">Mapped Pairs</span>
              <span className="font-bold text-text font-mono">
                {Object.keys(answerKeys[0].parsed_mappings || {}).length} entries
              </span>
            </div>
          </div>

          {answerKeys[0].raw_key_text && (
            <div className="mt-3 p-3 bg-white rounded border border-border font-mono text-[11px] text-text-muted max-h-28 overflow-y-auto">
              <span className="font-sans font-semibold text-text block mb-1">
                Raw Key Snippet:
              </span>
              {answerKeys[0].raw_key_text}
            </div>
          )}
        </Card>
      )}

      {/* Questions to Answers Mapping Table */}
      <Card className="p-0 overflow-hidden">
        <div className="p-5 border-b border-border">
          <h3 className="text-sm font-semibold text-text">Question-to-Answer Association Matrix</h3>
          <p className="text-xs text-text-muted mt-0.5">
            Real Q &rarr; A mappings showing solution certainty and provenance
          </p>
        </div>

        {questions.length === 0 ? (
          <div className="p-8">
            <EmptyState
              title="No answer mappings found"
              description="No questions extracted or answer key associated with this document."
            />
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50 text-text-muted uppercase border-b border-border font-medium">
                <tr>
                  <th className="px-5 py-3">Question #</th>
                  <th className="px-4 py-3">Question Prompt</th>
                  <th className="px-4 py-3">Answer</th>
                  <th className="px-4 py-3">Solution Status</th>
                  <th className="px-4 py-3">Source Page</th>
                  <th className="px-4 py-3">Confidence</th>
                  <th className="px-5 py-3 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {questions.map((q) => {
                  const isUncertain = q.answer_status === "UNCERTAIN";
                  const hasAnswer = Boolean(q.answer);

                  return (
                    <tr key={q.id} className="hover:bg-slate-50/50 transition-colors">
                      <td className="px-5 py-3 font-mono font-bold text-primary">
                        Q{q.question_number}
                      </td>
                      <td className="px-4 py-3 text-text font-medium max-w-sm truncate">
                        {q.question_text}
                      </td>
                      <td className="px-4 py-3 font-mono font-bold text-sm">
                        {hasAnswer ? (
                          <span className="bg-slate-100 px-2 py-0.5 rounded border border-border">
                            {q.answer}
                          </span>
                        ) : (
                          <span className="text-text-muted font-normal">—</span>
                        )}
                      </td>
                      <td className="px-4 py-3">
                        {isUncertain ? (
                          <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-warning bg-warning-light px-2 py-0.5 rounded border border-warning/20">
                            <AlertTriangle className="w-3 h-3 shrink-0" /> UNCERTAIN
                          </span>
                        ) : hasAnswer ? (
                          <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-success bg-success-light px-2 py-0.5 rounded border border-success/20">
                            <CheckCircle2 className="w-3 h-3 shrink-0" /> CONFIRMED
                          </span>
                        ) : (
                          <span className="text-text-muted text-[11px]">NOT FOUND</span>
                        )}
                      </td>
                      <td className="px-4 py-3 text-text-muted">
                        Page {q.answer_source_page || q.source_pages[0] || "—"}
                      </td>
                      <td className="px-4 py-3 font-mono font-medium">
                        {(q.confidence * 100).toFixed(0)}%
                      </td>
                      <td className="px-5 py-3 text-right">
                        <Link
                          href={`/questions/${q.id}`}
                          className="text-primary hover:underline font-medium inline-flex items-center gap-1"
                        >
                          Edit Solution <ArrowRight className="w-3 h-3" />
                        </Link>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </div>
  );
}
