"use client";

import { useState, useEffect } from "react";
import { useAuth } from "@/components/auth-provider";
import { SignIn } from "@/components/sign-in";
import { LoadingPage, Loading } from "@/components/loading";
import { Markdown } from "@/components/markdown";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Progress } from "@/components/ui/progress";
import { Separator } from "@/components/ui/separator";
import {
  FileText,
  Clock,
  CheckCircle,
  AlertCircle,
  ArrowLeft,
  Play,
  RefreshCw,
  Trash2,
} from "lucide-react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { formatDistanceToNow } from "date-fns";
import {
  getDocument,
  getDocumentQuestions,
  generateExam,
  listGeneratedExams,
  deleteDocument,
  deleteGeneratedExam,
} from "@/lib/api";
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
  original_exam?: {
    metadata: {
      title: string;
      duration_minutes?: number;
    };
  };
}

interface Question {
  id: string;
  index: number;
  type: "multiple_choice" | "true_false" | "short_answer" | "text";
  content: string;
  data?: {
    options?: string[];
    clauses?: string[];
  };
}

interface GeneratedExam {
  id: string;
  metadata: {
    title: string;
    created_at?: number;
    duration_minutes?: number;
  };
  status: "pending" | "processing" | "done" | "error";
  total: number;
  completed: number;
}

