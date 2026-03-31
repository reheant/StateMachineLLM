"use client";

import { useEffect, useRef, useState } from "react";
import { fetchArtifacts, fetchDescription, fetchExamples, fetchHistory, fileUrl } from "@/lib/api";
import type { Artifacts, Example, Run } from "@/lib/types";
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
import { AlertTriangle, Check, ChevronDown, Loader2, X, Zap } from "lucide-react";
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
  onGeneratingChange?: (v: boolean) => void;
}

type PromptStrategy = "single_prompt" | "two_shot_prompt";

type ProgressStep = {
  label: string;
  status: "pending" | "active" | "done";
};

type ToastState = { kind: "error" | "info"; message: string };

function hasGradingArtifacts(artifacts: Artifacts | null): boolean {
  return Boolean(
    artifacts?.grading_output || artifacts?.grading_csv || artifacts?.grading_tsv
  );
}

// Poll until grading finishes. Return TSV artifacts when ready or an error message if grading failed.
// Gives up after maxWaitMs (default 2 minutes) to avoid hanging the UI forever.
async function waitForGradingCompletion(
  folder: string,
  intervalMs = 1200,
  maxWaitMs = 2 * 60 * 1000
): Promise<{ artifacts: Artifacts | null; errorMessage: string | null }> {
  const deadline = Date.now() + maxWaitMs;
  while (Date.now() < deadline) {
    try {
      const artifacts = await fetchArtifacts(folder);

      // Use status.json as the authoritative signal when available.
      if (artifacts.status) {
        const s = artifacts.status;
        if (s.status === "success") return { artifacts, errorMessage: null };
        if (s.status === "failed" || s.status === "partial") {
          return {
            artifacts,
            errorMessage: s.error?.message ?? "Automatic grading failed.",
          };
        }
        // status is "in_progress" — keep polling.
      } else {
        // Fallback: legacy runs without status.json.
        if (artifacts.grading_tsv) return { artifacts, errorMessage: null };
        if (artifacts.grading_output) {
          try {
            const res = await fetch(fileUrl(artifacts.grading_output));
            const text = await res.text();
            return { artifacts, errorMessage: text || "Automatic grading failed." };
          } catch {
            return { artifacts, errorMessage: "Automatic grading failed." };
          }
        }
      }
    } catch {
      // Ignore transient fetch errors while grading finishes.
    }

    await new Promise((resolve) => setTimeout(resolve, intervalMs));
  }
  // Timed out — return the last known state.
  return { artifacts: null, errorMessage: "Automatic grading timed out. Check the run in History for results." };
}

