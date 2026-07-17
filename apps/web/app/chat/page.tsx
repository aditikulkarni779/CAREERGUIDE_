"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useRef, useState } from "react";

import {
  api,
  streamMessage,
  tokenStore,
  type Citation,
  type Conversation,
  type ChatMessage,
  type RoadmapEvent,
} from "@/lib/api";

type UiMessage = {
  role: "user" | "assistant";
  content: string;
  citations: Citation[];
  roadmap?: RoadmapEvent;
  streaming?: boolean;
};

export default function ChatPage() {
  const router = useRouter();
  const [convos, setConvos] = useState<Conversation[]>([]);
  const [activeId, setActiveId] = useState<string | null>(null);
  const [messages, setMessages] = useState<UiMessage[]>([]);
  const [input, setInput] = useState("");
  const [step, setStep] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const endRef = useRef<HTMLDivElement>(null);

  const refreshConvos = useCallback(async () => {
    try {
      setConvos(await api.listConversations());
    } catch {
      tokenStore.clear();
      router.push("/login");
    }
  }, [router]);

  useEffect(() => {
    if (!tokenStore.access()) {
      router.push("/login");
      return;
    }
    refreshConvos();
  }, [router, refreshConvos]);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, step]);

  async function openConversation(id: string) {
    setActiveId(id);
    const history: ChatMessage[] = await api.getMessages(id);
    setMessages(
      history.map((m) => ({
        role: m.role as "user" | "assistant",
        content: m.content,
        citations: m.citations,
      })),
    );
  }

  async function newChat() {
    const c = await api.createConversation();
    await refreshConvos();
    setActiveId(c.id);
    setMessages([]);
  }

  async function send() {
    if (!input.trim() || busy) return;
    let convId = activeId;
    if (!convId) {
      const c = await api.createConversation();
      convId = c.id;
      setActiveId(c.id);
      await refreshConvos();
    }
    const q = input.trim();
    setInput("");
    setBusy(true);
    setMessages((m) => [
      ...m,
      { role: "user", content: q, citations: [] },
      { role: "assistant", content: "", citations: [], streaming: true },
    ]);

    await streamMessage(convId, q, {
      onStep: (d) => setStep(String(d.intent ?? d.agent ?? "")),
      onToken: (t) =>
        setMessages((m) => {
          const copy = [...m];
          copy[copy.length - 1] = {
            ...copy[copy.length - 1],
            content: copy[copy.length - 1].content + t,
          };
          return copy;
        }),
      onCitation: (c) =>
        setMessages((m) => {
          const copy = [...m];
          const last = copy[copy.length - 1];
          copy[copy.length - 1] = { ...last, citations: [...last.citations, c] };
          return copy;
        }),
      onRoadmap: (r) =>
        setMessages((m) => {
          const copy = [...m];
          copy[copy.length - 1] = { ...copy[copy.length - 1], roadmap: r };
          return copy;
        }),
      onDone: () => {
        setMessages((m) => {
          const copy = [...m];
          copy[copy.length - 1] = { ...copy[copy.length - 1], streaming: false };
          return copy;
        });
        setStep(null);
        setBusy(false);
      },
      onError: (e) => {
        setMessages((m) => {
          const copy = [...m];
          copy[copy.length - 1] = {
            ...copy[copy.length - 1],
            content: `⚠ ${e}`,
            streaming: false,
          };
          return copy;
        });
        setBusy(false);
      },
    });
  }

  return (
    <main className="flex h-screen">
      <aside className="flex w-64 flex-col border-r border-gray-200 p-3">
        <div className="mb-3 flex items-center justify-between">
          <Link href="/dashboard" className="text-sm text-gray-500 underline">
            ← Dashboard
          </Link>
        </div>
        <button
          onClick={newChat}
          className="mb-3 rounded-md bg-black py-2 text-sm font-medium text-white"
        >
          + New chat
        </button>
        <div className="flex-1 space-y-1 overflow-y-auto">
          {convos.map((c) => (
            <button
              key={c.id}
              onClick={() => openConversation(c.id)}
              className={`block w-full truncate rounded-md px-3 py-2 text-left text-sm ${
                c.id === activeId ? "bg-gray-100 font-medium" : "hover:bg-gray-50"
              }`}
            >
              {c.title}
            </button>
          ))}
        </div>
      </aside>

      <section className="flex flex-1 flex-col">
        <div className="flex-1 space-y-4 overflow-y-auto p-6">
          {messages.length === 0 && (
            <p className="mt-20 text-center text-gray-400">
              Ask your AI career mentor anything. Try: “I know Python. How do I become an ML
              Engineer?”
            </p>
          )}
          {messages.map((m, i) => (
            <div key={i} className={m.role === "user" ? "flex justify-end" : ""}>
              <div
                className={`max-w-2xl whitespace-pre-wrap rounded-xl px-4 py-3 text-sm ${
                  m.role === "user"
                    ? "bg-black text-white"
                    : "border border-gray-200 bg-white text-gray-800"
                }`}
              >
                {m.content || (m.streaming ? "…" : "")}
                {m.roadmap && (
                  <div className="mt-3 rounded-lg border border-gray-200 bg-gray-50 p-3 text-xs">
                    <div className="mb-2 font-semibold text-gray-700">
                      📍 Roadmap → {m.roadmap.role} · ~{m.roadmap.total_hours}h total
                    </div>
                    <ol className="space-y-1">
                      {m.roadmap.items.map((it, k) => (
                        <li key={k} className="flex items-start gap-2">
                          <span className="mt-0.5 rounded bg-gray-200 px-1.5 text-[10px] font-medium">
                            M{it.milestone}
                          </span>
                          <span>
                            <span className="font-medium">{it.skill}</span>{" "}
                            <span className="text-gray-400">
                              ~{it.est_hours}h · importance {it.importance}
                            </span>
                          </span>
                        </li>
                      ))}
                    </ol>
                  </div>
                )}
                {m.citations.length > 0 && (
                  <div className="mt-3 border-t border-gray-100 pt-2 text-xs text-gray-500">
                    <div className="mb-1 font-medium">Sources</div>
                    {m.citations.map((c, j) => (
                      <div key={j}>
                        [{j + 1}] {c.title}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          ))}
          {step && <p className="text-xs text-gray-400">· {step} …</p>}
          <div ref={endRef} />
        </div>

        <div className="border-t border-gray-200 p-4">
          <div className="mx-auto flex max-w-2xl gap-2">
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && send()}
              placeholder="Message your mentor…"
              disabled={busy}
              className="flex-1 rounded-md border border-gray-300 px-3 py-2 text-sm"
            />
            <button
              onClick={send}
              disabled={busy}
              className="rounded-md bg-black px-5 py-2 text-sm font-medium text-white disabled:opacity-50"
            >
              Send
            </button>
          </div>
        </div>
      </section>
    </main>
  );
}
