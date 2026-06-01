import axios from "axios";

export const api = axios.create({
  baseURL: "/api",
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("access_token");

  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }

  return config;
});

export async function login(email: string, password: string) {
  const formData = new URLSearchParams();
  formData.append("username", email);
  formData.append("password", password);

  const response = await api.post("/auth/login", formData, {
    headers: {
      "Content-Type": "application/x-www-form-urlencoded",
    },
  });

  localStorage.setItem("access_token", response.data.access_token);

  return response.data;
}

export async function listKnowledgeBases() {
  const response = await api.get("/knowledge-bases");
  return response.data;
}

export async function listDocuments(knowledgeBaseId: number) {
  const response = await api.get("/documents", {
    params: {
      knowledge_base_id: knowledgeBaseId,
    },
  });

  return response.data;
}

export async function uploadDocument(knowledgeBaseId: number, file: File) {
  const formData = new FormData();
  formData.append("knowledge_base_id", String(knowledgeBaseId));
  formData.append("file", file);

  const response = await api.post("/documents/upload", formData, {
    headers: {
      "Content-Type": "multipart/form-data",
    },
  });

  return response.data;
}

export async function prepareDocumentAsync(documentId: number, force = false) {
  const response = await api.post(`/documents/${documentId}/prepare-async`, null, {
    params: { force },
  });

  return response.data;
}

export async function cancelDocumentIngestion(documentId: number) {
  const response = await api.post(`/documents/${documentId}/cancel-ingestion`);
  return response.data;
}

export async function retryDocumentIngestion(documentId: number, force = true) {
  const response = await api.post(`/documents/${documentId}/retry-ingestion`, null, {
    params: { force },
  });

  return response.data;
}

export async function deleteDocument(documentId: number) {
  const response = await api.delete(`/documents/${documentId}`);
  return response.data;
}

export async function getBatchIngestionStatus(knowledgeBaseId: number) {
  const response = await api.get("/documents/ingestion-status-batch", {
    params: {
      knowledge_base_id: knowledgeBaseId,
    },
  });

  return response.data;
}

export async function prepareBatchAsync(knowledgeBaseId: number, force = false) {
  const response = await api.post("/documents/prepare-batch-async", null, {
    params: {
      knowledge_base_id: knowledgeBaseId,
      force,
    },
  });

  return response.data;
}

export async function cancelBatchIngestion(knowledgeBaseId: number) {
  const response = await api.post("/documents/cancel-batch-ingestion", null, {
    params: {
      knowledge_base_id: knowledgeBaseId,
    },
  });

  return response.data;
}

export async function retryBatchIngestion(knowledgeBaseId: number, force = true) {
  const response = await api.post("/documents/retry-batch-ingestion", null, {
    params: {
      knowledge_base_id: knowledgeBaseId,
      force,
    },
  });

  return response.data;
}