"use client";

import React, { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import {
  ArrowLeft,
  CheckCircle2,
  AlertTriangle,
  Save,
  FileText,
  Plus,
  Trash2,
  RefreshCw,
  Eye,
  Layers,
} from "lucide-react";
import { api } from "@/lib/api";
import { Question, DocumentDetail, Option } from "@/lib/types";
import { Card, CardHeader } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { StatusBadge } from "@/components/ui/Badge";

export default function QuestionDetailPage() {
  const params = useParams();
  const router = useRouter();
  const questionId = params.id as string;

  const [question, setQuestion] = useState<Question | null>(null);
  const [doc, setDoc] = useState<DocumentDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);

  // Editable Form State
  const [questionText, setQuestionText] = useState("");
  const [questionType, setQuestionType] = useState("MCQ");
  const [options, setOptions] = useState<{ option_key: string; option_text: string }[]>([]);
  const [answer, setAnswer] = useState("");
  const [selectedSourcePage, setSelectedSourcePage] = useState<number>(1);

  const fetchQuestionData = async () => {
    setLoading(true);
    try {
      const q = await api.questions.get(questionId);
      setQuestion(q);
      setQuestionText(q.question_text);
      setQuestionType(q.question_type);
      setOptions(q.options.map((o) => ({ option_key: o.option_key, option_text: o.option_text })));
      setAnswer(q.answer || "");
      if (q.source_pages && q.source_pages.length > 0) {
        setSelectedSourcePage(q.source_pages[0]);
      }

      // Fetch parent document
      const d = await api.documents.get(q.document_id);
      setDoc(d);
    } catch (err: any) {
      if (err.status === 401) router.push("/login");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchQuestionData();
  }, [questionId]);

  const handleAddOption = () => {
    const keys = ["A", "B", "C", "D", "E", "F"];
    const nextKey = keys[options.length] || `Option_${options.length + 1}`;
    setOptions([...options, { option_key: nextKey, option_text: "" }]);
  };

  const handleRemoveOption = (index: number) => {
    const newOpts = [...options];
    newOpts.splice(index, 1);
    setOptions(newOpts);
  };

  const handleOptionTextChange = (index: number, text: string) => {
    const newOpts = [...options];
    newOpts[index].option_text = text;
    setOptions(newOpts);
  };

  // Human Review: Save & Approve
  const handleSaveAndApprove = async (approve: boolean) => {
    setSaving(true);
    setSaveSuccess(false);

    try {
      const updated = await api.questions.patch(questionId, {
        question_text: questionText,
        question_type: questionType,
        options: options,
        answer: answer || null,
        status: approve ? "VERIFIED" : undefined,
        review_required: approve ? false : undefined,
        is_reviewed: approve ? true : undefined,
      });

      setQuestion(updated);
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 3000);
    } catch (err: any) {
      alert(err.message || "Failed to save corrections.");
    } finally {
      setSaving(false);
    }
  };

  if (loading || !question || !doc) {
    return (
      <div className="flex items-center justify-center min-h-[50vh]">
        <RefreshCw className="w-5 h-5 text-primary animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-surface p-4 rounded-lg border border-border">
        <div className="flex items-center gap-3">
          <button
            onClick={() => router.back()}
            className="p-1.5 rounded hover:bg-slate-100 text-text-muted hover:text-text"
            title="Go back"
          >
            <ArrowLeft className="w-4 h-4" />
          </button>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-mono text-xs font-bold text-primary bg-primary-light px-2 py-0.5 rounded">
                Question {question.question_number}
              </span>
              <StatusBadge status={question.status} />
              {question.review_required && (
                <span className="text-[11px] font-medium text-warning flex items-center gap-1">
                  <AlertTriangle className="w-3 h-3" /> Review Required
                </span>
              )}
            </div>
            <div className="text-[11px] text-text-muted mt-0.5">
              Source: {doc.original_filename} (Pages: [{question.source_pages.join(", ")}])
            </div>
          </div>
        </div>

        {/* Action Controls */}
        <div className="flex items-center gap-2">
          {saveSuccess && (
            <span className="text-xs font-semibold text-success flex items-center gap-1 animate-pulse">
              <CheckCircle2 className="w-4 h-4" /> Changes Saved!
            </span>
          )}
          <Button
            variant="outline"
            size="sm"
            onClick={() => handleSaveAndApprove(false)}
            isLoading={saving}
          >
            <Save className="w-3.5 h-3.5 mr-1" />
            Save Changes
          </Button>
          <Button
            variant="primary"
            size="sm"
            onClick={() => handleSaveAndApprove(true)}
            isLoading={saving}
          >
            <CheckCircle2 className="w-3.5 h-3.5 mr-1" />
            Approve & Verify
          </Button>
        </div>
      </div>

      {/* Split View (50% Source Page, 50% Question Editor) */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 items-start">
        {/* LEFT COLUMN: Real Source Page Snapshot */}
        <Card className="p-4 space-y-3">
          <div className="flex items-center justify-between border-b border-border pb-2">
            <div className="flex items-center gap-2">
              <Eye className="w-4 h-4 text-primary" />
              <h3 className="text-xs font-semibold text-text uppercase tracking-wider">
                Source Document Page
              </h3>
            </div>

            {/* If question spans multiple pages, provide switcher */}
            {question.source_pages.length > 1 && (
              <div className="flex items-center gap-1 text-xs">
                <span className="text-text-muted">Pages:</span>
                {question.source_pages.map((p) => (
                  <button
                    key={p}
                    onClick={() => setSelectedSourcePage(p)}
                    className={`px-2 py-0.5 rounded font-mono text-xs ${
                      selectedSourcePage === p
                        ? "bg-primary text-white font-bold"
                        : "bg-slate-100 text-text-muted hover:text-text"
                    }`}
                  >
                    P{p}
                  </button>
                ))}
              </div>
            )}
          </div>

          <div className="bg-slate-200/60 rounded border border-border p-2 max-h-[750px] overflow-y-auto flex justify-center">
            <img
              src={api.documents.getPageImageUrl(doc.id, selectedSourcePage)}
              alt={`Source Page ${selectedSourcePage}`}
              className="max-w-full h-auto object-contain rounded shadow-card block"
            />
          </div>

          <div className="text-[11px] text-text-muted text-center">
            Viewing actual rendered scan of page {selectedSourcePage}.
          </div>
        </Card>

        {/* RIGHT COLUMN: Question Editor & Human Review Controls */}
        <Card className="p-5 space-y-4">
          <CardHeader
            title="Question Transcription & Metadata"
            subtitle="Edit question prompt, options, and solutions directly"
          />

          {/* Prompt Editor */}
          <div>
            <label className="block text-xs font-semibold text-text mb-1.5">
              Question Text / Prompt
            </label>
            <textarea
              rows={4}
              value={questionText}
              onChange={(e) => setQuestionText(e.target.value)}
              className="w-full p-3 text-xs rounded-md border border-border bg-surface text-text focus:outline-none focus:ring-2 focus:ring-primary/30 leading-relaxed font-sans"
            />
          </div>

          {/* Type and Confidence Breakdown */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-text mb-1">
                Question Type
              </label>
              <select
                value={questionType}
                onChange={(e) => setQuestionType(e.target.value)}
                className="w-full px-2.5 py-1.5 text-xs rounded-md border border-border bg-surface text-text focus:outline-none focus:ring-2 focus:ring-primary/30"
              >
                <option value="MCQ">Multiple Choice (MCQ)</option>
                <option value="SHORT">Short Answer / Subjective</option>
                <option value="TRUE_FALSE">True / False</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-text mb-1">
                Extraction Confidence
              </label>
              <div className="px-3 py-1.5 bg-slate-50 border border-border rounded-md text-xs font-mono font-medium text-text flex items-center justify-between">
                <span>{(question.confidence * 100).toFixed(1)}%</span>
                <span className="text-[11px] text-text-muted">
                  {question.confidence >= 0.9 ? "High" : question.confidence >= 0.7 ? "Moderate" : "Low"}
                </span>
              </div>
            </div>
          </div>

          {/* Options Editor */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <label className="text-xs font-semibold text-text">
                Answer Options ({options.length})
              </label>
              <button
                type="button"
                onClick={handleAddOption}
                className="text-xs text-primary hover:underline font-medium flex items-center gap-1"
              >
                <Plus className="w-3.5 h-3.5" /> Add Option
              </button>
            </div>

            <div className="space-y-2">
              {options.map((opt, idx) => (
                <div key={idx} className="flex items-center gap-2">
                  <span className="w-7 h-7 bg-slate-100 border border-border rounded text-xs font-mono font-bold flex items-center justify-center shrink-0">
                    {opt.option_key}
                  </span>
                  <input
                    type="text"
                    value={opt.option_text}
                    onChange={(e) => handleOptionTextChange(idx, e.target.value)}
                    placeholder={`Option ${opt.option_key} text...`}
                    className="flex-1 px-3 py-1.5 text-xs rounded-md border border-border bg-surface text-text focus:outline-none focus:ring-2 focus:ring-primary/30"
                  />
                  <button
                    type="button"
                    onClick={() => handleRemoveOption(idx)}
                    className="p-1.5 text-text-muted hover:text-danger rounded"
                    title="Remove option"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>
              ))}
            </div>
          </div>

          {/* Solution / Correct Answer */}
          <div>
            <label className="block text-xs font-semibold text-text mb-1">
              Correct Answer Key
            </label>
            <div className="flex items-center gap-3">
              <select
                value={answer}
                onChange={(e) => setAnswer(e.target.value)}
                className="px-3 py-1.5 text-xs rounded-md border border-border bg-surface text-text focus:outline-none focus:ring-2 focus:ring-primary/30 w-48 font-mono"
              >
                <option value="">No Answer Associated</option>
                {options.map((opt) => (
                  <option key={opt.option_key} value={opt.option_key}>
                    Option {opt.option_key} ({opt.option_text.slice(0, 30)}...)
                  </option>
                ))}
              </select>
              {question.answer_status === "INVALID" && (
                <span className="text-danger text-xs font-medium flex items-center gap-1">
                  <AlertTriangle className="w-3.5 h-3.5" /> Flagged as INVALID (key does not match options)
                </span>
              )}
              {question.answer_status === "UNCERTAIN" && (
                <span className="text-warning text-xs font-medium flex items-center gap-1">
                  <AlertTriangle className="w-3.5 h-3.5" /> Flagged as uncertain by pipeline
                </span>
              )}
            </div>
          </div>

          {/* Provenance Footer */}
          <div className="pt-4 border-t border-border/80 text-[11px] text-text-muted space-y-1 bg-slate-50 p-3 rounded">
            <div>
              <strong>Document ID:</strong> {question.document_id}
            </div>
            <div>
              <strong>Source Pages:</strong> [{question.source_pages.join(", ")}]
            </div>
            {question.is_reviewed && (
              <div>
                <strong>Reviewed:</strong> Yes (Marked verified)
              </div>
            )}
          </div>
        </Card>
      </div>
    </div>
  );
}
