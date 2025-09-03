"use client";

import { useState, useEffect } from "react";
import { useAuth } from "@/components/auth-provider";
import { SignIn } from "@/components/sign-in";
import { LoadingPage, Loading } from "@/components/loading";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  FileText,
  Upload,
  Clock,
  CheckCircle,
  AlertCircle,
  Plus,
} from "lucide-react";
import Link from "next/link";
import { formatDistanceToNow } from "date-fns";
import { listDocuments } from "@/lib/api";
import { toast } from "sonner";

interface Document {
  id: string;
  filename: string;
  content_type: string;
  size: number;
  storage_path: string;
  created_at?: number;
  created_by: string;
  ocr_status: "pending" | "processing" | "done" | "error";
  extract_status: "pending" | "processing" | "done" | "error";
}

export default function DocumentsPage() {
  const { user, loading } = useAuth();
  const [documents, setDocuments] = useState<Document[]>([]);
  const [documentsLoading, setDocumentsLoading] = useState(true);

  useEffect(() => {
    if (user) {
      loadDocuments();
    }
  }, [user]);

  const loadDocuments = async () => {
    try {
      setDocumentsLoading(true);
      const response = await listDocuments();
      setDocuments(response.documents || []);
    } catch (error) {
      console.error("Failed to load documents:", error);
      toast.error("Failed to load documents");
    } finally {
      setDocumentsLoading(false);
    }
  };

  const refreshDocuments = () => {
    loadDocuments();
  };

  if (loading) {
    return <LoadingPage />;
  }

  if (!user) {
    return <SignIn />;
  }

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return "0 Bytes";
    const k = 1024;
    const sizes = ["Bytes", "KB", "MB", "GB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
  };

  const getStatusBadge = (ocrStatus: string, extractStatus: string) => {
    if (ocrStatus === "error" || extractStatus === "error") {
      return (
        <Badge variant="destructive" className="flex items-center space-x-1">
          <AlertCircle className="h-3 w-3" />
          <span>Error</span>
        </Badge>
      );
    }

    if (ocrStatus === "processing" || extractStatus === "processing") {
      return (
        <Badge variant="secondary" className="flex items-center space-x-1">
          <Clock className="h-3 w-3" />
          <span>Processing</span>
        </Badge>
      );
    }

    if (ocrStatus === "pending" || extractStatus === "pending") {
      return (
        <Badge variant="outline" className="flex items-center space-x-1">
          <Clock className="h-3 w-3" />
          <span>Pending</span>
        </Badge>
      );
    }

    if (ocrStatus === "done" && extractStatus === "done") {
      return (
        <Badge
          variant="default"
          className="flex items-center space-x-1 bg-green-600 hover:bg-green-700"
        >
          <CheckCircle className="h-3 w-3" />
          <span>Ready</span>
        </Badge>
      );
    }

    return null;
  };

  const getFileIcon = (contentType: string) => {
    if (contentType === "application/pdf") {
      return <FileText className="h-4 w-4 text-red-500" />;
    }
    return <FileText className="h-4 w-4 text-blue-500" />;
  };

  if (documentsLoading) {
    return (
      <div className="container mx-auto py-8">
        <div className="flex items-center justify-center min-h-[400px]">
          <Loading size="lg" />
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto py-8">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold text-foreground">My Documents</h1>
          <p className="mt-2 text-muted-foreground">
            Manage your uploaded documents and generated exams
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={refreshDocuments}>
            Refresh
          </Button>
          <Button asChild>
            <Link href="/upload">
              <Plus className="mr-2 h-4 w-4" />
              Upload Document
            </Link>
          </Button>
        </div>
      </div>

      {documents.length === 0 ? (
        <div className="text-center py-12">
          <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-muted">
            <FileText className="h-8 w-8 text-muted-foreground" />
          </div>
          <h3 className="mt-4 text-lg font-semibold text-foreground">
            No documents yet
          </h3>
          <p className="mt-2 text-sm text-muted-foreground">
            Upload your first document to get started with AI-powered exam
            generation.
          </p>
          <div className="mt-6">
            <Button asChild>
              <Link href="/upload">
                <Upload className="mr-2 h-4 w-4" />
                Upload Document
              </Link>
            </Button>
          </div>
        </div>
      ) : (
        <div className="grid gap-6">
          {documents.map((doc) => (
            <Card key={doc.id} className="hover:shadow-md transition-shadow">
              <CardHeader className="pb-4">
                <div className="flex items-start justify-between">
                  <div className="flex items-start space-x-3">
                    {getFileIcon(doc.content_type)}
                    <div className="min-w-0 flex-1">
                      <CardTitle className="text-lg font-medium text-foreground truncate">
                        {doc.filename}
                      </CardTitle>
                      <CardDescription className="mt-1">
                        {formatFileSize(doc.size)} • Uploaded{" "}
                        {doc.created_at
                          ? formatDistanceToNow(
                              new Date(doc.created_at * 1000),
                              {
                                addSuffix: true,
                              }
                            )
                          : "recently"}
                      </CardDescription>
                    </div>
                  </div>
                  {getStatusBadge(doc.ocr_status, doc.extract_status)}
                </div>
              </CardHeader>

              <CardContent className="pt-0">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-4 text-sm text-muted-foreground">
                    <div className="flex items-center space-x-1">
                      <span>OCR:</span>
                      <span
                        className={`font-medium ${
                          doc.ocr_status === "done"
                            ? "text-green-600"
                            : doc.ocr_status === "error"
                            ? "text-red-600"
                            : "text-yellow-600"
                        }`}
                      >
                        {doc.ocr_status}
                      </span>
                    </div>
                    <div className="flex items-center space-x-1">
                      <span>Extract:</span>
                      <span
                        className={`font-medium ${
                          doc.extract_status === "done"
                            ? "text-green-600"
                            : doc.extract_status === "error"
                            ? "text-red-600"
                            : "text-yellow-600"
                        }`}
                      >
                        {doc.extract_status}
                      </span>
                    </div>
                  </div>

                  <div className="flex items-center space-x-2">
                    {doc.ocr_status === "done" &&
                      doc.extract_status === "done" && (
                        <Button variant="outline" size="sm" asChild>
                          <Link href={`/documents/${doc.id}`}>
                            View Questions
                          </Link>
                        </Button>
                      )}
                    <Button size="sm" asChild>
                      <Link href={`/documents/${doc.id}`}>View Details</Link>
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
