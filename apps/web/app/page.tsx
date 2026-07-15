import Link from "next/link";

export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center gap-6 p-8">
      <h1 className="text-3xl font-bold">AI Career Copilot</h1>
      <p className="text-gray-500">Your personal AI career mentor.</p>
      <Link
        href="/login"
        className="rounded-md bg-black px-5 py-2 text-sm font-medium text-white"
      >
        Get started
      </Link>
    </main>
  );
}