function buildProgressSteps(
  strategy: PromptStrategy,
  logs: string[],
  artifacts: Artifacts | null,
  showAutoGradingStages: boolean
): ProgressStep[] {
  const logText = logs.join("\n").toLowerCase();
  const sawGradingStartedLog = /running automatic grading/.test(logText);
  const sawGradingEvaluatingLog = /evaluating generation against ground truth/.test(logText);
  const hasGradingPrompt = Boolean(artifacts?.grading_prompt);
  const gradingFinished =
    /automatic grading completed|automatic grading skipped|automatic grading failed/.test(
      logText
    ) ||
    Boolean(artifacts?.grading_output || artifacts?.grading_csv || artifacts?.grading_tsv);

  const buildGradingSteps = (generationComplete: boolean): ProgressStep[] => {
    if (!showAutoGradingStages) return [];

    // If grading logs are delayed, infer the active grading phase from artifacts
    // so the UI always has one active (orange) step while work is still running.
    const gradingStarted =
      sawGradingStartedLog || (generationComplete && !gradingFinished);
    const gradingEvaluating =
      sawGradingEvaluatingLog || (hasGradingPrompt && !gradingFinished);

    return [
      {
        label: "Running automatic grading",
        status: gradingStarted
          ? gradingEvaluating || gradingFinished
            ? "done"
            : "active"
          : "pending",
      },
      {
        label: "Evaluating generation against ground truth",
        status: gradingFinished
          ? "done"
          : gradingEvaluating
          ? "active"
          : "pending",
      },
    ];
  };

  if (strategy === "two_shot_prompt") {
    const shot1Started =
      /running shot 1|shot 1 raw llm response|shot 1: failed/.test(logText);
    const shot1Mermaid = Boolean(artifacts?.shot1_mmd);
    const shot1Image = Boolean(artifacts?.shot1_png);
    const shot2Started =
      /running shot 2|shot 2 raw llm response|shot 2: failed/.test(logText);
    const shot2Mermaid = Boolean(artifacts?.mmd || artifacts?.txt);
    const finalImage = Boolean(artifacts?.png);
    const gradingSteps = buildGradingSteps(finalImage);

    return [
      { label: "Shot 1 started", status: shot1Started ? "done" : "active" },
      { label: "Shot 1 Mermaid generated", status: shot1Mermaid ? "done" : shot1Started ? "active" : "pending" },
      { label: "Shot 1 image generated", status: shot1Image ? "done" : shot1Mermaid ? "active" : "pending" },
      { label: "Shot 2 started", status: shot2Started ? "done" : shot1Image ? "active" : "pending" },
      { label: "Shot 2 Mermaid generated", status: shot2Mermaid ? "done" : shot2Started ? "active" : "pending" },
      { label: "Image generated", status: finalImage ? "done" : shot2Mermaid ? "active" : "pending" },
      ...gradingSteps,
    ];
  }

  const mermaidGenerated = Boolean(artifacts?.mmd || artifacts?.txt);
  const imageGenerated = Boolean(artifacts?.png);
  const gradingSteps = buildGradingSteps(imageGenerated);

  return [
    { label: "Calling LLM", status: mermaidGenerated ? "done" : "active" },
    { label: "Mermaid generated", status: mermaidGenerated ? (imageGenerated ? "done" : "active") : "pending" },
    { label: "Image generated", status: imageGenerated ? "done" : mermaidGenerated ? "active" : "pending" },
    ...gradingSteps,
  ];
}

function GeneratingProgress({
  strategy,
  logs,
  artifacts,
  showAutoGradingStages,
  onCancel,
}: {
  strategy: PromptStrategy;
  logs: string[];
  artifacts: Artifacts | null;
  showAutoGradingStages: boolean;
  onCancel: () => void;
}) {
  const [showLogs, setShowLogs] = useState(false);
  const logsEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (showLogs) logsEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [logs, showLogs]);

  const steps = buildProgressSteps(
    strategy,
    logs,
    artifacts,
    showAutoGradingStages
  );

  return (
    <div className="overflow-hidden rounded-2xl border border-white/[0.10] bg-[oklch(0.19_0.04_258)] shadow-lg shadow-black/40">

      {/* Header */}
      <div className="flex items-center gap-2 border-b border-white/[0.06] px-4 py-3">
        <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-orange-400" />
        <span className="text-[10px] font-bold uppercase tracking-widest text-white/40">Generating</span>
      </div>

      {/* Steps — each clickable to toggle log terminal */}
      <div className="flex flex-col px-3 py-3">
        {steps.map((step, i) => {
          const done = step.status === "done";
          const active = step.status === "active";
          return (
            <button
              key={i}
              onClick={() => setShowLogs((v) => !v)}
              className={cn(
                "flex w-full items-center gap-3 rounded-xl px-2 py-2.5 text-left transition-colors",
                active ? "bg-orange-400/[0.07]" : "hover:bg-white/[0.03]"
              )}
            >
              <span className={cn(
                "flex h-5 w-5 shrink-0 items-center justify-center rounded-full transition-all duration-300",
                done  && "bg-orange-500/20",
                active && "ring-2 ring-orange-400/50 ring-offset-1 ring-offset-[oklch(0.19_0.04_258)] bg-orange-400/10",
                !done && !active && "border border-white/[0.10]"
              )}>
                {done ? (
                  <Check className="h-3 w-3 text-orange-400" />
                ) : active ? (
                  <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-orange-400" />
                ) : (
                  <span className="h-1.5 w-1.5 rounded-full bg-white/15" />
                )}
              </span>
              <span className={cn(
                "text-[13px] transition-colors duration-200",
                done  && "text-white/25 line-through decoration-white/15",
                active && "font-semibold text-white/80",
                !done && !active && "text-white/25"
              )}>
                {step.label}
              </span>
              {active && (
                <ChevronDown className={cn(
                  "ml-auto h-3.5 w-3.5 shrink-0 text-white/25 transition-transform duration-200",
                  showLogs && "rotate-180"
                )} />
              )}
            </button>
          );
        })}
      </div>

      {/* Terminal log pane */}
      {showLogs && (
        <div className="border-t border-white/[0.06]">
          <ScrollArea className="h-44 px-3 py-3">
            <div className="flex flex-col gap-0.5">
              {logs.length === 0 ? (
                <p className="font-mono text-[10px] text-white/20 italic">Waiting for output…</p>
              ) : (
                logs.map((line, i) => (
                  <p key={i} className="font-mono text-[10px] leading-relaxed text-orange-300/50 break-all">
                    <span className="mr-1.5 text-white/15">›</span>{line}
                  </p>
                ))
              )}
              <div ref={logsEndRef} />
            </div>
          </ScrollArea>
        </div>
      )}

      {/* Footer */}
      <div className="border-t border-white/[0.06] px-4 py-3">
        <button
          onClick={onCancel}
          className="w-full rounded-xl border border-white/[0.10] bg-white/[0.04] py-2 text-sm font-medium text-white/50 transition-all hover:border-white/[0.20] hover:bg-white/[0.07] hover:text-white/80"
        >
          Cancel
        </button>
      </div>
    </div>
  );
}

