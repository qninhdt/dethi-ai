"use client";

import { useState } from "react";
import { useAuth } from "@/components/auth-provider";
import { SignIn } from "@/components/sign-in";
import { LoadingPage } from "@/components/loading";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Upload, FileText, CheckCircle, AlertCircle } from "lucide-react";
import { uploadDocument } from "@/lib/api";
import { useRouter } from "next/navigation";
import { toast } from "sonner";

export default function UploadPage() {
  const { user, loading } = useAuth();
  const router = useRouter();
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [dragActive, setDragActive] = useState(false);

  if (loading) {
    return <LoadingPage />;
  }

  if (!user) {
    return <SignIn />;
  }

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const droppedFile = e.dataTransfer.files[0];
      if (validateFile(droppedFile)) {
        setFile(droppedFile);
      }
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const selectedFile = e.target.files[0];
      if (validateFile(selectedFile)) {
        setFile(selectedFile);
      }
    }
  };

  const validateFile = (file: File): boolean => {
    const allowedTypes = [
      "application/pdf",
      "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ];
    const maxSize = 50 * 1024 * 1024; // 50MB

    if (!allowedTypes.includes(file.type)) {
      toast.error("Please upload a PDF or DOCX file");
      return false;
    }

    if (file.size > maxSize) {
      toast.error("File size must be less than 50MB");
      return false;
    }

    return true;
  };

  const handleUpload = async () => {
    if (!file) return;

    setUploading(true);
    try {
      const result = await uploadDocument(file);
      toast.success("Document uploaded successfully");
      router.push(`/documents/${result.id}`);
    } catch (error) {
      console.error("Upload failed:", error);
      toast.error("Failed to upload document");
    } finally {
      setUploading(false);
    }
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return "0 Bytes";
    const k = 1024;
    const sizes = ["Bytes", "KB", "MB", "GB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
  };

  return (
    <div className="container mx-auto py-8">
      <div className="max-w-2xl mx-auto">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-foreground">
            Upload Document
          </h1>
          <p className="mt-2 text-muted-foreground">
            Upload a PDF or DOCX file to generate AI-powered exam questions
          </p>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>Select File</CardTitle>
            <CardDescription>
              Supported formats: PDF, DOCX (Max size: 50MB)
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* File Upload Area */}
            <div
              className={`relative border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
                dragActive
                  ? "border-primary bg-primary/5"
                  : "border-muted-foreground/25 hover:border-muted-foreground/50"
              }`}
              onDragEnter={handleDrag}
              onDragLeave={handleDrag}
              onDragOver={handleDrag}
              onDrop={handleDrop}
            >
              <input
                type="file"
                id="file-upload"
                className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                accept=".pdf,.docx"
                onChange={handleFileChange}
                disabled={uploading}
              />

              <div className="space-y-4">
                <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-primary/10">
                  <Upload className="h-8 w-8 text-primary" />
                </div>

                {file ? (
                  <div className="space-y-2">
                    <div className="flex items-center justify-center space-x-2 text-sm">
                      <FileText className="h-4 w-4 text-primary" />
                      <span className="font-medium text-foreground">
                        {file.name}
                      </span>
                    </div>
                    <p className="text-xs text-muted-foreground">
                      {formatFileSize(file.size)}
                    </p>
                  </div>
                ) : (
                  <div>
                    <p className="text-lg font-medium text-foreground">
                      Drop your file here, or{" "}
                      <span className="text-primary cursor-pointer hover:underline">
                        browse
                      </span>
                    </p>
                    <p className="text-sm text-muted-foreground">
                      PDF or DOCX files up to 50MB
                    </p>
                  </div>
                )}
              </div>
            </div>

            {/* File Info */}
            {file && (
              <Alert>
                <CheckCircle className="h-4 w-4" />
                <AlertDescription>
                  File selected: <strong>{file.name}</strong> (
                  {formatFileSize(file.size)})
                </AlertDescription>
              </Alert>
            )}

            {/* Upload Button */}
            <div className="flex justify-end space-x-4">
              {file && (
                <Button
                  variant="outline"
                  onClick={() => setFile(null)}
                  disabled={uploading}
                >
                  Clear
                </Button>
              )}
              <Button
                onClick={handleUpload}
                disabled={!file || uploading}
                className="min-w-[120px]"
              >
                {uploading ? (
                  <>
                    <Upload className="mr-2 h-4 w-4 animate-spin" />
                    Uploading...
                  </>
                ) : (
                  <>
                    <Upload className="mr-2 h-4 w-4" />
                    Upload
                  </>
                )}
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Info Section */}
        <div className="mt-8 space-y-4">
          <Alert>
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>
              <strong>Processing Time:</strong> OCR and AI analysis typically
              takes 2-5 minutes depending on document length.
            </AlertDescription>
          </Alert>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm">What happens next?</CardTitle>
              </CardHeader>
              <CardContent className="text-sm text-muted-foreground space-y-2">
                <p>1. OCR extracts text from your document</p>
                <p>2. AI analyzes content and creates questions</p>
                <p>3. You can review and select questions</p>
                <p>4. Generate new exams based on selections</p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm">Supported Content</CardTitle>
              </CardHeader>
              <CardContent className="text-sm text-muted-foreground space-y-2">
                <p>• Mathematical formulas</p>
                <p>• Technical diagrams and figures</p>
                <p>• Multiple languages</p>
                <p>• Academic and educational content</p>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
}
