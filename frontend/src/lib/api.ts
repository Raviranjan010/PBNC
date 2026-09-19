import { getToken } from "./auth";
import {
  User,
  Document,
  DocumentDetail,
  ProcessingStatus,
  Question,
  QuestionListResponse,
  QuestionUpdatePayload,
  AnswerKey,
  DocumentReviewItemsResponse,
  AnalyticsData,
} from "./types";

const API_BASE = "/api/v1";

export class ApiError extends Error {
  status: number;
  data: any;

  constructor(status: number, message: string, data?: any) {
    super(message);
    this.status = status;
    this.data = data;
    this.name = "ApiError";
  }
}

async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const token = getToken();
  const headers: Record<string, string> = {
    ...(options.headers as Record<string, string>),
  };

  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  // Set json content-type if body is object and not FormData
  if (options.body && !(options.body instanceof FormData)) {
    headers["Content-Type"] = "application/json";
  }

  const res = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers,
  });

  if (!res.ok) {
    let errorDetail = `Request failed with status ${res.status}`;
    let errorData = null;
    try {
      errorData = await res.json();
      if (errorData.detail) {
        errorDetail = typeof errorData.detail === "string" ? errorData.detail : JSON.stringify(errorData.detail);
      }
    } catch {
      // Body not JSON
    }
    throw new ApiError(res.status, errorDetail, errorData);
  }

  // Handle empty responses
  if (res.status === 204) {
    return {} as T;
  }

  return (await res.json()) as T;
}

export const api = {
  auth: {
    register: (data: { email: string; password: string; full_name?: string }) =>
      request<User>("/auth/register", {
        method: "POST",
        body: JSON.stringify(data),
      }),
    login: (data: { email: string; password: string }) =>
      request<{ access_token: string; token_type: string; user_id: string; email: string }>("/auth/login", {
        method: "POST",
        body: JSON.stringify(data),
      }),
    me: () => request<User>("/auth/me"),
  },

  documents: {
    upload: (file: File) => {
      const formData = new FormData();
      formData.append("file", file);
      return request<{ document_id: string; job_id: string; filename: string; status: string; message: string }>(
        "/documents/upload",
        {
          method: "POST",
          body: formData,
        }
      );
    },
    list: () => request<Document[]>("/documents"),
    get: (id: string) => request<DocumentDetail>(`/documents/${id}`),
    getStatus: (id: string) => request<ProcessingStatus>(`/documents/${id}/status`),
    getPageImageUrl: (id: string, pageNum: number) => `${API_BASE}/documents/${id}/pages/${pageNum}`,
    relate: (id: string, relatedId: string, relationshipType: string = "ANSWER_KEY") =>
      request<{ id: string }>(`/documents/${id}/related`, {
        method: "POST",
        body: JSON.stringify({
          related_document_id: relatedId,
          relationship_type: relationshipType,
        }),
      }),
  },

  questions: {
    listForDoc: (
      docId: string,
      params?: { status?: string; review_required?: boolean; min_confidence?: number; search?: string }
    ) => {
      const q = new URLSearchParams();
      if (params?.status) q.set("status", params.status);
      if (params?.review_required !== undefined) q.set("review_required", String(params.review_required));
      if (params?.min_confidence !== undefined) q.set("min_confidence", String(params.min_confidence));
      if (params?.search) q.set("search", params.search);
      const queryStr = q.toString() ? `?${q.toString()}` : "";
      return request<QuestionListResponse>(`/documents/${docId}/questions${queryStr}`);
    },
    get: (id: string) => request<Question>(`/questions/${id}`),
    patch: (id: string, data: QuestionUpdatePayload) =>
      request<Question>(`/questions/${id}`, {
        method: "PATCH",
        body: JSON.stringify(data),
      }),
  },

  answers: {
    getForDoc: (docId: string) => request<AnswerKey[]>(`/documents/${docId}/answers`),
  },

  review: {
    getForDoc: (docId: string) => request<DocumentReviewItemsResponse>(`/documents/${docId}/review-items`),
    getQueue: () => request<Question[]>("/review/queue"),
  },

  analytics: {
    get: () => request<AnalyticsData>("/analytics"),
  },

  exports: {
    getJsonUrl: (docId: string) => `${API_BASE}/documents/${docId}/export/json`,
    getCsvUrl: (docId: string) => `${API_BASE}/documents/${docId}/export/csv`,
  },
};
