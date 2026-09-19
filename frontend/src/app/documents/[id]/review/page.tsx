"use client";

import React, { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import {
  ArrowLeft,
  AlertTriangle,
  AlertCircle,
  CheckCircle2,
  HelpCircle,
  Eye,
  RefreshCw,
} from "lucide-react";
import { api } from "@/lib/api";
import { DocumentDetail, DocumentReviewItemsResponse } from "@/lib/types";
import { Card, CardHeader } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { StatusBadge } from "@/components/ui/Badge";
import { EmptyState } from "@/components/ui/EmptyState";

export default function DocumentReviewPage() {
  const params = useParams();
  const router = useRouter();
  const docId = params.id as string;

  const [doc, setDoc] = useState<DocumentDetail | null>(null);
  const [reviewData, setReviewData] = useState<DocumentReviewItemsResponse | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchReviews = async () => {
    setLoading(true);
    try {
      const [docRes, revRes] = await Promise.all([
        api.documents.get(docId),
        api.review.getForDoc(docId),
      ]);
      setDoc(docRes);
      setReviewData(revRes);
    } catch (err: any) {
      if (err.status === 401) router.push("/login");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchReviews();
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
            <span className="text-text font-medium">Review Issues</span>
          </div>
          <h1 className="text-xl font-bold text-text mt-1">Review & Warnings</h1>
        </div>
        <Button variant="outline" size="sm" onClick={fetchReviews} disabled={loading}>
          <RefreshCw className={`w-3.5 h-3.5 mr-1.5 ${loading ? "animate-spin" : ""}`} />
          Refresh
        </Button>
      </div>

      {/* Issues Section */}
      <div className="space-y-4">
        <h2 className="text-sm font-semibold text-text uppercase tracking-wider">
          Flagged Review Items ({reviewData?.review_items?.length || 0})
        </h2>

        {(!reviewData || reviewData.review_items.length === 0) ? (
          <EmptyState
            icon={<CheckCircle2 className="w-8 h-8 text-success" />}
            title="No Pending Review Items"
            description="All questions in this document meet verification thresholds."
          />
        ) : (
          <div className="space-y-3">
            {reviewData.review_items.map((item) => (
              <Card
                key={item.id}
                className="p-4 border-l-4 border-l-warning flex items-start justify-between gap-4"
              >
                <div>
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-xs font-bold text-text">
                      {item.issue_type.replace("_", " ")}
                    </span>
                    {item.is_resolved ? (
                      <span className="text-[10px] bg-success-light text-success px-2 py-0.5 rounded font-medium">
                        Resolved
                      </span>
                    ) : (
                      <span className="text-[10px] bg-warning-light text-warning px-2 py-0.5 rounded font-medium">
                        Action Required
                      </span>
                    )}
                  </div>
                  <p className="text-xs text-text-muted">{item.description}</p>
                </div>

                {item.question_id && (
                  <Link href={`/questions/${item.question_id}`}>
                    <Button size="sm" variant="outline">
                      <Eye className="w-3.5 h-3.5 mr-1" /> Inspect Question
                    </Button>
                  </Link>
                )}
              </Card>
            ))}
          </div>
        )}
      </div>

      {/* Extraction Warnings Section */}
      {reviewData?.warnings && reviewData.warnings.length > 0 && (
        <div className="space-y-4 mt-8">
          <h2 className="text-sm font-semibold text-text uppercase tracking-wider">
            Pipeline Extraction Warnings ({reviewData.warnings.length})
          </h2>
          <div className="space-y-2">
            {reviewData.warnings.map((w) => (
              <div
                key={w.id}
                className="p-3 bg-slate-50 border border-border rounded flex items-start gap-2.5 text-xs"
              >
                <AlertCircle className="w-4 h-4 text-warning shrink-0 mt-0.5" />
                <div>
                  <span className="font-semibold uppercase text-text font-mono text-[10px] mr-2">
                    [{w.stage}]
                  </span>
                  <span className="text-text">{w.message}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
