"use client";

import React, { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import {
  FileText,
  HelpCircle,
  AlertTriangle,
  Download,
  Eye,
  CheckSquare,
  Link2,
  RefreshCw,
  Clock,
  Layers,
  FileCheck,
} from "lucide-react";
import { api } from "@/lib/api";
import { DocumentDetail } from "@/lib/types";
import { Card, CardHeader } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { StatusBadge } from "@/components/ui/Badge";

export default function DocumentDetailPage() {
  const params = useParams();
  const router = useRouter();
  const docId = params.id as string;

  const [doc, setDoc] = useState<DocumentDetail | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchDoc = async () => {
    setLoading(true);
    try {
      const data = await api.documents.get(docId);
      setDoc(data);
    } catch (err: any) {
      if (err.status === 401) router.push("/login");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDoc();
  }, [docId]);

  if (loading || !doc) {
    return (
      <div className="flex items-center justify-center min-h-[40vh]">
        <RefreshCw className="w-5 h-5 text-primary animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 text-xs text-text-muted">
            <Link href="/documents" className="hover:text-text">
              Documents
            </Link>
            <span>/</span>
            <span className="text-text font-medium">{doc.original_filename}</span>
          </div>
          <div className="flex items-center gap-3 mt-1.5">
            <h1 className="text-xl font-bold text-text">{doc.original_filename}</h1>
            <StatusBadge status={doc.status} />
          </div>
        </div>

        {/* Action Toolbar */}
        <div className="flex flex-wrap items-center gap-2">
          <Link href={`/documents/${doc.id}/viewer`}>
            <Button variant="outline" size="sm">
              <Eye className="w-3.5 h-3.5 mr-1.5" />
              View Source
            </Button>
          </Link>
          <Link href={`/documents/${doc.id}/questions`}>
            <Button variant="outline" size="sm">
              <HelpCircle className="w-3.5 h-3.5 mr-1.5" />
              Questions ({doc.questions_count})
            </Button>
          </Link>
          {doc.review_required_count > 0 && (
            <Link href={`/documents/${doc.id}/review`}>
              <Button variant="danger" size="sm">
                <AlertTriangle className="w-3.5 h-3.5 mr-1.5" />
                Review Issues ({doc.review_required_count})
              </Button>
            </Link>
          )}
          <Link href={`/documents/${doc.id}/status`}>
            <Button variant="outline" size="sm">
              <Clock className="w-3.5 h-3.5 mr-1.5" />
              Status
            </Button>
          </Link>

          {/* Real Live Exports */}
          <a
            href={api.exports.getJsonUrl(doc.id)}
            target="_blank"
            rel="noopener noreferrer"
            download
          >
            <Button variant="secondary" size="sm">
              <Download className="w-3.5 h-3.5 mr-1.5" />
              JSON
            </Button>
          </a>
          <a
            href={api.exports.getCsvUrl(doc.id)}
            target="_blank"
            rel="noopener noreferrer"
            download
          >
            <Button variant="secondary" size="sm">
              <Download className="w-3.5 h-3.5 mr-1.5" />
              CSV
            </Button>
          </a>
        </div>
      </div>

      {/* Metadata Metrics Row */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <Card className="p-4">
          <div className="text-xs text-text-muted">Total Questions</div>
          <div className="text-2xl font-bold text-text mt-1">{doc.questions_count}</div>
          <div className="text-[11px] text-text-muted mt-1">Structured entities</div>
        </Card>

        <Card className="p-4">
          <div className="text-xs text-text-muted">Average Confidence</div>
          <div className="text-2xl font-bold text-text mt-1 font-mono">
            {doc.average_confidence != null
              ? `${(doc.average_confidence * 100).toFixed(0)}%`
              : "—"}
          </div>
          <div className="text-[11px] text-text-muted mt-1">Across all questions</div>
        </Card>

        <Card className="p-4">
          <div className="text-xs text-text-muted">Review Required</div>
          <div className="text-2xl font-bold text-text mt-1 text-warning">
            {doc.review_required_count}
          </div>
          <div className="text-[11px] text-text-muted mt-1">Uncertain / low confidence</div>
        </Card>

        <Card className="p-4">
          <div className="text-xs text-text-muted">Total Pages</div>
          <div className="text-2xl font-bold text-text mt-1">{doc.page_count}</div>
          <div className="text-[11px] text-text-muted mt-1">Rendered snapshots</div>
        </Card>
      </div>

      {/* Detailed Information */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card className="p-5">
          <CardHeader title="Document Specifications" />
          <dl className="space-y-2.5 text-xs">
            <div className="flex justify-between py-1 border-b border-border/50">
              <dt className="text-text-muted">File ID</dt>
              <dd className="font-mono text-text">{doc.id}</dd>
            </div>
            <div className="flex justify-between py-1 border-b border-border/50">
              <dt className="text-text-muted">Format</dt>
              <dd className="uppercase font-medium text-text">{doc.file_type}</dd>
            </div>
            <div className="flex justify-between py-1 border-b border-border/50">
              <dt className="text-text-muted">MIME Type</dt>
              <dd className="font-mono text-text">{doc.mime_type}</dd>
            </div>
            <div className="flex justify-between py-1 border-b border-border/50">
              <dt className="text-text-muted">File Size</dt>
              <dd className="text-text">
                {(doc.file_size_bytes / 1024).toFixed(1)} KB
              </dd>
            </div>
            <div className="flex justify-between py-1 border-b border-border/50">
              <dt className="text-text-muted">Uploaded At</dt>
              <dd className="text-text">{new Date(doc.created_at).toLocaleString()}</dd>
            </div>
          </dl>
        </Card>

        <Card className="p-5">
          <CardHeader
            title="Associated Documents & Answer Keys"
            subtitle="Linked answer keys or solution appendices"
          />
          {doc.related_document_ids.length === 0 ? (
            <div className="text-xs text-text-muted py-4 text-center border border-dashed border-border rounded-md">
              No related answer keys or appendices associated.
            </div>
          ) : (
            <div className="space-y-2">
              {doc.related_document_ids.map((relId) => (
                <div
                  key={relId}
                  className="flex items-center justify-between p-2.5 bg-slate-50 border border-border rounded text-xs"
                >
                  <div className="flex items-center gap-2">
                    <Link2 className="w-3.5 h-3.5 text-primary" />
                    <span className="font-mono text-text truncate max-w-[220px]">
                      {relId}
                    </span>
                  </div>
                  <Link
                    href={`/documents/${relId}`}
                    className="text-primary hover:underline font-medium"
                  >
                    View
                  </Link>
                </div>
              ))}
            </div>
          )}
        </Card>
      </div>
    </div>
  );
}