function StepNumber({ n }: { n: number }) {
  return (
    <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-orange-400/20 text-[11px] font-bold text-orange-300 ring-1 ring-orange-400/30">
      {n}
    </span>
  );
}

function normalizeToken(value: string): string {
  return value.toLowerCase().replace(/[^a-z0-9]/g, "");
}

function normalizeSystemName(value: string): string {
  return value.trim().replace(/[_\s]+/g, " ").toLowerCase();
}

function findCompletedRun(
  history: Run[],
  strategy: PromptStrategy,
  systemName: string,
  model: string,
  startedAt: number
): Run | null {
  const requestedModel = normalizeToken(model.split(":").pop() ?? model);
  const requestedSystem = normalizeSystemName(systemName);

  const strictMatches = history.filter((run) => {
    if (run.strategy !== strategy || !run.has_png) return false;
    if (normalizeSystemName(run.system) !== requestedSystem) return false;
    return normalizeToken(run.model) === requestedModel;
  });

  const fallbackMatches = strictMatches.length > 0
    ? strictMatches
    : history.filter(
        (run) =>
          run.strategy === strategy &&
          run.has_png &&
          normalizeSystemName(run.system) === requestedSystem
      );

  return (
    fallbackMatches.find((run) => {
      const completedAt = Date.parse(`${run.date}T${run.time}`);
      return Number.isNaN(completedAt) || completedAt >= startedAt - 60_000;
    }) ?? null
  );
}

function findMatchingRun(
  history: Run[],
  strategy: PromptStrategy,
  systemName: string,
  model: string,
  startedAt: number
): Run | null {
  const requestedModel = normalizeToken(model.split(":").pop() ?? model);
  const requestedSystem = normalizeSystemName(systemName);

  const strictMatches = history.filter((run) => {
    if (run.strategy !== strategy) return false;
    if (normalizeSystemName(run.system) !== requestedSystem) return false;
    return normalizeToken(run.model) === requestedModel;
  });

  const fallbackMatches = strictMatches.length > 0
    ? strictMatches
    : history.filter(
        (run) =>
          run.strategy === strategy &&
          normalizeSystemName(run.system) === requestedSystem
      );

  return (
    fallbackMatches.find((run) => {
      const completedAt = Date.parse(`${run.date}T${run.time}`);
      return Number.isNaN(completedAt) || completedAt >= startedAt - 60_000;
    }) ?? null
  );
}

