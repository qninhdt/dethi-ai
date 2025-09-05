import { auth } from "./firebase";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8080";

async function getAuthHeaders() {
  const user = auth.currentUser;
  if (!user) {
    throw new Error("User not authenticated");
  }

  const token = await user.getIdToken();
  return {
    Authorization: `Bearer ${token}`,
    "Content-Type": "application/json",
  };
}

export async function listDocuments() {
  const headers = await getAuthHeaders();

  const response = await fetch(`${API_BASE_URL}/documents`, {
    headers,
  });

  if (!response.ok) {
    throw new Error("Failed to fetch documents");
  }

  return response.json();
}

export async function uploadDocument(file: File) {
  const formData = new FormData();
  formData.append("file", file);

  const user = auth.currentUser;
  if (!user) {
    throw new Error("User not authenticated");
  }

  const token = await user.getIdToken();

  const response = await fetch(`${API_BASE_URL}/documents`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
    },
    body: formData,
  });

  if (!response.ok) {
    throw new Error("Failed to upload document");
  }

  return response.json();
}

export async function getDocument(docId: string) {
  const headers = await getAuthHeaders();

  const response = await fetch(`${API_BASE_URL}/documents/${docId}`, {
    headers,
  });

  if (!response.ok) {
    throw new Error("Failed to fetch document");
  }

  return response.json();
}

export async function getDocumentQuestions(docId: string) {
  const headers = await getAuthHeaders();

  const response = await fetch(`${API_BASE_URL}/documents/${docId}/questions`, {
    headers,
  });

  if (!response.ok) {
    throw new Error("Failed to fetch questions");
  }

  return response.json();
}

export async function generateExam(
  docId: string,
  selectedIds: string[],
  targetCount: number
) {
  const headers = await getAuthHeaders();

  const response = await fetch(`${API_BASE_URL}/documents/${docId}/generate`, {
    method: "POST",
    headers,
    body: JSON.stringify({
      selected_ids: selectedIds,
      target_count: targetCount,
    }),
  });

  if (!response.ok) {
    throw new Error("Failed to generate exam");
  }

  return response.json();
}

export async function getGeneratedExam(docId: string, genId: string) {
  const headers = await getAuthHeaders();

  const response = await fetch(
    `${API_BASE_URL}/documents/${docId}/exams/${genId}`,
    {
      headers,
    }
  );

  if (!response.ok) {
    throw new Error("Failed to fetch generated exam");
  }

  return response.json();
}

export async function exportExam(
  docId: string,
  genId: string,
  format: "markdown" | "pdf" | "docx"
) {
  const user = auth.currentUser;
  if (!user) {
    throw new Error("User not authenticated");
  }

  const token = await user.getIdToken();
  const headers = {
    Authorization: `Bearer ${token}`,
  };

  const response = await fetch(
    `${API_BASE_URL}/documents/${docId}/exams/${genId}/export?format=${format}`,
    {
      headers,
    }
  );

  if (!response.ok) {
    throw new Error("Failed to export exam");
  }

  if (format === "pdf" || format === "docx") {
    return response.blob();
  } else {
    return response.text();
  }
}

export async function listGeneratedExams(docId: string) {
  const headers = await getAuthHeaders();

  const response = await fetch(`${API_BASE_URL}/documents/${docId}/exams`, {
    headers,
  });

  if (!response.ok) {
    throw new Error("Failed to fetch generated exams");
  }

  return response.json();
}

export async function deleteDocument(docId: string) {
  const headers = await getAuthHeaders();

  const response = await fetch(`${API_BASE_URL}/documents/${docId}`, {
    method: "DELETE",
    headers,
  });

  if (!response.ok) {
    throw new Error("Failed to delete document");
  }

  return response.json();
}

export async function deleteGeneratedExam(docId: string, genId: string) {
  const headers = await getAuthHeaders();

  const response = await fetch(
    `${API_BASE_URL}/documents/${docId}/exams/${genId}`,
    {
      method: "DELETE",
      headers,
    }
  );

  if (!response.ok) {
    throw new Error("Failed to delete generated exam");
  }

  return response.json();
}
