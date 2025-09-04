"use client";

import { useState, useEffect } from "react";
import { useAuth } from "@/components/auth-provider";
import { SignIn } from "@/components/sign-in";
import { LoadingPage, Loading } from "@/components/loading";
import { LaTeX } from "@/components/latex";
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
  Download,
  RefreshCw,
  Eye,
  EyeOff,
  Trash2,
} from "lucide-react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { formatDistanceToNow } from "date-fns";
import { getGeneratedExam, exportExam, deleteGeneratedExam } from "@/lib/api";
import { toast } from "sonner";

interface GeneratedExam {
  metadata: {
    title: string;
    duration_minutes?: number;
    created_at?: number;
    updated_at?: number;
  };
  status: "pending" | "processing" | "done" | "error";
  total: number;
  completed: number;
  elements: GeneratedQuestion[];
}

interface GeneratedQuestion {
  id?: string;
  type?: "multiple_choice" | "true_false" | "short_answer";
  status: "pending" | "processing" | "done" | "error";
  content?: string;
  data?: {
    options?: string[];
    clauses?: string[];
  };
  answer?: {
    selected_options?: number;
    explanation?: string;
    error_analysis?: string[];
    clause_correctness?: boolean[];
    general_explanation?: string;
    explanations?: string[];
    answer_text?: string;
  };
  error?: string;
}

