"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { HelpCircle, Search, ArrowRight, RefreshCw, FileText } from "lucide-react";
import { api } from "@/lib/api";
import { Question, Document } from "@/lib/types";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { StatusBadge } from "@/components/ui/Badge";
import { EmptyState } from "@/components/ui/EmptyState";

export default function GlobalQuestionsPage() {
  const router = useRouter();
  const [documents, setDocuments] = useState<Document[]>([]);
  const [questionsByDoc, setQuestionsByDoc] = useState<Record<string, Question[]>>({});
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");

  const loadAll = async () => {
    setLoading(true);
    try {
      const docs = await api.documents.list();
      setDocuments(docs);
      
      const qMap: Record<string, Question[]> = {};
      await Promise.all(
        docs.map(async (d) => {
          const res = await api.questions.listForDoc(d.id);
          qMap[d.id] = res.items;
        })
      );
      setQuestionsByDoc(qMap);
    } catch (err: any) {
      if (err.status === 401) router.push("/login");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAll();
  }, []);

  const allQuestions = Object.entries(questionsByDoc).flatMap(([docId, qs]) =>
    qs.map((q) => ({
      ...q,
      docName: documents.find((d) => d.id === docId)?.original_filename || docId,
    }))
  );

  const filtered = allQuestions.filter(
    (q) =>
      q.question_text.toLowerCase().includes(search.toLowerCase()) ||
      q.docName.toLowerCase().includes(search.toLowerCase()) ||
      q.question_number.includes(search)
  );

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-text">Structured Questions Bank</h1>
          <p className="text-xs text-text-muted mt-0.5">
            Global search across all extracted questions, options, and source documents
          </p>
        </div>
        <Button variant="outline" size="sm" onClick={loadAll} disabled={loading}>
          <RefreshCw className={`w-3.5 h-3.5 mr-1.5 ${loading ? "animate-spin" : ""}`} />
          Refresh
        </Button>
      </div>

      <div className="relative max-w-sm">
        <Search className="w-3.5 h-3.5 text-text-muted absolute left-3 top-2.5" />
        <input
          type="text"
          placeholder="Search question text or document name..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="w-full pl-8 pr-3 py-1.5 text-xs rounded-md border border-border bg-surface text-text focus:outline-none focus:ring-2 focus:ring-primary/30"
        />
      </div>

      {filtered.length === 0 ? (
        <EmptyState
          title="No questions found"
          description={
            search
              ? "No questions match your query."
              : "No questions have been extracted from your uploaded documents yet."
          }
        />
      ) : (
        <div className="space-y-3">
          {filtered.map((q) => (
            <Card key={q.id} className="p-4 hover:border-slate-300 transition-colors">
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <span className="font-mono text-xs font-bold text-primary bg-primary-light px-2 py-0.5 rounded">
                    Q{q.question_number}
                  </span>
                  <StatusBadge status={q.status} />
                  <span className="text-[11px] text-text-muted flex items-center gap-1">
                    <FileText className="w-3 h-3" /> {q.docName}
                  </span>
                </div>
                <Link
                  href={`/questions/${q.id}`}
                  className="text-xs font-medium text-primary hover:underline flex items-center gap-1"
                >
                  Edit & Review <ArrowRight className="w-3 h-3" />
                </Link>
              </div>

              <p className="text-xs font-medium text-text line-clamp-2 mb-2">
                {q.question_text}
              </p>

              <div className="flex items-center gap-4 text-[11px] text-text-muted">
                <span>Options: {q.options.length}</span>
                <span>Answer: <strong className="font-mono text-text">{q.answer || "—"}</strong></span>
                <span>Pages: [{q.source_pages.join(", ")}]</span>
                <span>Confidence: {(q.confidence * 100).toFixed(0)}%</span>
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
