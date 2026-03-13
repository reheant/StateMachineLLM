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
  const [strategy, setStrategy] = useState<
    "single_prompt" | "two_shot_prompt" | "mermaid_compiler" | "automatic_grader"
  >("single_prompt");
  const [model, setModel] = useState("anthropic:claude-4-5-sonnet");
  const [inputTab, setInputTab] = useState<"example" | "custom">("example");
  const [exampleKey, setExampleKey] = useState("");
  const [gradingExampleKey, setGradingExampleKey] = useState("");
  const [description, setDescription] = useState("");
  const [systemName, setSystemName] = useState("");
  const [examples, setExamples] = useState<Example[]>([]);
  const [generating, setGenerating] = useState(false);
  const [logs, setLogs] = useState<string[]>([]);
  const [enableAutoGrading, setEnableAutoGrading] = useState(false);

  // Mermaid sandbox state
  const [mermaidCode, setMermaidCode] = useState("");
  const [mermaidSystemName, setMermaidSystemName] = useState("");
  const [renderingMermaid, setRenderingMermaid] = useState(false);
  const [gradingMermaid, setGradingMermaid] = useState(false);
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
    if (ex.description) {
      setDescription(ex.description);
      return;
    }
    setDescription("Loading…");
    try {
      const desc = await fetchDescription(key);
      setDescription(desc);
    } catch {
      setDescription(ex.blurb);
    }
  }

  function handleInputTabChange(tab: "example" | "custom") {
    setInputTab(tab);
    setExampleKey("");
    setGradingExampleKey("");
    setDescription("");
    setSystemName("");
    setMermaidError(null);
  }

  function handleStrategyChange(next: "single_prompt" | "two_shot_prompt" | "mermaid_compiler" | "automatic_grader") {
    setStrategy(next);
    setMermaidError(null);
    if (next !== "automatic_grader") {
      setGradingExampleKey("");
    }
    if (next === "mermaid_compiler" || next === "automatic_grader") {
      setInputTab("example");
    }
  }

  async function handleGenerate() {
    const desc = description.trim();
    const name = systemName.trim();
    if (!desc || !name) return;

    setGenerating(true);
    setLogs([]);

    const isManualCustomInput = inputTab === "custom";
    const shouldEnableAutoGrading = !isManualCustomInput && enableAutoGrading;

    const res = await fetch("/api/generate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        strategy,
        model,
        system_name: name,
        description: desc,
        enable_auto_grading: shouldEnableAutoGrading,
        input_mode: inputTab,
      }),
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
        setMermaidError(
          (err.detail ?? "Rendering failed.") +
            " Ensure valid Mermaid state diagram syntax (stateDiagram-v2)."
        );
        return;
      }
      const payload = await res.json();
      onHistoryRefresh();
      const run: Run = {
        strategy: "mermaid_compiler",
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

  async function handleAutomaticGrade() {
    const code = mermaidCode.trim();
    if (!code || !gradingExampleKey) return;

    setGradingMermaid(true);
    setMermaidError(null);

    const recoverFromHistory = async (): Promise<Run | null> => {
      try {
        const historyRes = await fetch("/api/history", { cache: "no-store" });
        if (!historyRes.ok) return null;

        const runs = (await historyRes.json()) as Run[];
        const recovered = runs.find(
          (r) =>
            r.strategy === "automatic_grader" &&
            r.folder.includes(`/${gradingExampleKey}/`)
        );

        return recovered ?? null;
      } catch {
        return null;
      }
    };

    try {
      const res = await fetch("/api/automatic-grade", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ mermaid_code: code, example_key: gradingExampleKey, model }),
      });
      if (!res.ok) {
        const recoveredRun = await recoverFromHistory();
        if (recoveredRun) {
          onHistoryRefresh();
          onComplete(recoveredRun);
          return;
        }

        const err = await res.json().catch(() => ({ detail: "Automatic grading failed." }));
        setMermaidError(err.detail ?? "Automatic grading failed.");
        return;
      }

      const payload = await res.json();
      const selectedExample = examples.find((e) => e.key === gradingExampleKey);
      onHistoryRefresh();
      const run: Run = {
        strategy: "automatic_grader",
        model,
        system: selectedExample?.label ?? gradingExampleKey,
        folder: payload.folder,
        date: new Date().toISOString().slice(0, 10),
        time: new Date().toTimeString().slice(0, 8),
        has_png: false,
      };
      onComplete(run);
    } catch {
      const recoveredRun = await recoverFromHistory();
      if (recoveredRun) {
        onHistoryRefresh();
        onComplete(recoveredRun);
        return;
      }
      setMermaidError("Network error while grading. If artifacts were created, open the latest automatic grader run in History.");
    } finally {
      setGradingMermaid(false);
    }
  }

  const canGenerate =
    !generating &&
    (strategy === "single_prompt" || strategy === "two_shot_prompt") &&
    description.trim().length > 0 &&
    systemName.trim().length > 0;
  const canRender = !renderingMermaid && mermaidCode.trim().length > 0;
  const canAutoGrade =
    !gradingMermaid && mermaidCode.trim().length > 0 && gradingExampleKey.trim().length > 0;
  const isPromptStrategy = strategy === "single_prompt" || strategy === "two_shot_prompt";
  const autoGradingForcedOff = isPromptStrategy && inputTab === "custom";

  return (
    <div className="flex flex-col bg-background">

      <div className="flex flex-col px-6 py-10">
      <div className="mx-auto w-full max-w-5xl flex flex-col gap-10">
        <div className="flex flex-col items-center gap-1.5 text-center">
          <h1 className="text-5xl font-black tracking-tight bg-gradient-to-br from-orange-300 via-orange-400 to-orange-600 bg-clip-text text-transparent">Tracer</h1>
          <p className="text-sm text-white/30">Generate a state machine diagram from any system description.</p>
        </div>

        {/* Step 1 — Strategy */}
        <div className="flex flex-col gap-4">
          <div className="flex items-center gap-2.5">
            <StepNumber n={1} />
            <span className="text-xs font-semibold uppercase tracking-widest text-white/30">Strategy</span>
          </div>
          <div className="grid grid-cols-2 gap-3">
            {([
              "single_prompt",
              "two_shot_prompt",
              "mermaid_compiler",
              "automatic_grader",
            ] as const).map((s) => (
              <button
                key={s}
                onClick={() => handleStrategyChange(s)}
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
                  {s === "single_prompt"
                    ? "Single Prompt"
                    : s === "two_shot_prompt"
                    ? "Two-Shot"
                    : s === "mermaid_compiler"
                    ? "Mermaid Compiler"
                    : "Automatic Grader"}
                </span>
                <span className={cn(
                  "text-[11px]",
                  strategy === s ? "text-orange-400/60" : "text-white/25"
                )}>
                  {s === "single_prompt"
                    ? "One-shot generation"
                    : s === "two_shot_prompt"
                    ? "Draft, then refine"
                    : s === "mermaid_compiler"
                    ? "Compile Mermaid directly"
                    : "Score against a selected example"}
                </span>
              </button>
            ))}
          </div>
        </div>

        {/* Step 2 — Parameters */}
        <div className="flex flex-col gap-5">
          <div className="flex items-center gap-2.5">
            <StepNumber n={2} />
            <span className="text-xs font-semibold uppercase tracking-widest text-white/30">Parameters</span>
          </div>

          {(strategy === "single_prompt" || strategy === "two_shot_prompt" || strategy === "automatic_grader") && (
            <div className="flex items-center gap-2">
              <Select value={model} onValueChange={(v) => v && setModel(v)}>
                <SelectTrigger className="h-11 w-full rounded-2xl border-white/[0.08] bg-white/[0.03] text-sm text-white/70 focus:ring-orange-500/20">
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
          )}

          {isPromptStrategy && (
            <>
              <div className="flex flex-1 overflow-hidden rounded-2xl border border-white/[0.07] bg-white/[0.03] p-1">
                {(["example", "custom"] as const).map((tab) => (
                  <button
                    key={tab}
                    onClick={() => handleInputTabChange(tab)}
                    className={cn(
                      "flex-1 rounded-xl px-3 py-1.5 text-sm font-medium transition-all",
                      inputTab === tab
                        ? "bg-white/[0.08] text-white/80"
                        : "text-white/30 hover:text-white/55"
                    )}
                  >
                    {tab === "example" ? "Example" : "Custom"}
                  </button>
                ))}
              </div>

              <div className="flex items-center justify-between rounded-xl border border-white/[0.08] bg-white/[0.03] px-4 py-3">
                <div className="flex flex-col">
                  <span className="text-sm font-semibold text-white/70">Automatic grading</span>
                  <span className="text-xs text-white/30">
                    {autoGradingForcedOff
                      ? "Disabled for manual custom descriptions"
                      : "Run grading prompt and LLM evaluation after generation"}
                  </span>
                </div>
                <button
                  type="button"
                  role="switch"
                  aria-checked={enableAutoGrading && !autoGradingForcedOff}
                  aria-disabled={autoGradingForcedOff}
                  disabled={autoGradingForcedOff}
                  onClick={() => setEnableAutoGrading((prev) => !prev)}
                  className={cn(
                    "relative h-7 w-12 rounded-full border transition-all duration-200",
                    enableAutoGrading && !autoGradingForcedOff
                      ? "border-orange-400/40 bg-orange-500/80"
                      : "border-white/[0.15] bg-white/[0.08]",
                    autoGradingForcedOff && "cursor-not-allowed opacity-60"
                  )}
                >
                  <span
                    className={cn(
                      "absolute top-1 h-5 w-5 rounded-full bg-white shadow-md transition-all duration-200",
                      enableAutoGrading && !autoGradingForcedOff ? "left-6" : "left-0.5"
                    )}
                  />
                </button>
              </div>

              <div className="flex flex-col gap-3">
                {inputTab === "example" && (
                  <div className="flex flex-col gap-3">
                    {examples.length > 0 && (
                      <div className="grid grid-cols-3 gap-2">
                        {examples.map((ex) => (
                          <button
                            key={ex.key}
                            onClick={() => handleExampleChange(ex.key)}
                            className={cn(
                              "flex items-center gap-2.5 rounded-2xl border px-4 py-3 text-left transition-all duration-150",
                              exampleKey === ex.key
                                ? "border-orange-400/30 bg-orange-400/10 ring-1 ring-orange-400/20"
                                : "border-white/[0.07] bg-white/[0.03] hover:border-white/[0.12] hover:bg-white/[0.05]"
                            )}
                          >
                            <span className="text-lg leading-none">{ex.icon}</span>
                            <span className="flex flex-col">
                              <span className={cn(
                                "text-[13px] font-semibold leading-snug",
                                exampleKey === ex.key ? "text-orange-200" : "text-white/55"
                              )}>
                                {ex.label}
                              </span>
                              <span className="text-[11px] text-white/35 line-clamp-2">
                                {ex.blurb}
                              </span>
                            </span>
                          </button>
                        ))}
                      </div>
                    )}
                    <Textarea
                      placeholder={
                        !exampleKey
                          ? "Select an example above to auto-fill…"
                          : "Describe the system behaviour in detail…"
                      }
                      value={description}
                      onChange={(e) => setDescription(e.target.value)}
                      className="min-h-[6rem] max-h-[22rem] resize-none overflow-y-auto rounded-xl border-white/[0.08] bg-white/[0.03] font-sans text-sm text-white/70 leading-relaxed placeholder:text-white/20 focus:border-orange-500/30 focus:ring-orange-500/10"
                    />
                  </div>
                )}

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
              </div>
            </>
          )}

          {strategy === "mermaid_compiler" && (
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
            </div>
          )}

          {strategy === "automatic_grader" && (
            <div className="flex flex-col gap-3">
              <p className="text-xs text-white/35">
                Select one of {examples.length} available state machine descriptions as grading reference.
              </p>
              <div className="grid grid-cols-3 gap-2">
                {examples.map((ex) => (
                  <button
                    key={ex.key}
                    onClick={() => setGradingExampleKey(ex.key)}
                    className={cn(
                      "flex items-center gap-2.5 rounded-2xl border px-4 py-3 text-left transition-all duration-150",
                      gradingExampleKey === ex.key
                        ? "border-orange-400/30 bg-orange-400/10 ring-1 ring-orange-400/20"
                        : "border-white/[0.07] bg-white/[0.03] hover:border-white/[0.12] hover:bg-white/[0.05]"
                    )}
                  >
                    <span className="text-lg leading-none">{ex.icon}</span>
                    <span className="flex flex-col">
                      <span className={cn(
                        "text-[13px] font-semibold leading-snug",
                        gradingExampleKey === ex.key ? "text-orange-200" : "text-white/55"
                      )}>
                        {ex.label}
                      </span>
                      <span className="text-[11px] text-white/35 line-clamp-2">
                        {ex.blurb}
                      </span>
                    </span>
                  </button>
                ))}
              </div>
              <Textarea
                placeholder={"Paste Mermaid code to grade against the selected example..."}
                value={mermaidCode}
                onChange={(e) => setMermaidCode(e.target.value)}
                className="min-h-48 resize-none rounded-xl border-white/[0.08] bg-white/[0.03] font-mono text-sm text-white/70 leading-relaxed placeholder:text-white/20 focus:border-orange-500/30 focus:ring-orange-500/10"
              />
            </div>
          )}

          {mermaidError && (
            <p className="rounded-lg border border-red-500/20 bg-red-500/10 px-4 py-2.5 text-xs text-red-400">
              {mermaidError}
            </p>
          )}
        </div>{/* end Parameters */}

        {isPromptStrategy && (
          <button
            onClick={handleGenerate}
            disabled={!canGenerate}
            className={cn(
              "group relative flex w-full items-center justify-center gap-2.5 overflow-hidden rounded-xl py-3.5 text-sm font-semibold transition-all duration-200",
              canGenerate
                ? "bg-orange-500/90 text-white shadow-lg shadow-orange-500/20 hover:bg-orange-400/90 active:scale-[0.99]"
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

        {strategy === "mermaid_compiler" && (
          <button
            onClick={handleRenderMermaid}
            disabled={!canRender}
            className={cn(
              "group relative flex w-full items-center justify-center gap-2.5 overflow-hidden rounded-xl py-3.5 text-sm font-semibold transition-all duration-200",
              canRender
                ? "bg-orange-500/90 text-white shadow-lg shadow-orange-500/20 hover:bg-orange-400/90 active:scale-[0.99]"
                : "cursor-not-allowed bg-white/[0.04] text-white/20"
            )}
          >
            {renderingMermaid ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Zap className="h-4 w-4 transition-transform group-hover:scale-110" />
            )}
            {renderingMermaid ? "Compiling…" : "Compile Mermaid"}
          </button>
        )}

        {strategy === "automatic_grader" && (
          <button
            onClick={handleAutomaticGrade}
            disabled={!canAutoGrade}
            className={cn(
              "group relative flex w-full items-center justify-center gap-2.5 overflow-hidden rounded-xl py-3.5 text-sm font-semibold transition-all duration-200",
              canAutoGrade
                ? "bg-orange-500/90 text-white shadow-lg shadow-orange-500/20 hover:bg-orange-400/90 active:scale-[0.99]"
                : "cursor-not-allowed bg-white/[0.04] text-white/20"
            )}
          >
            {gradingMermaid ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Zap className="h-4 w-4 transition-transform group-hover:scale-110" />
            )}
            {gradingMermaid ? "Grading…" : "Run Automatic Grader"}
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
