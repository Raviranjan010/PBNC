"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  FileText,
  Plus,
  Search,
  ArrowRight,
  RefreshCw,
  UploadCloud,
  RotateCcw,
  Trash2,
  ChevronLeft,
  ChevronRight,
} from "lucide-react";
import { api } from "@/lib/api";
import { Document } from "@/lib/types";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { StatusBadge } from "@/components/ui/Badge";
import { EmptyState } from "@/components/ui/EmptyState";

export default function DocumentsPage() {
  const router = useRouter();
  const [documents, setDocuments] = useState<Document[]>([]);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const limit = 10;

  const fetchDocs = async (targetPage: number = page) => {
    setLoading(true);
    try {
      const data = await api.documents.list({ page: targetPage, limit });
      setDocuments(data.items);
      setTotal(data.total);
      setPage(data.page);
    } catch (err: any) {
      if (err.status === 401) router.push("/login");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDocs(page);
  }, [page]);

  const handleDelete = async (docId: string, filename: string) => {
    if (!confirm(`Are you sure you want to delete "${filename}"? This action cannot be undone.`)) {
      return;
    }
    setActionLoading(docId);
    try {
      await api.documents.delete(docId);
      await fetchDocs(page);
    } catch (err: any) {
      alert(`Failed to delete document: ${err.message || "Unknown error"}`);
    } finally {
      setActionLoading(null);
    }
  };

  const handleRetry = async (docId: string) => {
    setActionLoading(docId);
    try {
      await api.documents.retry(docId);
      router.push(`/documents/${docId}/status`);
    } catch (err: any) {
      alert(`Retry failed: ${err.message || "Unknown error"}`);
      setActionLoading(null);
    }
  };

  const filtered = documents.filter((d) =>
    d.original_filename.toLowerCase().includes(search.toLowerCase())
  );

  const totalPages = Math.ceil(total / limit) || 1;

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-text">Documents Repository</h1>
          <p className="text-xs text-text-muted mt-0.5">
            Manage your ingested question papers and answer key documents
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={() => fetchDocs(page)} disabled={loading}>
            <RefreshCw className={`w-3.5 h-3.5 mr-1.5 ${loading ? "animate-spin" : ""}`} />
            Refresh
          </Button>
          <Link href="/dashboard">
            <Button size="sm">
              <UploadCloud className="w-3.5 h-3.5 mr-1.5" />
              Upload Document
            </Button>
          </Link>
        </div>
      </div>

      {/* Filter and Search */}
      <div className="flex items-center gap-3">
        <div className="relative flex-1 max-w-sm">
          <Search className="w-3.5 h-3.5 text-text-muted absolute left-3 top-2.5" />
          <input
            type="text"
            placeholder="Search by filename..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-8 pr-3 py-1.5 text-xs rounded-md border border-border bg-surface text-text focus:outline-none focus:ring-2 focus:ring-primary/30"
          />
        </div>
      </div>

      {/* Documents Table */}
      <Card className="p-0 overflow-hidden">
        {filtered.length === 0 ? (
          <div className="p-8">
            <EmptyState
              title={search ? "No matching documents" : "No documents in workspace"}
              description={
                search
                  ? "Try searching for a different filename or keyword."
                  : "Upload your first exam or question bank document to get started."
              }
              action={
                !search ? (
                  <Link href="/dashboard">
                    <Button size="sm">Upload Document</Button>
                  </Link>
                ) : undefined
              }
            />
          </div>
        ) : (
          <div>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-50 text-text-muted uppercase border-b border-border font-medium">
                  <tr>
                    <th className="px-5 py-3">Filename</th>
                    <th className="px-4 py-3">Type</th>
                    <th className="px-4 py-3">Pages</th>
                    <th className="px-4 py-3">Uploaded</th>
                    <th className="px-4 py-3">Status</th>
                    <th className="px-4 py-3">Avg Confidence</th>
                    <th className="px-5 py-3 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {filtered.map((doc) => {
                    const isRetryable = ["FAILED", "REVIEW_REQUIRED", "PARTIAL"].includes(doc.status);
                    const isBusy = actionLoading === doc.id;

                    return (
                      <tr key={doc.id} className="hover:bg-slate-50/50 transition-colors">
                        <td className="px-5 py-3 font-medium text-text flex items-center gap-2">
                          <FileText className="w-4 h-4 text-text-muted shrink-0" />
                          <span className="truncate max-w-[220px]">{doc.original_filename}</span>
                        </td>
                        <td className="px-4 py-3 uppercase text-[11px] text-text-muted">
                          {doc.file_type}
                        </td>
                        <td className="px-4 py-3 text-text-muted">
                          {doc.page_count > 0 ? doc.page_count : "—"}
                        </td>
                        <td className="px-4 py-3 text-text-muted">
                          {new Date(doc.created_at).toLocaleDateString()}
                        </td>
                        <td className="px-4 py-3">
                          <StatusBadge status={doc.status} />
                        </td>
                        <td className="px-4 py-3 font-mono font-medium">
                          {doc.average_confidence != null
                            ? `${(doc.average_confidence * 100).toFixed(0)}%`
                            : "—"}
                        </td>
                        <td className="px-5 py-3 text-right">
                          <div className="inline-flex items-center gap-2">
                            {isRetryable && (
                              <button
                                onClick={() => handleRetry(doc.id)}
                                disabled={isBusy}
                                title="Retry Extraction"
                                className="text-amber-600 hover:text-amber-700 p-1 rounded hover:bg-amber-50"
                              >
                                <RotateCcw className={`w-3.5 h-3.5 ${isBusy ? "animate-spin" : ""}`} />
                              </button>
                            )}
                            <button
                              onClick={() => handleDelete(doc.id, doc.original_filename)}
                              disabled={isBusy}
                              title="Delete Document"
                              className="text-danger hover:text-danger/80 p-1 rounded hover:bg-red-50"
                            >
                              <Trash2 className="w-3.5 h-3.5" />
                            </button>
                            <Link
                              href={`/documents/${doc.id}`}
                              className="text-primary hover:text-primary-dark font-medium inline-flex items-center gap-1 ml-1"
                            >
                              Details <ArrowRight className="w-3 h-3" />
                            </Link>
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>

            {/* Pagination controls */}
            <div className="px-5 py-3 border-t border-border flex items-center justify-between text-xs text-text-muted">
              <div>
                Showing {(page - 1) * limit + 1} to {Math.min(page * limit, total)} of {total} documents
              </div>
              <div className="flex items-center gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  disabled={page <= 1 || loading}
                >
                  <ChevronLeft className="w-3.5 h-3.5 mr-1" /> Previous
                </Button>
                <span className="font-medium text-text px-2">
                  Page {page} of {totalPages}
                </span>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                  disabled={page >= totalPages || loading}
                >
                  Next <ChevronRight className="w-3.5 h-3.5 ml-1" />
                </Button>
              </div>
            </div>
          </div>
        )}
      </Card>
    </div>
  );
}
