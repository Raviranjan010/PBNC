"use client";

import React, { useEffect, useState } from "react";
import { useParams, useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import {
  ChevronLeft,
  ChevronRight,
  ZoomIn,
  ZoomOut,
  Maximize2,
  FileText,
  HelpCircle,
  ArrowLeft,
  RefreshCw,
} from "lucide-react";
import { api } from "@/lib/api";
import { DocumentDetail, Question } from "@/lib/types";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { StatusBadge } from "@/components/ui/Badge";

export default function DocumentViewerPage() {
  const params = useParams();
  const searchParams = useSearchParams();
  const router = useRouter();
  const docId = params.id as string;
  const initialPage = parseInt(searchParams.get("page") || "1", 10);

  const [doc, setDoc] = useState<DocumentDetail | null>(null);
  const [questions, setQuestions] = useState<Question[]>([]);
  const [currentPage, setCurrentPage] = useState<number>(initialPage);
  const [zoom, setZoom] = useState<number>(100);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        const [docData, qData] = await Promise.all([
          api.documents.get(docId),
          api.questions.listForDoc(docId),
        ]);
        setDoc(docData);
        setQuestions(qData.items);
      } catch (err: any) {
        if (err.status === 401) router.push("/login");
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [docId, router]);

  const totalPages = doc?.page_count || 1;

  // Questions present on this page
  const pageQuestions = questions.filter((q) => q.source_pages.includes(currentPage));

  return (
    <div className="space-y-4">
      {/* Top Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-surface p-3 rounded-lg border border-border">
        <div className="flex items-center gap-3">
          <Link href={`/documents/${docId}`}>
            <Button variant="outline" size="sm">
              <ArrowLeft className="w-3.5 h-3.5 mr-1" /> Back
            </Button>
          </Link>
          <div>
            <h2 className="text-xs font-semibold text-text truncate max-w-xs">
              {doc?.original_filename || "Document Viewer"}
            </h2>
            <div className="text-[11px] text-text-muted">
              Page {currentPage} of {totalPages}
            </div>
          </div>
        </div>

        {/* Page & Zoom Controls */}
        <div className="flex items-center gap-2">
          <div className="flex items-center border border-border rounded-md bg-white">
            <button
              onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
              disabled={currentPage <= 1}
              className="p-1.5 text-text-muted hover:text-text disabled:opacity-30"
              title="Previous Page"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
            <span className="px-3 text-xs font-medium text-text border-x border-border">
              {currentPage} / {totalPages}
            </span>
            <button
              onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
              disabled={currentPage >= totalPages}
              className="p-1.5 text-text-muted hover:text-text disabled:opacity-30"
              title="Next Page"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>

          <div className="flex items-center border border-border rounded-md bg-white">
            <button
              onClick={() => setZoom((z) => Math.max(50, z - 25))}
              className="p-1.5 text-text-muted hover:text-text"
              title="Zoom out"
            >
              <ZoomOut className="w-4 h-4" />
            </button>
            <span className="px-2 text-xs font-mono text-text border-x border-border">
              {zoom}%
            </span>
            <button
              onClick={() => setZoom((z) => Math.min(200, z + 25))}
              className="p-1.5 text-text-muted hover:text-text"
              title="Zoom in"
            >
              <ZoomIn className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>

      {/* Main Split Viewer */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Document Canvas Column (3 cols) */}
        <div className="lg:col-span-3 bg-slate-200/60 rounded-lg border border-border p-4 min-h-[700px] flex items-center justify-center overflow-auto">
          {loading ? (
            <div className="flex items-center gap-2 text-xs text-text-muted">
              <RefreshCw className="w-4 h-4 animate-spin text-primary" />
              Loading rendered page snapshot...
            </div>
          ) : (
            <div
              className="transition-all duration-150 shadow-elevation bg-white rounded overflow-hidden"
              style={{ width: `${zoom}%` }}
            >
              {/* Actual Rendered Page Image (Zero Mock) */}
              <img
                src={api.documents.getPageImageUrl(docId, currentPage)}
                alt={`Page ${currentPage}`}
                className="w-full h-auto object-contain block select-none"
                loading="lazy"
              />
            </div>
          )}
        </div>

        {/* Source Page Questions Linkage Sidebar (1 col) */}
        <div className="space-y-4">
          <Card className="p-4">
            <h3 className="text-xs font-semibold text-text uppercase tracking-wider mb-3 flex items-center gap-1.5">
              <HelpCircle className="w-3.5 h-3.5 text-primary" />
              Questions on Page {currentPage} ({pageQuestions.length})
            </h3>

            {pageQuestions.length === 0 ? (
              <div className="text-xs text-text-muted py-4 text-center border border-dashed border-border rounded">
                No questions identified on this specific page.
              </div>
            ) : (
              <div className="space-y-3 max-h-[600px] overflow-y-auto pr-1">
                {pageQuestions.map((q) => (
                  <div
                    key={q.id}
                    className="p-3 bg-slate-50 border border-border rounded-md hover:border-primary/50 transition-colors"
                  >
                    <div className="flex items-center justify-between mb-1.5">
                      <span className="text-xs font-bold text-primary">
                        Q{q.question_number}
                      </span>
                      <StatusBadge status={q.status} />
                    </div>
                    <p className="text-xs text-text line-clamp-3 mb-2 font-medium">
                      {q.question_text}
                    </p>
                    <div className="flex items-center justify-between text-[11px] text-text-muted pt-1.5 border-t border-border/50">
                      <span>Pages: [{q.source_pages.join(", ")}]</span>
                      <Link
                        href={`/questions/${q.id}`}
                        className="text-primary hover:underline font-medium"
                      >
                        Inspect & Edit →
                      </Link>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </Card>
        </div>
      </div>
    </div>
  );
}