export function RunForm({ onComplete, onHistoryRefresh, onGeneratingChange }: Props) {
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
  const [progressArtifacts, setProgressArtifacts] = useState<Artifacts | null>(null);
  const [showAutoGradingStages, setShowAutoGradingStages] = useState(false);
  const [toast, setToast] = useState<ToastState | null>(null);

  // Generation error state — persists after failure so the user can see what went wrong.
  const [generationError, setGenerationError] = useState<{
    message: string;
    logs: string[];
  } | null>(null);

  // Mermaid sandbox state
  const [mermaidCode, setMermaidCode] = useState("");
  const [mermaidSystemName, setMermaidSystemName] = useState("");
  const [renderingMermaid, setRenderingMermaid] = useState(false);
  const [gradingMermaid, setGradingMermaid] = useState(false);
  const [mermaidError, setMermaidError] = useState<string | null>(null);

  const abortRef = useRef<AbortController | null>(null);
  // Always hold latest callback refs so async handlers don't close over stale values
  const onCompleteRef = useRef(onComplete);
  const onHistoryRefreshRef = useRef(onHistoryRefresh);
  const onGeneratingChangeRef = useRef(onGeneratingChange);
  useEffect(() => { onCompleteRef.current = onComplete; }, [onComplete]);
  useEffect(() => { onHistoryRefreshRef.current = onHistoryRefresh; }, [onHistoryRefresh]);
  useEffect(() => { onGeneratingChangeRef.current = onGeneratingChange; }, [onGeneratingChange]);

  useEffect(() => {
    fetchExamples().then(setExamples).catch(console.error);
  }, []);

  // Notify parent of generating state changes
  useEffect(() => {
    onGeneratingChangeRef.current?.(generating);
  }, [generating]);

  useEffect(() => {
    if (!toast) return;
    const id = setTimeout(() => setToast(null), 6500);
    return () => clearTimeout(id);
  }, [toast]);

  // Abort on unmount
  useEffect(() => {
    return () => { abortRef.current?.abort(); };
  }, []);

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

  function pushToast(message: string, kind: ToastState["kind"] = "error") {
    setToast({ kind, message });
  }

  function handleStrategyChange(next: "single_prompt" | "two_shot_prompt" | "mermaid_compiler" | "automatic_grader") {
    setStrategy(next);
    setMermaidError(null);
    setGenerationError(null);
    if (next !== "automatic_grader") {
      setGradingExampleKey("");
    }
    if (next === "mermaid_compiler" || next === "automatic_grader") {
      setInputTab("example");
    }
  }

  function handleCancel() {
    abortRef.current?.abort();
    abortRef.current = null;
    setGenerating(false);
    setLogs([]);
    setProgressArtifacts(null);
    setShowAutoGradingStages(false);
    setGenerationError(null);
  }

  async function handleGenerate() {
    const desc = description.trim();
    const name = systemName.trim();
    if (!desc || !name) return;
    if (inputTab === "example" && !exampleKey) return;
    const promptStrategy: PromptStrategy =
      strategy === "two_shot_prompt" ? "two_shot_prompt" : "single_prompt";
    const startedAt = Date.now();

    const controller = new AbortController();
    abortRef.current = controller;

    setGenerating(true);
    setLogs([]);
    setProgressArtifacts(null);
    setGenerationError(null);

    const isManualCustomInput = inputTab === "custom";
    const shouldEnableAutoGrading = !isManualCustomInput && enableAutoGrading;
    setShowAutoGradingStages(shouldEnableAutoGrading);
    let finished = false;

    const completeRun = (run: Run) => {
      if (finished) return;
      finished = true;
      abortRef.current = null;
      setProgressArtifacts(null);
      setShowAutoGradingStages(false);
      setGenerating(false);
      onHistoryRefreshRef.current();
      onCompleteRef.current(run);
    };

    const failRun = (message: string) => {
      if (finished) return;
      finished = true;
      abortRef.current = null;
      setProgressArtifacts(null);
      setShowAutoGradingStages(false);
      setLogs((prev) => {
        const allLogs = [...prev, message];
        // Persist the error + collected logs so the user can see them
        // even after the progress panel disappears.
        setGenerationError({ message, logs: allLogs });
        return allLogs;
      });
      setGenerating(false);
    };

    const pollForRenderedRun = async () => {
      while (!finished && !controller.signal.aborted) {
        try {
          const history = await fetchHistory();
          const matchingRun = findMatchingRun(
            history,
            promptStrategy,
            name,
            model,
            startedAt
          );
          let matchingArtifacts: Artifacts | null = null;

          if (matchingRun) {
            try {
              const artifacts = await fetchArtifacts(matchingRun.folder);
              matchingArtifacts = artifacts;
              setProgressArtifacts(artifacts);
            } catch {
              // Ignore artifact polling failures; keep polling.
            }
          }

          const recoveredRun = findCompletedRun(
            history,
            promptStrategy,
            name,
            model,
            startedAt
          );
          if (recoveredRun) {
            // Keep prior behavior for non-grading runs: open as soon as image is ready.
            if (!shouldEnableAutoGrading) {
              completeRun(recoveredRun);
              return;
            }

            // For graded runs, only auto-open once grading artifacts are present.
            let recoveredArtifacts =
              matchingRun?.folder === recoveredRun.folder
                ? matchingArtifacts
                : null;

            if (!recoveredArtifacts) {
              try {
                recoveredArtifacts = await fetchArtifacts(recoveredRun.folder);
                setProgressArtifacts(recoveredArtifacts);
              } catch {
                // Keep waiting for grading completion signal/artifacts.
              }
            }

            // Check status.json first (authoritative); fall back to artifact heuristic.
            const st = recoveredArtifacts?.status;
            if (st) {
              if (st.status === "success" || st.status === "partial") {
                completeRun(recoveredRun);
                return;
              }
              if (st.status === "failed") {
                failRun(st.error?.message ?? "Generation failed.");
                return;
              }
              // "in_progress" — keep waiting.
            } else if (hasGradingArtifacts(recoveredArtifacts)) {
              completeRun(recoveredRun);
              return;
            }
          }
        } catch {
          // Ignore polling failures; SSE/error path will handle terminal state.
        }

        await new Promise((resolve) => setTimeout(resolve, 2000));
      }
    };

    try {
      void pollForRenderedRun();
      const res = await fetch("/api/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          strategy: promptStrategy,
          model,
          system_name: name,
          description: desc,
          example_key: inputTab === "example" ? exampleKey : null,
          enable_auto_grading: shouldEnableAutoGrading,
          input_mode: inputTab,
        }),
        signal: controller.signal,
      });

      if (!res.ok || !res.body) {
        failRun("Error: failed to start generation.");
        return;
      }

      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";
      let sawTerminalEvent = false;

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
            sawTerminalEvent = true;
            const payload = JSON.parse(data);

            // Check structured status from the backend.
            const runStatus = payload.status as string | undefined;
            const runError = payload.error as { message?: string; type?: string } | null | undefined;

            if (runStatus === "failed" && payload.folder) {
              // Open the run so the user can see the error banner in ArtifactView.
              const run: Run = {
                strategy: promptStrategy,
                model,
                system: name,
                folder: payload.folder,
                date: new Date().toISOString().slice(0, 10),
                time: new Date().toTimeString().slice(0, 8),
                has_png: false,
                run_status: "failed",
              };
              pushToast(
                runError?.message ?? "Generation failed."
              );
              completeRun(run);
              return;
            }

            if (runStatus === "failed") {
              failRun(runError?.message ?? "Generation failed.");
              return;
            }

            const run: Run = {
              strategy: promptStrategy,
              model,
              system: name,
              folder: payload.folder,
              date: new Date().toISOString().slice(0, 10),
              time: new Date().toTimeString().slice(0, 8),
              has_png: true,
            };

            if (runStatus === "partial") {
              // Generation OK but grading failed. Still open the run, but
              // show a toast so the user knows grading had issues.
              pushToast(
                runError?.message ?? "Generation succeeded but automatic grading failed."
              );
            }

            completeRun(run);
            return;
          } else if (eventType === "error") {
            sawTerminalEvent = true;
            // The server may send a structured JSON payload with a folder
            // reference, or a plain string for legacy/simple errors.
            let errorPayload: { message?: string; folder?: string; status?: string; error?: { message?: string } } | null = null;
            try {
              errorPayload = JSON.parse(data);
            } catch {
              // Plain string error — handled below.
            }

            if (errorPayload?.folder) {
              // A run folder exists — navigate to it so the user sees
              // the error banner and any partial artifacts in ArtifactView.
              const errorMsg =
                errorPayload.error?.message ??
                errorPayload.message ??
                "Generation failed.";
              const run: Run = {
                strategy: promptStrategy,
                model,
                system: name,
                folder: errorPayload.folder,
                date: new Date().toISOString().slice(0, 10),
                time: new Date().toTimeString().slice(0, 8),
                has_png: false,
                run_status: "failed",
              };
              pushToast(errorMsg);
              completeRun(run);
            } else {
              const errorMsg =
                errorPayload?.error?.message ??
                errorPayload?.message ??
                data;
              failRun(`Error: ${errorMsg}`);
            }
            return;
          }
        }
      }

      if (!sawTerminalEvent) {
        try {
          const history = await fetchHistory();
          const recoveredRun = findCompletedRun(
            history,
            promptStrategy,
            name,
            model,
            startedAt
          );
          if (recoveredRun) {
            if (!shouldEnableAutoGrading) {
              completeRun(recoveredRun);
              return;
            }

            const recoveredArtifacts = await fetchArtifacts(recoveredRun.folder).catch(
              () => null
            );
            if (recoveredArtifacts) {
              setProgressArtifacts(recoveredArtifacts);
            }

            // Check status.json first, then fall back to artifact heuristic.
            const st = recoveredArtifacts?.status;
            if (st) {
              if (st.status === "success" || st.status === "partial") {
                completeRun(recoveredRun);
                return;
              }
              if (st.status === "failed") {
                failRun(st.error?.message ?? "Generation failed.");
                return;
              }
            } else if (hasGradingArtifacts(recoveredArtifacts)) {
              completeRun(recoveredRun);
              return;
            }

            failRun("Error: generation stream ended before grading completed.");
          }
        } catch {
          // Fall through to the generic stream-closed error below.
        }

        failRun("Error: generation stream ended before completion.");
      }
    } catch (err) {
      if ((err as Error).name === "AbortError") return; // user cancelled
      failRun("Error: unexpected failure.");
    }

    if (!finished) {
      abortRef.current = null;
      setShowAutoGradingStages(false);
      setGenerating(false);
    }
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
        const detail = typeof err.detail === "object" ? err.detail : { message: err.detail };
        const message = (detail.message ?? "Rendering failed.") +
          " Ensure valid Mermaid state diagram syntax (stateDiagram-v2).";
        const errorFolder = detail.folder as string | undefined;

        // If a folder was created despite the failure, open it so the
        // user can see the error banner and mermaid source.
        if (errorFolder) {
          onHistoryRefresh();
          const run: Run = {
            strategy: "mermaid_compiler",
            model: "custom-input",
            system: name,
            folder: errorFolder,
            date: new Date().toISOString().slice(0, 10),
            time: new Date().toTimeString().slice(0, 8),
            has_png: false,
            run_status: "failed",
          };
          pushToast(message);
          onComplete(run);
          return;
        }

        setMermaidError(message);
        pushToast(detail.message ?? "Mermaid rendering failed.");
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
      pushToast("Network error while rendering Mermaid.");
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
        // The backend may return structured error details with a folder reference.
        const err = await res.json().catch(() => ({ detail: "Automatic grading failed." }));
        const detail = typeof err.detail === "object" ? err.detail : { message: err.detail };
        const message = detail.message ?? "Automatic grading failed.";
        const errorFolder = detail.folder as string | undefined;

        // If the backend created a folder despite the error, open it so the
        // user can inspect fallback artifacts + error state.
        if (errorFolder) {
          onHistoryRefresh();
          const selectedExample = examples.find((e) => e.key === gradingExampleKey);
          const run: Run = {
            strategy: "automatic_grader",
            model,
            system: selectedExample?.label ?? gradingExampleKey,
            folder: errorFolder,
            date: new Date().toISOString().slice(0, 10),
            time: new Date().toTimeString().slice(0, 8),
            has_png: false,
          };
          pushToast(message);
          onComplete(run);
          return;
        }

        // No folder — try history recovery.
        const recoveredRun = await recoverFromHistory();
        if (recoveredRun) {
          const { artifacts, errorMessage } = await waitForGradingCompletion(recoveredRun.folder);
          onHistoryRefresh();
          if (errorMessage || !artifacts?.grading_tsv) {
            setMermaidError(errorMessage || message);
            pushToast(errorMessage || message);
            return;
          }
          onComplete(recoveredRun);
          return;
        }

        setMermaidError(message);
        pushToast(message);
        return;
      }

      const payload = await res.json();
      const folder = payload.folder as string;
      const payloadStatus = payload.status as { status?: string; error?: { message?: string } } | null;
      const selectedExample = examples.find((e) => e.key === gradingExampleKey);

      // If the backend already reports failure/partial in the response, handle it directly.
      if (payloadStatus?.status === "failed") {
        onHistoryRefresh();
        const errMsg = payloadStatus.error?.message ?? "Automatic grading failed.";
        setMermaidError(errMsg);
        pushToast(errMsg);
        return;
      }

      if (payloadStatus?.status === "partial") {
        onHistoryRefresh();
        const warnMsg = payloadStatus.error?.message ?? "Grading completed with issues.";
        pushToast(warnMsg);
        const run: Run = {
          strategy: "automatic_grader",
          model,
          system: selectedExample?.label ?? gradingExampleKey,
          folder,
          date: new Date().toISOString().slice(0, 10),
          time: new Date().toTimeString().slice(0, 8),
          has_png: false,
        };
        onComplete(run);
        return;
      }

      // Success or status not yet written — poll for completion.
      const { artifacts, errorMessage } = await waitForGradingCompletion(folder);
      onHistoryRefresh();
      if (errorMessage || !artifacts?.grading_tsv) {
        const message = errorMessage || "Automatic grading failed.";
        setMermaidError(message);
        pushToast(message);
        return;
      }
      onHistoryRefresh();
      const run: Run = {
        strategy: "automatic_grader",
        model,
        system: selectedExample?.label ?? gradingExampleKey,
        folder,
        date: new Date().toISOString().slice(0, 10),
        time: new Date().toTimeString().slice(0, 8),
        has_png: false,
      };
      onComplete(run);
    } catch {
      const recoveredRun = await recoverFromHistory();
      if (recoveredRun) {
        const { artifacts, errorMessage } = await waitForGradingCompletion(recoveredRun.folder);
        onHistoryRefresh();
        if (errorMessage || !artifacts?.grading_tsv) {
          const message = errorMessage || "Automatic grading failed.";
          setMermaidError(message);
          pushToast(message);
          return;
        }
        onHistoryRefresh();
        onComplete(recoveredRun);
        return;
      }
      setMermaidError("Network error while grading. If artifacts were created, open the latest automatic grader run in History.");
      pushToast("Network error while grading. If artifacts were created, open the latest automatic grader run in History.");
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
      {toast && (
        <div className="pointer-events-auto fixed right-5 top-5 z-50 w-[min(24rem,calc(100vw-2.5rem))]">
          <div
            className={cn(
              "flex items-start gap-3 rounded-2xl border px-4 py-3 shadow-xl",
              toast.kind === "error"
                ? "border-red-500/30 bg-red-500/15 shadow-red-500/20"
                : "border-white/[0.12] bg-white/[0.08] shadow-black/40"
            )}
          >
            <span
              className={cn(
                "mt-0.5 rounded-full p-1.5",
                toast.kind === "error"
                  ? "bg-red-500/15 text-red-300"
                  : "bg-white/10 text-white/60"
              )}
            >
              <AlertTriangle className="h-4 w-4" />
            </span>
            <div className="flex-1 space-y-1">
              <p className="text-[11px] font-semibold uppercase tracking-[0.14em] text-white/45">Attention</p>
              <p className="text-sm leading-relaxed text-white/85">{toast.message}</p>
            </div>
            <button
              onClick={() => setToast(null)}
              className="mt-0.5 rounded-full p-1 text-white/30 transition-colors hover:bg-white/10 hover:text-white/80"
              aria-label="Dismiss notification"
            >
              <X className="h-4 w-4" />
            </button>
          </div>
        </div>
      )}
      <div className="flex flex-col px-6 py-10">
      <div className="mx-auto w-full max-w-5xl flex flex-col gap-10">
        <div className="flex flex-col items-center gap-1.5 text-center">
          <h1 className="text-5xl font-black tracking-tight bg-gradient-to-br from-orange-300 via-orange-400 to-orange-600 bg-clip-text text-transparent">Tracer</h1>
          <p className="text-sm text-white/30">Generate a state machine diagram from any system description.</p>
        </div>

        <div className="flex flex-col gap-10">

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

        {/* Generation failure card — shown after a prompt generation fails so
            the user sees the error instead of a silently-reset form. */}
        {generationError && !generating && isPromptStrategy && (
          <div className="overflow-hidden rounded-2xl border border-red-500/25 bg-red-500/10 shadow-lg shadow-red-500/5">
            <div className="flex items-center gap-2 border-b border-red-500/15 px-4 py-3">
              <AlertTriangle className="h-4 w-4 text-red-400" />
              <span className="text-[10px] font-bold uppercase tracking-widest text-red-400/70">Generation Failed</span>
              <button
                onClick={() => setGenerationError(null)}
                className="ml-auto rounded-full p-1 text-white/30 transition-colors hover:bg-white/10 hover:text-white/80"
                aria-label="Dismiss error"
              >
                <X className="h-3.5 w-3.5" />
              </button>
            </div>
            <div className="px-4 py-3">
              <p className="text-sm leading-relaxed text-red-300/80">{generationError.message}</p>
            </div>
            {generationError.logs.length > 1 && (
              <details className="border-t border-red-500/10">
                <summary className="cursor-pointer px-4 py-2 text-[11px] font-medium text-white/30 hover:text-white/50 transition-colors">
                  Show logs ({generationError.logs.length} lines)
                </summary>
                <ScrollArea className="max-h-44 px-3 pb-3">
                  <div className="flex flex-col gap-0.5">
                    {generationError.logs.map((line, i) => (
                      <p key={i} className="font-mono text-[10px] leading-relaxed text-red-300/40 break-all">
                        <span className="mr-1.5 text-white/15">›</span>{line}
                      </p>
                    ))}
                  </div>
                </ScrollArea>
              </details>
            )}
          </div>
        )}

        {isPromptStrategy && (
          <>
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
            {generating && (
              <GeneratingProgress
                strategy={strategy === "two_shot_prompt" ? "two_shot_prompt" : "single_prompt"}
                logs={logs}
                artifacts={progressArtifacts}
                showAutoGradingStages={showAutoGradingStages}
                onCancel={handleCancel}
              />
            )}
          </>
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

        </div>
      </div>
      </div>
    </div>
  );
}
