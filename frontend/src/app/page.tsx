"use client";

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
import {
  FileText,
  Zap,
  Brain,
  Download,
  Upload,
  ArrowRight,
} from "lucide-react";
import Link from "next/link";
import { Markdown } from "@/components/markdown";

export default function Home() {
  const { user, loading } = useAuth();

  if (loading) {
    return <LoadingPage />;
  }

  if (!user) {
    return <SignIn />;
  }

  return (
    <div className="flex flex-col min-h-screen">
      {/* Hero Section */}
      <section className="relative overflow-hidden bg-background py-20 sm:py-32">
        <div className="mx-auto max-w-7xl px-6 lg:px-8">
          <div className="mx-auto max-w-2xl text-center">
            <h1 className="text-4xl font-bold tracking-tight text-foreground sm:text-6xl">
              AI-Powered{" "}
              <span className="bg-gradient-to-r from-primary to-primary/70 bg-clip-text text-transparent">
                Exam Generator
              </span>
            </h1>
            <Markdown>
              {`
                # Markdown
                This is an example of a markdown with math. 
                
                $$ \\int_0^1 x^2 dx = \\frac{1}{3} $$
                
                $x^2$`}
            </Markdown>
            <p className="mt-6 text-lg leading-8 text-muted-foreground">
              Upload your documents and let AI generate intelligent, customized
              exams. Create multiple choice, true/false, and short answer
              questions from any content.
            </p>
            <div className="mt-10 flex items-center justify-center gap-x-6">
              <Button asChild size="lg">
                <Link href="/upload">
                  <Upload className="mr-2 h-4 w-4" />
                  Upload Document
                </Link>
              </Button>
              <Button variant="outline" size="lg" asChild>
                <Link href="/documents">
                  View Documents
                  <ArrowRight className="ml-2 h-4 w-4" />
                </Link>
              </Button>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-24 bg-muted/50">
        <div className="mx-auto max-w-7xl px-6 lg:px-8">
          <div className="mx-auto max-w-2xl text-center">
            <h2 className="text-3xl font-bold tracking-tight text-foreground sm:text-4xl">
              Powerful Features
            </h2>
            <p className="mt-4 text-lg text-muted-foreground">
              Everything you need to create professional exams from your
              documents
            </p>
          </div>

          <div className="mx-auto mt-16 max-w-2xl sm:mt-20 lg:mt-24 lg:max-w-none">
            <dl className="grid max-w-xl grid-cols-1 gap-x-8 gap-y-16 lg:max-w-none lg:grid-cols-3">
              <div className="flex flex-col">
                <dt className="flex items-center gap-x-3 text-base font-semibold leading-7 text-foreground">
                  <Brain className="h-5 w-5 flex-none text-primary" />
                  AI-Powered Analysis
                </dt>
                <dd className="mt-4 flex flex-auto flex-col text-base leading-7 text-muted-foreground">
                  <p className="flex-auto">
                    Advanced OCR and AI analysis extracts key concepts and
                    generates relevant questions from your documents with high
                    accuracy.
                  </p>
                </dd>
              </div>

              <div className="flex flex-col">
                <dt className="flex items-center gap-x-3 text-base font-semibold leading-7 text-foreground">
                  <Zap className="h-5 w-5 flex-none text-primary" />
                  Multiple Question Types
                </dt>
                <dd className="mt-4 flex flex-auto flex-col text-base leading-7 text-muted-foreground">
                  <p className="flex-auto">
                    Generate multiple choice, true/false, and short answer
                    questions. Each type includes detailed answers and
                    explanations.
                  </p>
                </dd>
              </div>

              <div className="flex flex-col">
                <dt className="flex items-center gap-x-3 text-base font-semibold leading-7 text-foreground">
                  <Download className="h-5 w-5 flex-none text-primary" />
                  Export Options
                </dt>
                <dd className="mt-4 flex flex-auto flex-col text-base leading-7 text-muted-foreground">
                  <p className="flex-auto">
                    Export your generated exams to Markdown, PDF, or DOCX format
                    for easy distribution and professional presentation.
                  </p>
                </dd>
              </div>
            </dl>
          </div>
        </div>
      </section>

      {/* Quick Start Section */}
      <section className="py-24">
        <div className="mx-auto max-w-7xl px-6 lg:px-8">
          <div className="mx-auto max-w-2xl text-center">
            <h2 className="text-3xl font-bold tracking-tight text-foreground sm:text-4xl">
              Get Started in Minutes
            </h2>
            <p className="mt-4 text-lg text-muted-foreground">
              Simple workflow to create professional exams
            </p>
          </div>

          <div className="mx-auto mt-16 grid max-w-2xl grid-cols-1 gap-6 sm:mt-20 lg:mx-0 lg:max-w-none lg:grid-cols-3 lg:gap-8">
            <Card>
              <CardHeader>
                <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary">
                  <Upload className="h-6 w-6 text-primary-foreground" />
                </div>
                <CardTitle className="text-base font-semibold leading-7">
                  1. Upload Document
                </CardTitle>
              </CardHeader>
              <CardContent>
                <CardDescription>
                  Upload your PDF or DOCX file. Our AI will extract and analyze
                  the content using advanced OCR technology.
                </CardDescription>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary">
                  <Brain className="h-6 w-6 text-primary-foreground" />
                </div>
                <CardTitle className="text-base font-semibold leading-7">
                  2. AI Analysis
                </CardTitle>
              </CardHeader>
              <CardContent>
                <CardDescription>
                  Our AI identifies key concepts and creates structured
                  questions. Review and select which questions to use for
                  generation.
                </CardDescription>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary">
                  <FileText className="h-6 w-6 text-primary-foreground" />
                </div>
                <CardTitle className="text-base font-semibold leading-7">
                  3. Generate Exam
                </CardTitle>
              </CardHeader>
              <CardContent>
                <CardDescription>
                  Create new questions based on your selections. Export to
                  Markdown, PDF, or DOCX when ready for distribution.
                </CardDescription>
              </CardContent>
            </Card>
          </div>
        </div>
      </section>
    </div>
  );
}
