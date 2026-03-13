"use client";

import { useEffect, useRef, useState } from "react";
import { fetchExamples, fetchDescription } from "@/lib/api";
import type { Example, Run } from "@/lib/types";
import { Textarea } from "@/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectLabel,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Loader2, Zap } from "lucide-react";
import { cn } from "@/lib/utils";

const MODELS: Record<string, { label: string; value: string }[]> = {
  Anthropic: [
    { label: "Claude 4.5 Sonnet", value: "anthropic:claude-4-5-sonnet" },
    { label: "Claude 3.5 Sonnet", value: "anthropic:claude-3-5-sonnet-20241022" },
    { label: "Claude Sonnet 4", value: "anthropic:claude-sonnet-4" },
  ],
  OpenAI: [
    { label: "GPT-4o", value: "openai:gpt-4o" },
    { label: "GPT-4o Mini", value: "openai:gpt-4o-mini" },
    { label: "GPT-4 Turbo", value: "openai:gpt-4-turbo" },
    { label: "o1", value: "openai:o1" },
    { label: "o1 Mini", value: "openai:o1-mini" },
  ],
  Google: [
    { label: "Gemini 2.0 Flash Exp", value: "google:gemini-2-0-flash-exp" },
    { label: "Gemini 1.5 Pro", value: "google:gemini-1-5-pro-001" },
    { label: "Gemini 1.5 Flash", value: "google:gemini-1-5-flash" },
  ],
  Meta: [
    { label: "Llama 3.3 70B", value: "meta:llama-3-3-70b-instruct" },
    { label: "Llama 3.1 405B", value: "meta:llama-3-1-405b-instruct" },
    { label: "Llama 3.1 70B", value: "meta:llama-3-1-70b-instruct" },
    { label: "Llama 3.2 3B", value: "meta:llama-3-2-3b-instruct" },
  ],
  Qwen: [
    { label: "QwQ 32B", value: "qwen:qwq-32b" },
    { label: "Qwen 2.5 72B", value: "qwen:qwen-2-5-72b-instruct" },
  ],
};

// Flat label map for SelectValue display
const MODEL_LABELS: Record<string, string> = Object.values(MODELS)
  .flat()
  .reduce((acc, m) => ({ ...acc, [m.value]: m.label }), {});

interface Props {
  onComplete: (run: Run) => void;
  onHistoryRefresh: () => void;
}

function StepNumber({ n }: { n: number }) {
  return (
    <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-orange-400/20 text-[11px] font-bold text-orange-300 ring-1 ring-orange-400/30">
      {n}
    </span>
  );
}

