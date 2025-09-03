"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { useAuth } from "@/components/auth-provider";
import { FileText, Chrome } from "lucide-react";

export function SignIn() {
  const { signInWithGoogle } = useAuth();
  const [isLoading, setIsLoading] = useState(false);

  const handleSignIn = async () => {
    setIsLoading(true);
    try {
      await signInWithGoogle();
    } catch (error) {
      console.error("Sign in failed:", error);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-background">
      <Card className="w-[400px]">
        <CardHeader className="text-center">
          <div className="mx-auto mb-4 flex h-20 w-20 items-center justify-center rounded-full bg-primary/10">
            <FileText className="h-10 w-10 text-primary" />
          </div>
          <CardTitle className="text-2xl font-bold">
            Welcome to DethiAI
          </CardTitle>
          <CardDescription>
            Sign in to upload documents and generate AI-powered exams
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Button
            onClick={handleSignIn}
            disabled={isLoading}
            className="w-full"
            size="lg"
          >
            <Chrome className="mr-2 h-4 w-4" />
            {isLoading ? "Signing in..." : "Sign in with Google"}
          </Button>

          <div className="mt-6 text-center text-sm text-muted-foreground">
            <p>
              By signing in, you agree to our terms of service and privacy
              policy.
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
