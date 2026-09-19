"use client";

import React from "react";
import { FileCode2, ExternalLink, Download, CheckCircle2, Shield } from "lucide-react";
import { Card, CardHeader } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";

export default function ApiDocsPage() {
  return (
    <div className="space-y-6 max-w-4xl">
      <div>
        <h1 className="text-xl font-bold text-text">REST API Documentation</h1>
        <p className="text-xs text-text-muted mt-0.5">
          Comprehensive API surface compliant with Pragati Bharti Round 2 technical specification
        </p>
      </div>

      {/* Quick Links */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Card className="p-5">
          <div className="flex items-center gap-3 mb-3">
            <div className="p-2.5 bg-primary-light text-primary rounded-lg">
              <ExternalLink className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-sm font-semibold text-text">Interactive Swagger UI</h3>
              <p className="text-xs text-text-muted">Test endpoints with live OpenAPI documentation</p>
            </div>
          </div>
          <a
            href="http://127.0.0.1:8000/docs"
            target="_blank"
            rel="noopener noreferrer"
          >
            <Button size="sm" variant="outline" className="w-full">
              Open /docs <ExternalLink className="w-3.5 h-3.5 ml-1.5" />
            </Button>
          </a>
        </Card>

        <Card className="p-5">
          <div className="flex items-center gap-3 mb-3">
            <div className="p-2.5 bg-success-light text-success rounded-lg">
              <Download className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-sm font-semibold text-text">Postman Collection</h3>
              <p className="text-xs text-text-muted">Pre-configured collection covering all workflows</p>
            </div>
          </div>
          <a
            href="/PaperMind.postman_collection.json"
            download="PaperMind.postman_collection.json"
          >
            <Button size="sm" variant="outline" className="w-full">
              Download Collection (v2.1) <Download className="w-3.5 h-3.5 ml-1.5" />
            </Button>
          </a>
        </Card>
      </div>

      {/* Endpoints Table */}
      <Card className="p-5">
        <CardHeader title="Specification Endpoint Matrix" subtitle="All 10 required REST services" />
        <div className="space-y-2 text-xs">
          {[
            { method: "POST", path: "/api/v1/auth/register", desc: "User registration & password hashing" },
            { method: "POST", path: "/api/v1/auth/login", desc: "OAuth2 & JWT authentication" },
            { method: "POST", path: "/api/v1/documents/upload", desc: "MIME-validated async upload" },
            { method: "GET", path: "/api/v1/documents", desc: "List user documents" },
            { method: "GET", path: "/api/v1/documents/{id}/status", desc: "Real stage-based status" },
            { method: "GET", path: "/api/v1/documents/{id}/questions", desc: "Questions list with search & filters" },
            { method: "GET", path: "/api/v1/questions/{id}", desc: "Individual question & options" },
            { method: "PATCH", path: "/api/v1/questions/{id}", desc: "Human review corrections & approval" },
            { method: "GET", path: "/api/v1/documents/{id}/answers", desc: "Detected answer keys" },
            { method: "GET", path: "/api/v1/documents/{id}/review-items", desc: "Review items & warnings" },
            { method: "POST", path: "/api/v1/documents/{id}/related", desc: "Answer key document association" },
            { method: "GET", path: "/api/v1/documents/{id}/export/json", desc: "Live JSON export" },
            { method: "GET", path: "/api/v1/documents/{id}/export/csv", desc: "Live CSV export" },
            { method: "GET", path: "/health", desc: "System health check" },
          ].map((ep, idx) => (
            <div
              key={idx}
              className="flex items-center justify-between p-2 rounded bg-slate-50 border border-border/60"
            >
              <div className="flex items-center gap-3">
                <span
                  className={`font-mono text-[10px] font-bold px-1.5 py-0.5 rounded ${
                    ep.method === "POST"
                      ? "bg-blue-100 text-blue-700"
                      : ep.method === "PATCH"
                      ? "bg-amber-100 text-amber-700"
                      : "bg-emerald-100 text-emerald-700"
                  }`}
                >
                  {ep.method}
                </span>
                <span className="font-mono text-text font-medium">{ep.path}</span>
              </div>
              <span className="text-text-muted text-[11px]">{ep.desc}</span>
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
}
