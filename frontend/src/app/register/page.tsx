"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { api } from "@/lib/api";
import { setAuth } from "@/lib/auth";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { AlertCircle, Lock, Mail, User } from "lucide-react";

export default function RegisterPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [fullName, setFullName] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      await api.auth.register({
        email,
        password,
        full_name: fullName || undefined,
      });

      // Auto-login after successful registration
      const loginRes = await api.auth.login({ email, password });
      localStorage.setItem("papermind_access_token", loginRes.access_token);
      const user = await api.auth.me();
      setAuth(loginRes.access_token, user);
      router.push("/dashboard");
    } catch (err: any) {
      setError(err.message || "Failed to create account. Please check your details.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-md mx-auto mt-12">
      <Card className="p-8">
        <div className="text-center mb-6">
          <div className="inline-flex w-10 h-10 rounded bg-primary text-white font-bold items-center justify-center font-mono text-lg mb-2 shadow-sm">
            P[M]
          </div>
          <h1 className="text-xl font-bold text-text">Create your Account</h1>
          <p className="text-xs text-text-muted mt-1">
            Start extracting structured intelligence from exam papers
          </p>
        </div>

        {error && (
          <div className="mb-4 p-3 bg-danger-light border border-danger/20 rounded-md flex items-center gap-2 text-xs text-danger">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-medium text-text mb-1">
              Full Name
            </label>
            <div className="relative">
              <User className="w-4 h-4 text-text-muted absolute left-3 top-2.5" />
              <input
                type="text"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                placeholder="Dr. Alan Turing"
                className="w-full pl-9 pr-3 py-2 text-xs rounded-md border border-border bg-surface text-text focus:outline-none focus:ring-2 focus:ring-primary/30"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-medium text-text mb-1">
              Email Address
            </label>
            <div className="relative">
              <Mail className="w-4 h-4 text-text-muted absolute left-3 top-2.5" />
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="name@example.com"
                className="w-full pl-9 pr-3 py-2 text-xs rounded-md border border-border bg-surface text-text focus:outline-none focus:ring-2 focus:ring-primary/30"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-medium text-text mb-1">
              Password (min 6 characters)
            </label>
            <div className="relative">
              <Lock className="w-4 h-4 text-text-muted absolute left-3 top-2.5" />
              <input
                type="password"
                required
                minLength={6}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                className="w-full pl-9 pr-3 py-2 text-xs rounded-md border border-border bg-surface text-text focus:outline-none focus:ring-2 focus:ring-primary/30"
              />
            </div>
          </div>

          <Button
            type="submit"
            isLoading={loading}
            className="w-full mt-2"
          >
            Create Account
          </Button>
        </form>

        <div className="mt-6 text-center text-xs text-text-muted">
          Already have an account?{" "}
          <Link href="/login" className="text-primary hover:underline font-medium">
            Sign In
          </Link>
        </div>
      </Card>
    </div>
  );
}