export default function DocumentDetailPage() {
  const { user, loading } = useAuth();
  const params = useParams();
  const router = useRouter();
  const docId = params.docId as string;

  const [document, setDocument] = useState<Document | null>(null);
  const [questions, setQuestions] = useState<Question[]>([]);
  const [generatedExams, setGeneratedExams] = useState<GeneratedExam[]>([]);
  const [selectedQuestions, setSelectedQuestions] = useState<string[]>([]);
  const [documentLoading, setDocumentLoading] = useState(true);
  const [questionsLoading, setQuestionsLoading] = useState(false);
  const [examsLoading, setExamsLoading] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [deleting, setDeleting] = useState(false);

  useEffect(() => {
    if (user && docId) {
      loadDocument();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user, docId]);

  const loadExams = async () => {
    try {
      setExamsLoading(true);
      const response = await listGeneratedExams(docId);
      setGeneratedExams(response.exams || []);
    } catch (error) {
      console.error("Failed to load generated exams:", error);
      toast.error("Failed to load generated exams");
    } finally {
      setExamsLoading(false);
    }
  };

  const loadDocument = async () => {
    try {
      setDocumentLoading(true);
      const doc = await getDocument(docId);
      setDocument(doc);

      // Load questions if document processing is done
      if (doc.extract_status === "done") {
        loadQuestions();
      }

      // Always load generated exams
      loadExams();
    } catch (error) {
      console.error("Failed to load document:", error);
      toast.error("Failed to load document");
    } finally {
      setDocumentLoading(false);
    }
  };

  const loadQuestions = async () => {
    try {
      setQuestionsLoading(true);
      const response = await getDocumentQuestions(docId);
      // Sort questions by index to maintain extraction order
      const sortedQuestions = (response.questions || []).sort(
        (a: Question, b: Question) => a.index - b.index
      );
      setQuestions(sortedQuestions);
    } catch (error) {
      console.error("Failed to load questions:", error);
      toast.error("Failed to load questions");
    } finally {
      setQuestionsLoading(false);
    }
  };

  const handleStartGeneration = async () => {
    if (selectedQuestions.length === 0) {
      toast.error("Please select at least one question");
      return;
    }

    try {
      setGenerating(true);
      const result = await generateExam(
        docId,
        selectedQuestions,
        selectedQuestions.length
      );
      toast.success("Exam generation started!");
      router.push(`/documents/${docId}/exams/${result.generated_exam_id}`);
    } catch (error) {
      console.error("Failed to start generation:", error);
      toast.error("Failed to start exam generation");
    } finally {
      setGenerating(false);
    }
  };

  const handleQuestionToggle = (id: string) => {
    setSelectedQuestions((prev) =>
      prev.includes(id) ? prev.filter((i) => i !== id) : [...prev, id]
    );
  };

  const handleDeleteDocument = async () => {
    if (
      !confirm(
        "Are you sure you want to delete this document and all its generated exams? This action cannot be undone."
      )
    ) {
      return;
    }

    try {
      setDeleting(true);
      await deleteDocument(docId);
      toast.success("Document deleted successfully");
      router.push("/documents");
    } catch (error) {
      console.error("Failed to delete document:", error);
      toast.error("Failed to delete document");
    } finally {
      setDeleting(false);
    }
  };

  const handleDeleteExam = async (examId: string) => {
    if (
      !confirm(
        "Are you sure you want to delete this generated exam? This action cannot be undone."
      )
    ) {
      return;
    }

    try {
      await deleteGeneratedExam(docId, examId);
      toast.success("Generated exam deleted successfully");
      loadExams(); // Refresh the list
    } catch (error) {
      console.error("Failed to delete exam:", error);
      toast.error("Failed to delete exam");
    }
  };

  if (loading) {
    return <LoadingPage />;
  }

  if (!user) {
    return <SignIn />;
  }

  if (documentLoading) {
    return (
      <div className="container mx-auto py-8">
        <div className="flex items-center justify-center min-h-[400px]">
          <Loading size="lg" />
        </div>
      </div>
    );
  }

  if (!document) {
    return (
      <div className="container mx-auto py-8">
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>Document not found</AlertDescription>
        </Alert>
      </div>
    );
  }

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

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return "0 Bytes";
    const k = 1024;
    const sizes = ["Bytes", "KB", "MB", "GB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
  };

  const questionQuestions = questions.filter((q) => q.type !== "text");
  const progressPercentage =
    document.ocr_status === "done" && document.extract_status === "done"
      ? 100
      : document.ocr_status === "processing" ||
        document.extract_status === "processing"
      ? 50
      : 25;

  return (
    <div className="container mx-auto py-8">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <Button variant="outline" size="sm" asChild>
          <Link href="/documents">
            <ArrowLeft className="mr-2 h-4 w-4" />
            Back to Documents
          </Link>
        </Button>
        <Button
          variant="destructive"
          size="sm"
          onClick={handleDeleteDocument}
          disabled={deleting}
        >
          {deleting ? (
            <RefreshCw className="mr-2 h-4 w-4 animate-spin" />
          ) : (
            <Trash2 className="mr-2 h-4 w-4" />
          )}
          Delete Document
        </Button>
      </div>

      {/* Document Info */}
      <Card className="mb-8">
        <CardHeader>
          <div className="flex items-start justify-between">
            <div className="flex items-start space-x-3">
              <FileText className="h-6 w-6 text-primary mt-1" />
              <div>
                <CardTitle className="text-xl">{document.filename}</CardTitle>
                <CardDescription className="mt-1">
                  {formatFileSize(document.size)} • Uploaded{" "}
                  {document.created_at
                    ? formatDistanceToNow(
                        new Date(document.created_at * 1000),
                        {
                          addSuffix: true,
                        }
                      )
                    : "recently"}
                </CardDescription>
              </div>
            </div>
            {getStatusBadge(document.ocr_status, document.extract_status)}
          </div>
        </CardHeader>

        <CardContent>
          <div className="space-y-4">
            {/* Processing Progress */}
            <div>
              <div className="flex items-center justify-between text-sm mb-2">
                <span className="font-medium">Processing Status</span>
                <span>{progressPercentage}%</span>
              </div>
              <Progress value={progressPercentage} className="h-2" />
              <div className="flex justify-between text-xs text-muted-foreground mt-2">
                <span>OCR: {document.ocr_status}</span>
                <span>Extract: {document.extract_status}</span>
              </div>
            </div>

            {/* Original Exam Info */}
            {document.original_exam && (
              <div>
                <h4 className="font-medium text-sm mb-2">Original Content</h4>
                <div className="text-sm text-muted-foreground">
                  <Markdown>{document.original_exam.metadata.title}</Markdown>
                  {document.original_exam.metadata.duration_minutes && (
                    <p className="mt-1">
                      Duration:{" "}
                      {document.original_exam.metadata.duration_minutes} minutes
                    </p>
                  )}
                </div>
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Generated Exams Section */}
      <Card className="mb-8">
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Generated Exams</CardTitle>
              <CardDescription>
                View and manage your generated exams
              </CardDescription>
            </div>
            <div className="flex items-center space-x-2">
              <Button
                variant="outline"
                size="sm"
                onClick={loadExams}
                disabled={examsLoading}
              >
                <RefreshCw
                  className={`mr-2 h-4 w-4 ${
                    examsLoading ? "animate-spin" : ""
                  }`}
                />
                Refresh
              </Button>
            </div>
          </div>
        </CardHeader>

        <CardContent>
          {examsLoading ? (
            <div className="flex items-center justify-center py-8">
              <Loading />
            </div>
          ) : generatedExams.length === 0 ? (
            <div className="text-center py-8">
              <p className="text-muted-foreground">No generated exams yet</p>
              <p className="text-sm text-muted-foreground mt-1">
                Select questions below to generate your first exam
              </p>
            </div>
          ) : (
            <div className="space-y-4">
              {generatedExams.map((exam) => (
                <div
                  key={exam.id}
                  className="border rounded-lg p-4 flex items-center justify-between"
                >
                  <div className="flex items-start space-x-3">
                    <FileText className="h-5 w-5 text-primary mt-0.5" />
                    <div>
                      <h4 className="font-medium">
                        <Markdown>{exam.metadata.title}</Markdown>
                      </h4>
                      <p className="text-sm text-muted-foreground">
                        Created{" "}
                        {exam.metadata.created_at
                          ? formatDistanceToNow(
                              new Date(exam.metadata.created_at * 1000),
                              {
                                addSuffix: true,
                              }
                            )
                          : "recently"}
                        {exam.total > 0 && (
                          <>
                            {" "}
                            • {exam.completed} of {exam.total} questions
                          </>
                        )}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center space-x-2">
                    {exam.status === "done" ? (
                      <Badge
                        variant="default"
                        className="bg-green-600 hover:bg-green-700"
                      >
                        <CheckCircle className="mr-1 h-3 w-3" />
                        Complete
                      </Badge>
                    ) : exam.status === "processing" ? (
                      <Badge variant="secondary">
                        <Clock className="mr-1 h-3 w-3" />
                        Processing
                      </Badge>
                    ) : exam.status === "error" ? (
                      <Badge variant="destructive">
                        <AlertCircle className="mr-1 h-3 w-3" />
                        Error
                      </Badge>
                    ) : (
                      <Badge variant="outline">
                        <Clock className="mr-1 h-3 w-3" />
                        Pending
                      </Badge>
                    )}
                    <Button variant="outline" size="sm" asChild>
                      <Link href={`/documents/${docId}/exams/${exam.id}`}>
                        View
                      </Link>
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleDeleteExam(exam.id)}
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Questions Section */}
      {document.ocr_status === "done" && document.extract_status === "done" && (
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle>Extracted Questions</CardTitle>
                <CardDescription>
                  Select questions to use for generating new exams
                </CardDescription>
              </div>
              <div className="flex items-center space-x-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={loadQuestions}
                  disabled={questionsLoading}
                >
                  <RefreshCw
                    className={`mr-2 h-4 w-4 ${
                      questionsLoading ? "animate-spin" : ""
                    }`}
                  />
                  Refresh
                </Button>
                <Button
                  onClick={handleStartGeneration}
                  disabled={selectedQuestions.length === 0 || generating}
                  size="sm"
                >
                  {generating ? (
                    <>
                      <RefreshCw className="mr-2 h-4 w-4 animate-spin" />
                      Generating...
                    </>
                  ) : (
                    <>
                      <Play className="mr-2 h-4 w-4" />
                      Generate Exam ({selectedQuestions.length})
                    </>
                  )}
                </Button>
              </div>
            </div>
          </CardHeader>

          <CardContent>
            {questionsLoading ? (
              <div className="flex items-center justify-center py-12">
                <Loading size="lg" />
              </div>
            ) : questions.length === 0 ? (
              <div className="text-center py-12">
                <p className="text-muted-foreground">No questions found</p>
              </div>
            ) : (
              <div className="space-y-6">
                {questions.map((question, index) => (
                  <div key={question.id || index}>
                    {question.type === "text" ? (
                      <div className="py-2">
                        <Markdown>{question.content}</Markdown>
                      </div>
                    ) : (
                      <div
                        className={`border rounded-lg p-4 transition-colors ${
                          selectedQuestions.includes(question.id)
                            ? "border-primary bg-primary/5"
                            : "border-border hover:border-border/80"
                        }`}
                      >
                        <div className="flex items-start space-x-3">
                          <input
                            type="checkbox"
                            checked={selectedQuestions.includes(question.id)}
                            onChange={() => handleQuestionToggle(question.id)}
                            className="mt-1 rounded border-border"
                          />
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center space-x-2 mb-2">
                              <span className="text-sm text-muted-foreground">
                                Question {parseInt(question.id) + 1}
                              </span>

                              <Badge variant="outline" className="text-xs">
                                {question.type.replace("_", " ")}
                              </Badge>
                            </div>

                            <div className="mb-3">
                              <Markdown>{question.content}</Markdown>
                            </div>

                            {question.data?.options && (
                              <div className="space-y-1">
                                {question.data.options.map((option, idx) => (
                                  <div
                                    key={idx}
                                    className="flex items-center space-x-2 text-sm"
                                  >
                                    <span className="text-muted-foreground">
                                      {String.fromCharCode(65 + idx)}.
                                    </span>
                                    <Markdown>{option}</Markdown>
                                  </div>
                                ))}
                              </div>
                            )}

                            {question.data?.clauses && (
                              <div className="space-y-1">
                                {question.data.clauses.map((clause, idx) => (
                                  <div
                                    key={idx}
                                    className="flex items-center space-x-2 text-sm"
                                  >
                                    <span className="text-muted-foreground">
                                      {idx + 1}.
                                    </span>
                                    <Markdown>{clause}</Markdown>
                                  </div>
                                ))}
                              </div>
                            )}
                          </div>
                        </div>
                      </div>
                    )}

                    {index < questions.length - 1 &&
                      question.type !== "text" && (
                        <Separator className="my-4" />
                      )}
                  </div>
                ))}

                {questionQuestions.length > 0 && (
                  <div className="flex items-center justify-between pt-4 border-t">
                    <div className="text-sm text-muted-foreground">
                      {selectedQuestions.length} of {questionQuestions.length}{" "}
                      questions selected
                    </div>
                    <div className="flex items-center space-x-2">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() =>
                          setSelectedQuestions(
                            questionQuestions.map((q) => q.id)
                          )
                        }
                      >
                        Select All
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => setSelectedQuestions([])}
                      >
                        Clear All
                      </Button>
                    </div>
                  </div>
                )}
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Error State */}
      {(document.ocr_status === "error" ||
        document.extract_status === "error") && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            There was an error processing this document. Please try uploading
            again or contact support.
          </AlertDescription>
        </Alert>
      )}

      {/* Processing State */}
      {(document.ocr_status === "processing" ||
        document.extract_status === "processing") && (
        <Alert>
          <Clock className="h-4 w-4" />
          <AlertDescription>
            Document is being processed. This may take a few minutes. You can
            refresh this page to check for updates.
          </AlertDescription>
        </Alert>
      )}
    </div>
  );
}
