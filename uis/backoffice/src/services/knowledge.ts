// uis/backoffice/src/services/knowledge.ts

export interface SourceChunk {
  source_document: string;
  document_title: string;
  section: string;
  score: number;
  text: string;
}

export interface KnowledgeQueryRequest {
  question: string;
  k?: number;
  min_score?: number;
}

export interface KnowledgeQueryResponse {
  question: string;
  answer: string;
  sources: SourceChunk[];
  sources_count: number;
}

class KnowledgeService {
  private getAuthHeaders(): HeadersInit {
    const token = typeof window !== "undefined" ? localStorage.getItem("access_token") : null;
    return {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    };
  }

  /**
   * Envía una pregunta en lenguaje natural al asistente RAG en FastAPI.
   */
  async queryKnowledgeBase(payload: KnowledgeQueryRequest): Promise<KnowledgeQueryResponse> {
    const res = await fetch("/api/knowledge/query", {
      method: "POST",
      headers: this.getAuthHeaders(),
      body: JSON.stringify({
        question: payload.question,
        k: payload.k ?? 5,
        min_score: payload.min_score ?? 0.70,
      }),
    });

    if (res.status === 401) {
      if (typeof window !== "undefined") {
        window.location.href = "/login";
      }
      throw new Error("Sesión expirada o no autorizada. Redirigiendo al login...");
    }

    if (!res.ok) {
      const errorData = await res.json().catch(() => ({}));
      const errorMsg = typeof errorData.detail === "string"
        ? errorData.detail
        : Array.isArray(errorData.detail)
          ? errorData.detail.map((e: { msg?: string }) => e.msg || JSON.stringify(e)).join(", ")
          : `Error al consultar la base de conocimiento (${res.status})`;
      throw new Error(errorMsg);
    }

    return res.json();
  }
}

export const knowledgeService = new KnowledgeService();

