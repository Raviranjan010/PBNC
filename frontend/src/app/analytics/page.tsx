"use client";

import React, { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import {
  BarChart3,
  CheckCircle2,
  AlertTriangle,
  FileText,
  HelpCircle,
  TrendingUp,
  RefreshCw,
  ShieldCheck,
} from "lucide-react";
import { api } from "@/lib/api";
import { AnalyticsData } from "@/lib/types";
import { Card, CardHeader } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { EmptyState } from "@/components/ui/EmptyState";

export default function AnalyticsPage() {
  const router = useRouter();
  const [data, setData] = useState<AnalyticsData | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchAnalytics = async () => {
    setLoading(true);
    try {
      const res = await api.analytics.get();
      setData(res);
    } catch (err: any) {
      if (err.status === 401) router.push("/login");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAnalytics();
  }, []);

  const hasData = data && data.total_documents > 0;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-text">Workspace Analytics</h1>
          <p className="text-xs text-text-muted mt-0.5">
            Real database metrics reflecting document intelligence extraction quality
          </p>
        </div>
        <Button variant="outline" size="sm" onClick={fetchAnalytics} disabled={loading}>
          <RefreshCw className={`w-3.5 h-3.5 mr-1.5 ${loading ? "animate-spin" : ""}`} />
          Refresh
        </Button>
      </div>

      {!hasData ? (
        <Card className="p-8">
          <EmptyState
            icon={<BarChart3 className="w-8 h-8 text-text-muted" />}
            title="Not Enough Data Yet"
            description="Analytics will populate automatically as documents and question banks are processed through the intelligence pipeline."
          />
        </Card>
      ) : (
        <div className="space-y-6">
          {/* Top Metrics Row */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            <Card className="p-4">
              <div className="text-xs text-text-muted flex items-center justify-between">
                <span>Documents Processed</span>
                <FileText className="w-4 h-4 text-primary" />
              </div>
              <div className="text-2xl font-bold text-text mt-2">
                {data.processed_documents} / {data.total_documents}
              </div>
              <div className="text-[11px] text-text-muted mt-1">
                {((data.processed_documents / data.total_documents) * 100).toFixed(0)}% completion rate
              </div>
            </Card>

            <Card className="p-4">
              <div className="text-xs text-text-muted flex items-center justify-between">
                <span>Average Confidence</span>
                <TrendingUp className="w-4 h-4 text-success" />
              </div>
              <div className="text-2xl font-bold text-text mt-2 font-mono">
                {(data.average_confidence * 100).toFixed(1)}%
              </div>
              <div className="text-[11px] text-text-muted mt-1">Across all questions</div>
            </Card>

            <Card className="p-4">
              <div className="text-xs text-text-muted flex items-center justify-between">
                <span>Verified Questions</span>
                <CheckCircle2 className="w-4 h-4 text-success" />
              </div>
              <div className="text-2xl font-bold text-text mt-2">
                {data.verified_questions}
              </div>
              <div className="text-[11px] text-text-muted mt-1">
                {data.total_questions > 0
                  ? `${((data.verified_questions / data.total_questions) * 100).toFixed(0)}% of total`
                  : "0%"}
              </div>
            </Card>

            <Card className="p-4">
              <div className="text-xs text-text-muted flex items-center justify-between">
                <span>Review Required</span>
                <AlertTriangle className="w-4 h-4 text-warning" />
              </div>
              <div className="text-2xl font-bold text-text mt-2 text-warning">
                {data.review_required_questions}
              </div>
              <div className="text-[11px] text-text-muted mt-1">Flagged for manual sign-off</div>
            </Card>
          </div>

          {/* Status Breakdown & Warnings */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <Card className="p-5">
              <CardHeader
                title="Question Quality Distribution"
                subtitle="Categorized by verification confidence thresholds"
              />
              <div className="space-y-3 mt-4">
                <div>
                  <div className="flex justify-between text-xs mb-1">
                    <span className="text-success font-medium">Verified (≥ 90% Confidence)</span>
                    <span className="font-bold text-text">{data.verified_questions}</span>
                  </div>
                  <div className="w-full bg-slate-100 rounded-full h-2">
                    <div
                      className="bg-success h-2 rounded-full transition-all"
                      style={{
                        width: `${
                          data.total_questions > 0
                            ? (data.verified_questions / data.total_questions) * 100
                            : 0
                        }%`,
                      }}
                    />
                  </div>
                </div>

                <div>
                  <div className="flex justify-between text-xs mb-1">
                    <span className="text-warning font-medium">Partial (70% - 89% Confidence)</span>
                    <span className="font-bold text-text">{data.partial_questions}</span>
                  </div>
                  <div className="w-full bg-slate-100 rounded-full h-2">
                    <div
                      className="bg-warning h-2 rounded-full transition-all"
                      style={{
                        width: `${
                          data.total_questions > 0
                            ? (data.partial_questions / data.total_questions) * 100
                            : 0
                        }%`,
                      }}
                    />
                  </div>
                </div>

                <div>
                  <div className="flex justify-between text-xs mb-1">
                    <span className="text-danger font-medium">Review Required (&lt; 70% or Uncertain)</span>
                    <span className="font-bold text-text">{data.review_required_questions}</span>
                  </div>
                  <div className="w-full bg-slate-100 rounded-full h-2">
                    <div
                      className="bg-danger h-2 rounded-full transition-all"
                      style={{
                        width: `${
                          data.total_questions > 0
                            ? (data.review_required_questions / data.total_questions) * 100
                            : 0
                        }%`,
                      }}
                    />
                  </div>
                </div>
              </div>
            </Card>

            <Card className="p-5">
              <CardHeader
                title="Pipeline Warnings by Stage"
                subtitle="Distribution of warnings encountered during extraction"
              />
              {Object.keys(data.warning_counts_by_stage).length === 0 ? (
                <div className="text-xs text-text-muted py-6 text-center border border-dashed border-border rounded-md mt-2">
                  No pipeline warnings recorded across any document.
                </div>
              ) : (
                <div className="space-y-3 mt-4">
                  {Object.entries(data.warning_counts_by_stage).map(([stage, count]) => (
                    <div
                      key={stage}
                      className="flex items-center justify-between p-2.5 bg-slate-50 border border-border rounded text-xs"
                    >
                      <span className="font-mono font-semibold text-text uppercase">
                        [{stage}]
                      </span>
                      <span className="font-bold text-text bg-white px-2 py-0.5 rounded border border-border">
                        {count} warnings
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </Card>
          </div>
        </div>
      )}
    </div>
  );
}
