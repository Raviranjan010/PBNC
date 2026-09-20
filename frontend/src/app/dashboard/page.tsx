"use client";

import React, { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import {
  FileText,
  UploadCloud,
  CheckCircle2,
  AlertTriangle,
  HelpCircle,
  Clock,
  ArrowRight,
  RefreshCw,
  AlertCircle,
} from "lucide-react";
import { api } from "@/lib/api";
import { isAuthenticated } from "@/lib/auth";
import { Document, AnalyticsData } from "@/lib/types";
import { Card, CardHeader } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { StatusBadge } from "@/components/ui/Badge";
import { EmptyState } from "@/components/ui/EmptyState";

export default function DashboardPage() {
  const router = useRouter();
  const [documents, setDocuments] = useState<Document[]>([]);
  const [analytics, setAnalytics] = useState<AnalyticsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [isDragOver, setIsDragOver] = useState(false);

  const loadDashboardData = useCallback(async () => {
    if (!isAuthenticated()) {
      router.replace("/login");
      return;
    }
    setLoading(true);
    try {
      const [docs, stats] = await Promise.all([
        api.documents.list(),
        api.analytics.get(),
      ]);
      setDocuments(docs.items);
      setAnalytics(stats);
    } catch (err: any) {
      if (err.status === 401) {
        router.replace("/login");
      }
    } finally {
      setLoading(false);
    }
  }, [router]);

  useEffect(() => {
    loadDashboardData();
  }, [loadDashboardData]);

  const handleFileUpload = async (file: File) => {
    setUploadError(null);
    setUploading(true);

    try {
      const res = await api.documents.upload(file);
      // Navigate to status tracker of this real upload
      router.push(`/documents/${res.document_id}/status`);
    } catch (err: any) {
      setUploadError(err.message || "Upload failed. Please check file format and size.");
      setUploading(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileUpload(e.dataTransfer.files[0]);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-text">Workspace Overview</h1>
          <p className="text-xs text-text-muted mt-0.5">
            Real-time document processing and structured question extraction
          </p>
        </div>
        <Button
          variant="outline"
          size="sm"
          onClick={loadDashboardData}
          disabled={loading}
        >
          <RefreshCw className={`w-3.5 h-3.5 mr-1.5 ${loading ? "animate-spin" : ""}`} />
          Refresh
        </Button>
      </div>

      {/* Metrics Row (Strict Zero Fake Data) */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card className="p-4">
          <div className="flex items-center justify-between text-text-muted text-xs">
            <span>Total Documents</span>
            <FileText className="w-4 h-4 text-primary" />
          </div>
          <div className="text-2xl font-bold text-text mt-2">
            {analytics ? analytics.total_documents : 0}
          </div>
          <div className="text-[11px] text-text-muted mt-1">Uploaded & stored</div>
        </Card>

        <Card className="p-4">
          <div className="flex items-center justify-between text-text-muted text-xs">
            <span>Processed</span>
            <CheckCircle2 className="w-4 h-4 text-success" />
          </div>
          <div className="text-2xl font-bold text-text mt-2">
            {analytics ? analytics.processed_documents : 0}
          </div>
          <div className="text-[11px] text-text-muted mt-1">Extraction completed</div>
        </Card>

        <Card className="p-4">
          <div className="flex items-center justify-between text-text-muted text-xs">
            <span>Total Questions</span>
            <HelpCircle className="w-4 h-4 text-primary" />
          </div>
          <div className="text-2xl font-bold text-text mt-2">
            {analytics ? analytics.total_questions : 0}
          </div>
          <div className="text-[11px] text-text-muted mt-1">Structured questions</div>
        </Card>

        <Card className="p-4">
          <div className="flex items-center justify-between text-text-muted text-xs">
            <span>Review Required</span>
            <AlertTriangle className="w-4 h-4 text-warning" />
          </div>
          <div className="text-2xl font-bold text-text mt-2">
            {analytics ? analytics.review_required_questions : 0}
          </div>
          <div className="text-[11px] text-text-muted mt-1">Pending verification</div>
        </Card>
      </div>

      {/* Drag & Drop Upload Panel */}
      <Card className="p-6">
        <CardHeader
          title="Upload Exam or Question Bank Document"
          subtitle="Supports PDF, scanned PDFs, PNG, and JPEG documents up to 25MB"
        />

        {uploadError && (
          <div className="mb-4 p-3 bg-danger-light border border-danger/20 rounded-md flex items-center gap-2 text-xs text-danger">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{uploadError}</span>
          </div>
        )}

        <div
          onDragOver={(e) => {
            e.preventDefault();
            setIsDragOver(true);
          }}
          onDragLeave={() => setIsDragOver(false)}
          onDrop={handleDrop}
          className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
            isDragOver
              ? "border-primary bg-primary-light/30"
              : "border-border bg-slate-50/50 hover:bg-slate-50"
          }`}
        >
          <div className="w-12 h-12 bg-white rounded-full border border-border shadow-subtle flex items-center justify-center mx-auto text-primary mb-3">
            <UploadCloud className="w-6 h-6" />
          </div>
          <h4 className="text-sm font-semibold text-text">
            {uploading ? "Uploading & Validating Document..." : "Drag and drop your document here"}
          </h4>
          <p className="text-xs text-text-muted mt-1 mb-4">
            or browse files from your computer
          </p>

          <label>
            <input
              type="file"
              accept=".pdf,.png,.jpg,.jpeg"
              className="hidden"
              disabled={uploading}
              onChange={(e) => {
                if (e.target.files && e.target.files[0]) {
                  handleFileUpload(e.target.files[0]);
                }
              }}
            />
            <Button
              type="button"
              variant="outline"
              size="sm"
              isLoading={uploading}
              className="pointer-events-none"
            >
              Choose File
            </Button>
          </label>
        </div>
      </Card>

      {/* Recent Documents Table */}
      <Card className="p-0 overflow-hidden">
        <div className="p-5 border-b border-border flex items-center justify-between">
          <div>
            <h3 className="text-sm font-semibold text-text">Recent Documents</h3>
            <p className="text-xs text-text-muted">Live document extraction records</p>
          </div>
          <Link
            href="/documents"
            className="text-xs font-medium text-primary hover:text-primary-dark flex items-center gap-1"
          >
            View all <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>

        {documents.length === 0 ? (
          <div className="p-6">
            <EmptyState
              title="No documents uploaded yet"
              description="Upload your first question paper or exam PDF to see real-time extraction results and questions."
            />
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50 text-text-muted uppercase border-b border-border font-medium">
                <tr>
                  <th className="px-5 py-3">Document Name</th>
                  <th className="px-4 py-3">Type</th>
                  <th className="px-4 py-3">Pages</th>
                  <th className="px-4 py-3">Status</th>
                  <th className="px-4 py-3">Confidence</th>
                  <th className="px-5 py-3 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {documents.slice(0, 5).map((doc) => (
                  <tr key={doc.id} className="hover:bg-slate-50/50 transition-colors">
                    <td className="px-5 py-3 font-medium text-text flex items-center gap-2">
                      <FileText className="w-4 h-4 text-text-muted shrink-0" />
                      <span className="truncate max-w-[200px]">{doc.original_filename}</span>
                    </td>
                    <td className="px-4 py-3 uppercase text-[11px] text-text-muted">
                      {doc.file_type}
                    </td>
                    <td className="px-4 py-3 text-text-muted">
                      {doc.page_count > 0 ? doc.page_count : "—"}
                    </td>
                    <td className="px-4 py-3">
                      <StatusBadge status={doc.status} />
                    </td>
                    <td className="px-4 py-3">
                      {doc.average_confidence != null ? (
                        <span className="font-mono font-medium">
                          {(doc.average_confidence * 100).toFixed(0)}%
                        </span>
                      ) : (
                        <span className="text-text-muted">—</span>
                      )}
                    </td>
                    <td className="px-5 py-3 text-right">
                      <Link
                        href={`/documents/${doc.id}`}
                        className="text-primary hover:text-primary-dark font-medium inline-flex items-center gap-1"
                      >
                        Inspect <ArrowRight className="w-3 h-3" />
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </div>
  );
}
