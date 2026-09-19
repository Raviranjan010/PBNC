export interface User {
  id: string;
  email: string;
  full_name?: string | null;
  is_active: boolean;
  created_at: string;
}

export interface AuthTokens {
  access_token: string;
  token_type: string;
  user_id: string;
  email: string;
}

export interface DocumentPage {
  id: string;
  page_number: number;
  extracted_text?: string | null;
  width?: number | null;
  height?: number | null;
  image_url?: string | null;
}

export interface Document {
  id: string;
  user_id: string;
  filename: string;
  original_filename: string;
  file_type: string;
  mime_type: string;
  file_size_bytes: number;
  page_count: number;
  status: "QUEUED" | "PROCESSING" | "COMPLETED" | "PARTIAL" | "REVIEW_REQUIRED" | "FAILED";
  average_confidence?: number | null;
  created_at: string;
  updated_at: string;
}

export interface DocumentDetail extends Document {
  questions_count: number;
  review_required_count: number;
  warnings_count: number;
  pages: DocumentPage[];
  related_document_ids: string[];
}

export interface StepDetail {
  step: string;
  message: string;
  timestamp: string;
}

export interface ProcessingStatus {
  document_id: string;
  job_id: string;
  status: string;
  current_step: string;
  step_details: StepDetail[];
  error_message?: string | null;
  started_at?: string | null;
  completed_at?: string | null;
}

export interface Option {
  id?: string;
  option_key: string;
  option_text: string;
}

export interface Question {
  id: string;
  document_id: string;
  question_number: string;
  question_text: string;
  question_type: string;
  options: Option[];
  answer?: string | null;
  answer_status: "CONFIRMED" | "UNCERTAIN" | "NOT_FOUND";
  answer_source_page?: number | null;
  confidence: number;
  status: "VERIFIED" | "PARTIAL" | "REVIEW_REQUIRED";
  review_required: boolean;
  is_reviewed: boolean;
  source_pages: number[];
  created_at: string;
  updated_at: string;
}

export interface QuestionListResponse {
  total: number;
  items: Question[];
}

export interface QuestionUpdatePayload {
  question_text?: string;
  question_type?: string;
  options?: { option_key: string; option_text: string }[];
  answer?: string | null;
  status?: string;
  review_required?: boolean;
  is_reviewed?: boolean;
}

export interface AnswerKey {
  id: string;
  document_id: string;
  raw_key_text?: string | null;
  detected_format?: string | null;
  source_page?: number | null;
  parsed_mappings: Record<string, string>;
  created_at: string;
}

export interface ReviewItem {
  id: string;
  document_id: string;
  question_id?: string | null;
  issue_type: string;
  description: string;
  is_resolved: boolean;
  resolved_by?: string | null;
  resolved_at?: string | null;
  created_at: string;
}

export interface ExtractionWarning {
  id: string;
  document_id: string;
  question_id?: string | null;
  stage: string;
  warning_code: string;
  message: string;
  severity: string;
  created_at: string;
}

export interface DocumentReviewItemsResponse {
  document_id: string;
  review_items: ReviewItem[];
  warnings: ExtractionWarning[];
}

export interface AnalyticsData {
  total_documents: number;
  processed_documents: number;
  total_questions: number;
  review_required_questions: number;
  verified_questions: number;
  partial_questions: number;
  average_confidence: number;
  status_distribution: Record<string, number>;
  warning_counts_by_stage: Record<string, number>;
}
