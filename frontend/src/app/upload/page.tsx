"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { UploadCloud, FileText, AlertCircle, ArrowLeft } from "lucide-react";
import { api } from "@/lib/api";
import { Card, CardHeader } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";

export default function DedicatedUploadPage() {
  const router = useRouter();
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isDragOver, setIsDragOver] = useState(false);

  const handleUpload = async (file: File) => {
    setError(null);
    setUploading(true);
    try {
      const res = await api.documents.upload(file);
      router.push(`/documents/${res.document_id}/status`);
    } catch (err: any) {
      setError(err.message || "Failed to upload document. Please check format and size.");
      setUploading(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <div className="flex items-center gap-3">
        <button
          onClick={() => router.back()}
          className="p-1.5 rounded hover:bg-slate-100 text-text-muted hover:text-text"
        >
          <ArrowLeft className="w-4 h-4" />
        </button>
        <div>
          <h1 className="text-xl font-bold text-text">Upload Document</h1>
          <p className="text-xs text-text-muted mt-0.5">
            Ingest exam papers, question sheets, and answer keys
          </p>
        </div>
      </div>

      <Card className="p-8">
        {error && (
          <div className="mb-4 p-3 bg-danger-light border border-danger/20 rounded-md flex items-center gap-2 text-xs text-danger">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        <div
          onDragOver={(e) => {
            e.preventDefault();
            setIsDragOver(true);
          }}
          onDragLeave={() => setIsDragOver(false)}
          onDrop={(e) => {
            e.preventDefault();
            setIsDragOver(false);
            if (e.dataTransfer.files && e.dataTransfer.files[0]) {
              handleUpload(e.dataTransfer.files[0]);
            }
          }}
          className={`border-2 border-dashed rounded-lg p-10 text-center transition-colors ${
            isDragOver
              ? "border-primary bg-primary-light/30"
              : "border-border bg-slate-50/50 hover:bg-slate-50"
          }`}
        >
          <div className="w-14 h-14 bg-white rounded-full border border-border shadow-subtle flex items-center justify-center mx-auto text-primary mb-3">
            <UploadCloud className="w-7 h-7" />
          </div>
          <h3 className="text-sm font-semibold text-text">
            {uploading ? "Uploading & Validating Document..." : "Select or drag & drop document"}
          </h3>
          <p className="text-xs text-text-muted mt-1 mb-5">
            PDF, scanned PDF, JPG, JPEG, and PNG supported (up to 25MB)
          </p>

          <label>
            <input
              type="file"
              accept=".pdf,.png,.jpg,.jpeg"
              disabled={uploading}
              className="hidden"
              onChange={(e) => {
                if (e.target.files && e.target.files[0]) {
                  handleUpload(e.target.files[0]);
                }
              }}
            />
            <Button
              type="button"
              variant="primary"
              size="md"
              isLoading={uploading}
              className="pointer-events-none"
            >
              Browse Files
            </Button>
          </label>
        </div>
      </Card>
    </div>
  );
}
