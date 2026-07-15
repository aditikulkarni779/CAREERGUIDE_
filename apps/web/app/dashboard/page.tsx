"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { api, tokenStore, type User } from "@/lib/api";

export default function DashboardPage() {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const token = tokenStore.access();
    if (!token) {
      router.push("/login");
      return;
    }
    api
      .me(token)
      .then(setUser)
      .catch(() => {
        tokenStore.clear();
        router.push("/login");
      });
  }, [router]);

  if (error) return <main className="p-8 text-red-600">{error}</main>;
  if (!user) return <main className="p-8 text-gray-500">Loading…</main>;

  return (
    <main className="mx-auto max-w-2xl space-y-4 p-8">
      <h1 className="text-2xl font-bold">Dashboard</h1>
      <p className="text-gray-600">
        Signed in as <span className="font-medium">{user.email}</span> ({user.role})
      </p>
      <p className="text-sm text-gray-400">
        Phase 0 shell. Career Twin, readiness score, and widgets land in Week 3–4.
      </p>
      <button
        onClick={() => {
          tokenStore.clear();
          router.push("/login");
        }}
        className="rounded-md border border-gray-300 px-4 py-2 text-sm"
      >
        Sign out
      </button>
    </main>
  );
}