export default function GeneratedExamPage() {
  const { user, loading } = useAuth();
  const params = useParams();
  const router = useRouter();
  const docId = params.docId as string;
  const genId = params.genId as string;

  const [exam, setExam] = useState<GeneratedExam | null>(null);
  const [showAnswers, setShowAnswers] = useState(false);
  const [examLoading, setExamLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [exporting, setExporting] = useState<"latex" | "pdf" | null>(null);
  const [deleting, setDeleting] = useState(false);

  useEffect(() => {
    if (user && docId && genId) {
      loadExam();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [docId, genId, user]);

  useEffect(() => {
    // Set up polling for updates if exam is not complete
    if (!exam) return;

    if (exam.status === "done" || exam.status === "error") return;

    const interval = setInterval(() => {
      loadExam();
    }, 3000);

    return () => clearInterval(interval);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [exam]);

  const loadExam = async () => {
    try {
      setRefreshing(true);
      const examData = await getGeneratedExam(docId, genId);
      setExam(examData);
    } catch (error) {
      console.error("Failed to load exam:", error);
      toast.error("Failed to load exam");
    } finally {
      setRefreshing(false);
      setExamLoading(false);
    }
  };

  const handleExport = async (format: "latex" | "pdf") => {
    try {
      setExporting(format);
      const result = await exportExam(docId, genId, format);

      if (format === "pdf") {
        // Create download link for PDF
        const blob = result as Blob;
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `exam-${genId}.pdf`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
      } else {
        // Create download link for LaTeX
        const text = result as string;
        const blob = new Blob([text], { type: "text/plain" });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `exam-${genId}.tex`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
      }

      toast.success(`${format.toUpperCase()} exported successfully`);
    } catch (error) {
      console.error(`Failed to export ${format}:`, error);
      toast.error(`Failed to export ${format.toUpperCase()}`);
    } finally {
      setExporting(null);
    }
  };

  const handleDeleteExam = async () => {
    if (
      !confirm(
        "Are you sure you want to delete this generated exam? This action cannot be undone."
      )
    ) {
      return;
    }

    try {
      setDeleting(true);
      await deleteGeneratedExam(docId, genId);
      toast.success("Generated exam deleted successfully");
      router.push(`/documents/${docId}`);
    } catch (error) {
      console.error("Failed to delete exam:", error);
      toast.error("Failed to delete exam");
    } finally {
      setDeleting(false);
    }
  };

  if (loading) {
    return <LoadingPage />;
  }

  if (!user) {
    return <SignIn />;
  }

  if (examLoading) {
    return (
      <div className="container mx-auto py-8">
        <div className="flex items-center justify-center min-h-[400px]">
          <Loading size="lg" />
        </div>
      </div>
    );
  }

  if (!exam) {
    return (
      <div className="container mx-auto py-8">
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>Generated exam not found</AlertDescription>
        </Alert>
      </div>
    );
  }

  const getQuestionStatusBadge = (status: string) => {
    switch (status) {
      case "done":
        return (
          <Badge variant="default" className="bg-green-600 hover:bg-green-700">
            <CheckCircle className="mr-1 h-3 w-3" />
            Complete
          </Badge>
        );
      case "processing":
        return (
          <Badge variant="secondary">
            <Clock className="mr-1 h-3 w-3" />
            Processing
          </Badge>
        );
      case "pending":
        return (
          <Badge variant="outline">
            <Clock className="mr-1 h-3 w-3" />
            Pending
          </Badge>
        );
      case "error":
        return (
          <Badge variant="destructive">
            <AlertCircle className="mr-1 h-3 w-3" />
            Error
          </Badge>
        );
      default:
        return null;
    }
  };

  if (examLoading) {
    return (
      <div className="container mx-auto py-8">
        <div className="flex items-center justify-center min-h-[400px]">
          <Loading size="lg" />
        </div>
      </div>
    );
  }

  if (!exam) {
    return (
      <div className="container mx-auto py-8">
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>Generated exam not found</AlertDescription>
        </Alert>
      </div>
    );
  }

  const progressPercentage =
    exam && exam.total > 0
      ? Math.round((exam.completed / exam.total) * 100)
      : 0;

  return (
    <div className="container mx-auto py-8">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <Button variant="outline" size="sm" asChild>
          <Link href={`/documents/${docId}`}>
            <ArrowLeft className="mr-2 h-4 w-4" />
            Back to Document
          </Link>
        </Button>
        <Button
          variant="destructive"
          size="sm"
          onClick={handleDeleteExam}
          disabled={deleting}
        >
          {deleting ? (
            <RefreshCw className="mr-2 h-4 w-4 animate-spin" />
          ) : (
            <Trash2 className="mr-2 h-4 w-4" />
          )}
          Delete Exam
        </Button>
      </div>

      {/* Exam Info */}
      <Card className="mb-8">
        <CardHeader>
          <div className="flex items-start justify-between">
            <div className="flex items-start space-x-3">
              <FileText className="h-6 w-6 text-primary mt-1" />
              <div>
                <CardTitle className="text-xl">
                  <LaTeX>{exam.metadata.title}</LaTeX>
                </CardTitle>
                <CardDescription className="mt-1">
                  Created{" "}
                  {exam.metadata.created_at
                    ? formatDistanceToNow(
                        new Date(exam.metadata.created_at * 1000),
                        {
                          addSuffix: true,
                        }
                      )
                    : "recently"}
                  {exam.metadata.duration_minutes && (
                    <> • Duration: {exam.metadata.duration_minutes} minutes</>
                  )}
                </CardDescription>
              </div>
            </div>
            <div className="flex items-center space-x-2">
              {exam.status === "done" && (
                <>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setShowAnswers(!showAnswers)}
                  >
                    {showAnswers ? (
                      <>
                        <EyeOff className="mr-2 h-4 w-4" />
                        Hide Answers
                      </>
                    ) : (
                      <>
                        <Eye className="mr-2 h-4 w-4" />
                        Show Answers
                      </>
                    )}
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleExport("latex")}
                    disabled={exporting === "latex"}
                  >
                    {exporting === "latex" ? (
                      <RefreshCw className="mr-2 h-4 w-4 animate-spin" />
                    ) : (
                      <Download className="mr-2 h-4 w-4" />
                    )}
                    LaTeX
                  </Button>
                  <Button
                    size="sm"
                    onClick={() => handleExport("pdf")}
                    disabled={exporting === "pdf"}
                  >
                    {exporting === "pdf" ? (
                      <RefreshCw className="mr-2 h-4 w-4 animate-spin" />
                    ) : (
                      <Download className="mr-2 h-4 w-4" />
                    )}
                    PDF
                  </Button>
                </>
              )}
              <Button
                variant="outline"
                size="sm"
                onClick={loadExam}
                disabled={refreshing}
              >
                <RefreshCw
                  className={`mr-2 h-4 w-4 ${refreshing ? "animate-spin" : ""}`}
                />
                Refresh
              </Button>
            </div>
          </div>
        </CardHeader>

        <CardContent>
          <div className="space-y-4">
            {/* Generation Progress */}
            <div>
              <div className="flex items-center justify-between text-sm mb-2">
                <span className="font-medium">Generation Progress</span>
                <span>
                  {exam.completed} of {exam.total} questions (
                  {progressPercentage}%)
                </span>
              </div>
              <Progress value={progressPercentage} className="h-2" />
              <div className="text-xs text-muted-foreground mt-2">
                Status: {exam.status} • Last updated{" "}
                {exam.metadata.updated_at
                  ? formatDistanceToNow(
                      new Date(exam.metadata.updated_at * 1000),
                      {
                        addSuffix: true,
                      }
                    )
                  : "recently"}
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Questions */}
      <Card>
        <CardHeader>
          <CardTitle>Generated Questions</CardTitle>
          <CardDescription>
            AI-generated questions with answers and explanations
          </CardDescription>
        </CardHeader>

        <CardContent>
          <div className="space-y-6">
            {exam.elements.map((question, index) => (
              <div key={question.id ?? index} className="border rounded-lg p-4">
                <div className="flex items-start justify-between mb-4">
                  <div className="flex items-center space-x-2">
                    <Badge variant="outline" className="text-xs">
                      Question {index + 1}
                    </Badge>
                    <Badge variant="outline" className="text-xs">
                      {question.type
                        ? question.type.replace("_", " ")
                        : "Question"}
                    </Badge>
                  </div>
                  {getQuestionStatusBadge(question.status)}
                </div>

                {question.status === "done" && question.content ? (
                  <div className="space-y-4">
                    {/* Question Content */}
                    <div>
                      <LaTeX>{question.content}</LaTeX>
                    </div>

                    {/* Question Options/Clauses */}
                    {question.data?.options && (
                      <div className="space-y-2">
                        {question.data.options.map((option, idx) => (
                          <div
                            key={idx}
                            className={`flex items-center space-x-2 text-sm p-2 rounded ${
                              showAnswers &&
                              question.answer?.selected_options === idx
                                ? "bg-green-100 dark:bg-green-900/20 border border-green-300 dark:border-green-700"
                                : "bg-muted/30"
                            }`}
                          >
                            <span className="text-muted-foreground font-medium">
                              {String.fromCharCode(65 + idx)}.
                            </span>
                            <LaTeX>{option}</LaTeX>
                            {showAnswers &&
                              question.answer?.selected_options === idx && (
                                <CheckCircle className="h-4 w-4 text-green-600 ml-auto" />
                              )}
                          </div>
                        ))}
                      </div>
                    )}

                    {question.data?.clauses && (
                      <div className="space-y-2">
                        {question.data.clauses.map((clause, idx) => (
                          <div
                            key={idx}
                            className={`flex items-center space-x-2 text-sm p-2 rounded ${
                              showAnswers
                                ? question.answer?.clause_correctness?.[idx]
                                  ? "bg-green-100 dark:bg-green-900/20 border border-green-300 dark:border-green-700"
                                  : "bg-red-100 dark:bg-red-900/20 border border-red-300 dark:border-red-700"
                                : "bg-muted/30"
                            }`}
                          >
                            <span className="text-muted-foreground font-medium">
                              {idx + 1}.
                            </span>
                            <LaTeX>{clause}</LaTeX>
                            {showAnswers && (
                              <Badge
                                variant={
                                  question.answer?.clause_correctness?.[idx]
                                    ? "default"
                                    : "destructive"
                                }
                                className="ml-auto text-xs"
                              >
                                {question.answer?.clause_correctness?.[idx]
                                  ? "True"
                                  : "False"}
                              </Badge>
                            )}
                          </div>
                        ))}
                      </div>
                    )}

                    {/* Answer Section */}
                    {showAnswers && question.answer && (
                      <div className="mt-4 p-4 bg-muted/50 rounded-lg">
                        <h4 className="font-medium text-sm mb-2 text-primary">
                          Answer & Explanation
                        </h4>

                        {question.answer.answer_text && (
                          <div className="mb-3">
                            <p className="text-sm font-medium mb-1">Answer:</p>
                            <LaTeX>{question.answer.answer_text}</LaTeX>
                          </div>
                        )}

                        {question.answer.explanation && (
                          <div className="mb-3">
                            <p className="text-sm font-medium mb-1">
                              Explanation:
                            </p>
                            <LaTeX>{question.answer.explanation}</LaTeX>
                          </div>
                        )}

                        {question.answer.general_explanation && (
                          <div className="mb-3">
                            <p className="text-sm font-medium mb-1">
                              General Explanation:
                            </p>
                            <LaTeX>{question.answer.general_explanation}</LaTeX>
                          </div>
                        )}

                        {question.answer.explanations && (
                          <div className="mb-3">
                            <p className="text-sm font-medium mb-1">
                              Detailed Explanations:
                            </p>
                            <div className="space-y-1">
                              {question.answer.explanations.map((exp, idx) => (
                                <div key={idx}>
                                  <span className="font-medium">
                                    {idx + 1}.
                                  </span>{" "}
                                  <LaTeX>{exp}</LaTeX>
                                </div>
                              ))}
                            </div>
                          </div>
                        )}

                        {question.answer.error_analysis && (
                          <div>
                            <p className="text-sm font-medium mb-1">
                              Why other options are incorrect:
                            </p>
                            <div className="space-y-1">
                              {question.answer.error_analysis.map(
                                (error, idx) => {
                                  // Skip the correct option
                                  if (
                                    idx === question.answer?.selected_options
                                  ) {
                                    return null;
                                  }
                                  return (
                                    <div
                                      key={idx}
                                      className="text-sm text-muted-foreground"
                                    >
                                      <span className="font-medium">
                                        {String.fromCharCode(65 + idx)}.
                                      </span>{" "}
                                      <LaTeX>{error}</LaTeX>
                                    </div>
                                  );
                                }
                              )}
                            </div>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                ) : question.status === "error" ? (
                  <Alert variant="destructive">
                    <AlertCircle className="h-4 w-4" />
                    <AlertDescription>
                      {question.error || "Failed to generate this question"}
                    </AlertDescription>
                  </Alert>
                ) : (
                  <div className="flex items-center justify-center py-8">
                    <div className="text-center">
                      {question.status === "processing" ? (
                        <>
                          <RefreshCw className="h-6 w-6 animate-spin mx-auto mb-2 text-muted-foreground" />
                          <p className="text-sm text-muted-foreground">
                            Generating question...
                          </p>
                        </>
                      ) : (
                        <>
                          <Clock className="h-6 w-6 mx-auto mb-2 text-muted-foreground" />
                          <p className="text-sm text-muted-foreground">
                            Waiting to generate...
                          </p>
                        </>
                      )}
                    </div>
                  </div>
                )}

                {index < exam.elements.length - 1 && (
                  <Separator className="mt-6" />
                )}
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Status Alerts */}
      {exam.status === "processing" && (
        <Alert className="mt-6">
          <RefreshCw className="h-4 w-4 animate-spin" />
          <AlertDescription>
            Exam generation is in progress. Questions will appear as they are
            completed. This page will automatically refresh.
          </AlertDescription>
        </Alert>
      )}

      {exam.status === "error" && (
        <Alert variant="destructive" className="mt-6">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            There was an error generating some questions in this exam. Check
            individual question status above.
          </AlertDescription>
        </Alert>
      )}

      {exam.status === "done" && (
        <Alert className="mt-6">
          <CheckCircle className="h-4 w-4" />
          <AlertDescription>
            Exam generation completed successfully! You can now export to LaTeX
            or PDF format.
          </AlertDescription>
        </Alert>
      )}
    </div>
  );
}