export function RunForm({ onComplete, onHistoryRefresh }: Props) {
  const [strategy, setStrategy] = useState<"single_prompt" | "two_shot_prompt">("single_prompt");
  const [model, setModel] = useState("anthropic:claude-4-5-sonnet");
  const [inputTab, setInputTab] = useState<"example" | "custom" | "mermaid">("example");
  const [exampleKey, setExampleKey] = useState("");
  const [description, setDescription] = useState("");
  const [systemName, setSystemName] = useState("");
  const [examples, setExamples] = useState<Example[]>([]);
  const [generating, setGenerating] = useState(false);
  const [logs, setLogs] = useState<string[]>([]);

  // Mermaid sandbox state
  const [mermaidCode, setMermaidCode] = useState("");
  const [mermaidSystemName, setMermaidSystemName] = useState("");
  const [renderingMermaid, setRenderingMermaid] = useState(false);
  const [mermaidError, setMermaidError] = useState<string | null>(null);

  const logsEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    fetchExamples().then(setExamples).catch(console.error);
  }, []);

  useEffect(() => {
    logsEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [logs]);

  async function handleExampleChange(key: string) {
    setExampleKey(key);
    const ex = examples.find((e) => e.key === key);
    if (!ex) return;
    setSystemName(ex.label);
    setDescription("Loading…");
    try {
      const desc = await fetchDescription(key);
      setDescription(desc);
    } catch {
      setDescription(ex.blurb);
    }
  }

  function handleInputTabChange(tab: "example" | "custom" | "mermaid") {
    setInputTab(tab);
    setExampleKey("");
    setDescription("");
    setSystemName("");
    setMermaidError(null);
  }

  async function handleGenerate() {
    const desc = description.trim();
    const name = systemName.trim();
    if (!desc || !name) return;

    setGenerating(true);
    setLogs([]);

    const res = await fetch("/api/generate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ strategy, model, system_name: name, description: desc }),
    });

    if (!res.ok || !res.body) {
      setLogs((l) => [...l, "Error: failed to start generation."]);
      setGenerating(false);
      return;
    }

    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const parts = buffer.split("\n\n");
      buffer = parts.pop() ?? "";

      for (const chunk of parts) {
        const lines = chunk.split("\n");
        let eventType = "message";
        let data = "";
        for (const line of lines) {
          if (line.startsWith("event: ")) eventType = line.slice(7);
          else if (line.startsWith("data: ")) data = line.slice(6);
        }

        if (eventType === "progress") {
          setLogs((l) => [...l, data]);
        } else if (eventType === "complete") {
          const payload = JSON.parse(data);
          onHistoryRefresh();
          const run: Run = {
            strategy, model,
            system: name,
            folder: payload.folder,
            date: new Date().toISOString().slice(0, 10),
            time: new Date().toTimeString().slice(0, 8),
            has_png: true,
          };
          setGenerating(false);
          onComplete(run);
          return;
        } else if (eventType === "error") {
          setLogs((l) => [...l, `Error: ${data}`]);
          setGenerating(false);
          return;
        }
      }
    }

    setGenerating(false);
  }

  async function handleRenderMermaid() {
    const code = mermaidCode.trim();
    const name = mermaidSystemName.trim() || "CustomMermaid";
    if (!code) return;

    setRenderingMermaid(true);
    setMermaidError(null);

    try {
      const res = await fetch("/api/render-mermaid", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ mermaid_code: code, system_name: name }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: "Rendering failed." }));
        setMermaidError(err.detail ?? "Rendering failed.");
        return;
      }
      const payload = await res.json();
      onHistoryRefresh();
      const run: Run = {
        strategy: "single_prompt",
        model: "custom-input",
        system: name,
        folder: payload.folder,
        date: new Date().toISOString().slice(0, 10),
        time: new Date().toTimeString().slice(0, 8),
        has_png: true,
      };
      onComplete(run);
    } catch {
      setMermaidError("Network error — is the server running?");
    } finally {
      setRenderingMermaid(false);
    }
  }

  const canGenerate =
    !generating && description.trim().length > 0 && systemName.trim().length > 0;
  const canRender = !renderingMermaid && mermaidCode.trim().length > 0;

  return (
    <div className="flex flex-col bg-background">

      {/* Hero header */}
      <div className="relative overflow-hidden border-b border-white/[0.06] px-10 py-10">
        {/* Glow orbs */}
        <div className="pointer-events-none absolute -top-16 -left-8 h-56 w-56 rounded-full bg-orange-500/10 blur-3xl" />
        <div className="pointer-events-none absolute -bottom-8 right-1/3 h-32 w-48 rounded-full bg-orange-500/8 blur-2xl" />
        <div className="flex flex-col items-center text-center gap-4">
          {/* Large hero logo */}
          <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-gradient-to-br from-orange-400 via-orange-500 to-orange-600 shadow-2xl shadow-orange-500/30">
            <svg viewBox="0 0 32 32" fill="none" className="h-8 w-8" aria-hidden="true">
              <path d="M22 4L28 10L11 27H5V21L22 4Z" stroke="white" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" fill="white" fillOpacity="0.15" />
              <path d="M18 8L24 14" stroke="white" strokeWidth="2.5" strokeLinecap="round" />
            </svg>
          </div>
          <div>
            <p className="text-[11px] font-bold uppercase tracking-[0.18em] text-orange-400/70">
              Tracer · New Run
            </p>
            <h1 className="mt-1 text-3xl font-bold tracking-tight text-white">
              Generate a diagram
            </h1>
            <p className="mt-1.5 text-sm text-white/45">
              Describe any system — Tracer traces its states for you.
            </p>
          </div>
        </div>
      </div>

      <div className="flex flex-col px-6 py-10">
      <div className="mx-auto w-full max-w-2xl flex flex-col gap-10">

        {/* Step 1 — Strategy */}
        <div className="flex flex-col gap-4">
          <div className="flex items-center gap-2.5">
            <StepNumber n={1} />
            <span className="text-xs font-semibold uppercase tracking-widest text-white/30">Strategy</span>
          </div>
          <div className="flex gap-3">
            {(["single_prompt", "two_shot_prompt"] as const).map((s) => (
              <button
                key={s}
                onClick={() => setStrategy(s)}
                className={cn(
                  "flex flex-1 flex-col gap-1 rounded-xl border px-5 py-4 text-left transition-all duration-150",
                  strategy === s
                    ? "border-orange-400/40 bg-orange-400/12 ring-1 ring-orange-400/30"
                    : "border-white/[0.07] bg-white/[0.02] hover:border-white/[0.12] hover:bg-white/[0.04]"
                )}
              >
                <span className={cn(
                  "text-sm font-semibold",
                  strategy === s ? "text-orange-200" : "text-white/50"
                )}>
                  {s === "single_prompt" ? "Single Prompt" : "Two-Shot"}
                </span>
                <span className={cn(
                  "text-[11px]",
                  strategy === s ? "text-orange-400/60" : "text-white/25"
                )}>
                  {s === "single_prompt" ? "One-shot generation" : "Draft, then refine"}
                </span>
              </button>
            ))}
          </div>
        </div>

        {/* Step 2 — Model */}
        <div className="flex flex-col gap-4">
          <div className="flex items-center gap-2.5">
            <StepNumber n={2} />
            <span className="text-xs font-semibold uppercase tracking-widest text-white/30">Model</span>
          </div>
          <Select value={model} onValueChange={(v) => v && setModel(v)}>
            <SelectTrigger className="h-11 rounded-xl border-white/[0.08] bg-white/[0.03] text-sm text-white/70 focus:ring-orange-500/20">
              <SelectValue>{MODEL_LABELS[model] ?? model}</SelectValue>
            </SelectTrigger>
            <SelectContent className="border-white/10 bg-[oklch(0.30_0.035_258)] text-white/80">
              {Object.entries(MODELS).map(([group, options]) => (
                <SelectGroup key={group}>
                  <SelectLabel className="text-white/30">{group}</SelectLabel>
                  {options.map((opt) => (
                    <SelectItem key={opt.value} value={opt.value} className="focus:bg-white/10 focus:text-white">
                      {opt.label}
                    </SelectItem>
                  ))}
                </SelectGroup>
              ))}
            </SelectContent>
          </Select>
        </div>

        {/* Step 3 — Input */}
        <div className="flex flex-col gap-4">
          <div className="flex items-center gap-2.5">
            <StepNumber n={3} />
            <span className="text-xs font-semibold uppercase tracking-widest text-white/30">Input</span>
          </div>

          {/* Tab bar */}
          <div className="flex overflow-hidden rounded-lg border border-white/[0.07] bg-white/[0.03] p-0.5">
            {(["example", "custom", "mermaid"] as const).map((tab) => (
              <button
                key={tab}
                onClick={() => handleInputTabChange(tab)}
                className={cn(
                  "flex-1 rounded-md px-3 py-1.5 text-xs font-medium transition-all",
                  inputTab === tab
                    ? "bg-white/[0.08] text-white/80"
                    : "text-white/25 hover:text-white/50"
                )}
              >
                {tab === "example" ? "Example" : tab === "custom" ? "Custom" : "Mermaid"}
              </button>
            ))}
          </div>

          {/* Example tab */}
          {inputTab === "example" && (
            <div className="flex flex-col gap-3">
              <Select value={exampleKey} onValueChange={(v) => v && handleExampleChange(v)}>
                <SelectTrigger className="h-11 rounded-xl border-white/[0.08] bg-white/[0.03] text-sm text-white/60 focus:ring-orange-500/20">
                  <SelectValue placeholder="Choose an example system…">
                    {exampleKey
                      ? (() => {
                          const ex = examples.find((e) => e.key === exampleKey);
                          return ex ? `${ex.icon} ${ex.label}` : exampleKey;
                        })()
                      : undefined}
                  </SelectValue>
                </SelectTrigger>
                <SelectContent className="border-white/10 bg-[oklch(0.30_0.035_258)] text-white/80">
                  {examples.map((ex) => (
                    <SelectItem key={ex.key} value={ex.key} className="focus:bg-white/10 focus:text-white">
                      {ex.icon} {ex.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <Textarea
                placeholder={
                  !exampleKey
                    ? "Select an example to auto-fill…"
                    : "Describe the system behaviour in detail…"
                }
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                className="min-h-48 resize-none rounded-xl border-white/[0.08] bg-white/[0.03] font-sans text-sm text-white/70 leading-relaxed placeholder:text-white/20 focus:border-orange-500/30 focus:ring-orange-500/10"
              />
            </div>
          )}

          {/* Custom tab */}
          {inputTab === "custom" && (
            <div className="flex flex-col gap-3">
              <input
                type="text"
                placeholder="System name (e.g. Dishwasher)"
                value={systemName}
                onChange={(e) => setSystemName(e.target.value)}
                className="h-11 rounded-xl border border-white/[0.08] bg-white/[0.03] px-4 text-sm text-white/80 placeholder:text-white/20 focus:border-orange-500/30 focus:outline-none focus:ring-2 focus:ring-orange-500/10"
              />
              <Textarea
                placeholder="Describe the system behaviour in detail…"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                className="min-h-48 resize-none rounded-xl border-white/[0.08] bg-white/[0.03] font-sans text-sm text-white/70 leading-relaxed placeholder:text-white/20 focus:border-orange-500/30 focus:ring-orange-500/10"
              />
            </div>
          )}

          {/* Mermaid sandbox tab */}
          {inputTab === "mermaid" && (
            <div className="flex flex-col gap-3">
              <input
                type="text"
                placeholder="System name (e.g. MyMachine)"
                value={mermaidSystemName}
                onChange={(e) => setMermaidSystemName(e.target.value)}
                className="h-11 rounded-xl border border-white/[0.08] bg-white/[0.03] px-4 text-sm text-white/80 placeholder:text-white/20 focus:border-orange-500/30 focus:outline-none focus:ring-2 focus:ring-orange-500/10"
              />
              <Textarea
                placeholder={"stateDiagram-v2\n  [*] --> Idle\n  Idle --> Running : start\n  Running --> [*] : stop"}
                value={mermaidCode}
                onChange={(e) => setMermaidCode(e.target.value)}
                className="min-h-48 resize-none rounded-xl border-white/[0.08] bg-white/[0.03] font-mono text-sm text-white/70 leading-relaxed placeholder:text-white/20 focus:border-orange-500/30 focus:ring-orange-500/10"
              />
              {mermaidError && (
                <p className="rounded-lg border border-red-500/20 bg-red-500/10 px-4 py-2.5 text-xs text-red-400">
                  {mermaidError}
                </p>
              )}
              <button
                onClick={handleRenderMermaid}
                disabled={!canRender}
                className={cn(
                  "group relative flex w-full items-center justify-center gap-2.5 overflow-hidden rounded-xl py-3.5 text-sm font-semibold transition-all duration-200",
                  canRender
                    ? "bg-gradient-to-r from-orange-400 to-yellow-300 text-[oklch(0.118_0.004_285)] shadow-lg shadow-orange-400/40 hover:shadow-orange-300/50 hover:from-orange-300 hover:to-yellow-200 active:scale-[0.99]"
                    : "cursor-not-allowed bg-white/[0.04] text-white/20"
                )}
              >
                {renderingMermaid ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Zap className="h-4 w-4 transition-transform group-hover:scale-110" />
                )}
                {renderingMermaid ? "Rendering…" : "Render"}
              </button>
            </div>
          )}
        </div>

        {/* Generate button — only for Example/Custom tabs */}
        {inputTab !== "mermaid" && (
          <button
            onClick={handleGenerate}
            disabled={!canGenerate}
            className={cn(
              "group relative flex w-full items-center justify-center gap-2.5 overflow-hidden rounded-xl py-3.5 text-sm font-semibold transition-all duration-200",
              canGenerate
                ? "bg-gradient-to-r from-orange-400 to-yellow-300 text-[oklch(0.118_0.004_285)] shadow-lg shadow-orange-400/40 hover:shadow-orange-300/50 hover:from-orange-300 hover:to-yellow-200 active:scale-[0.99]"
                : "cursor-not-allowed bg-white/[0.04] text-white/20"
            )}
          >
            {generating ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Zap className="h-4 w-4 transition-transform group-hover:scale-110" />
            )}
            {generating ? "Generating…" : "Generate"}
          </button>
        )}

        {/* Live log */}
        {logs.length > 0 && (
          <div className="flex flex-col gap-2">
            <div className="flex items-center gap-2.5">
              <span className="text-xs font-medium text-white/30">Output</span>
              {generating && (
                <span className="flex items-center gap-1.5">
                  <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-orange-400" />
                  <span className="text-[10px] font-semibold text-orange-400">Live</span>
                </span>
              )}
            </div>
            <ScrollArea className="h-56 rounded-xl border border-white/[0.06] bg-black/30 p-4">
              <div className="flex flex-col gap-0.5">
                {logs.map((line, i) => (
                  <p key={i} className="font-mono text-[11px] leading-relaxed text-orange-300/60">
                    <span className="mr-2 text-white/10">›</span>
                    {line}
                  </p>
                ))}
                <div ref={logsEndRef} />
              </div>
            </ScrollArea>
          </div>
        )}
      </div>
      </div>
    </div>
  );
}
