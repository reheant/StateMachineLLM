"use client";

import { useEffect, useState } from "react";
import { fetchArtifacts, imageUrl, fileUrl } from "@/lib/api";
import type { Run, Artifacts } from "@/lib/types";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import { ChevronDown, Plus } from "lucide-react";
import { cn } from "@/lib/utils";

interface Props {
  run: Run;
  onNewRun: () => void;
}

function CollapsibleSection({
  title,
  badge,
  children,
}: {
  title: string;
  badge?: string;
  children: React.ReactNode;
}) {
  const [open, setOpen] = useState(false);
  return (
    <Collapsible open={open} onOpenChange={setOpen}>
      <CollapsibleTrigger className="flex w-full items-center justify-between px-5 py-3.5 text-sm font-medium text-white/50 hover:text-white/70 transition-colors">
        <div className="flex items-center gap-2">
          {title}
          {badge && (
            <span className="rounded bg-white/[0.06] px-1.5 py-0.5 font-mono text-[10px] text-white/30">
              {badge}
            </span>
          )}
        </div>
        <ChevronDown
          className={cn("h-4 w-4 transition-transform duration-200", open && "rotate-180")}
        />
      </CollapsibleTrigger>
      <CollapsibleContent>
        <div className="px-5 pb-5">{children}</div>
      </CollapsibleContent>
    </Collapsible>
  );
}

function FileContent({ path }: { path: string }) {
  const [text, setText] = useState<string | null>(null);

  useEffect(() => {
    fetch(fileUrl(path))
      .then((r) => r.text())
      .then(setText)
      .catch(() => setText("Failed to load file."));
  }, [path]);

  if (text === null)
    return <p className="text-sm text-white/20">Loading…</p>;

  return (
    <pre className="max-h-[60vh] overflow-auto rounded-xl bg-black/40 border border-white/[0.06] px-5 py-4 text-xs font-mono leading-relaxed text-orange-300/60 whitespace-pre-wrap break-words">
      {text}
    </pre>
  );
}

export function ArtifactView({ run, onNewRun }: Props) {
  const [artifacts, setArtifacts] = useState<Artifacts | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setArtifacts(null);
    setError(null);
    fetchArtifacts(run.folder)
      .then(setArtifacts)
      .catch(() => setError("Failed to load artifacts."));
  }, [run.folder]);

  const strategyLabel = run.strategy === "single_prompt" ? "Single Prompt" : "Two-Shot";

  if (error)
    return <p className="p-10 text-sm text-red-400">{error}</p>;

  return (
    <div className="flex flex-col bg-background">
      {/* Header */}
      <div className="relative overflow-hidden border-b border-white/[0.06] px-10 py-10">
        <div className="pointer-events-none absolute -top-16 right-1/4 h-56 w-72 rounded-full bg-orange-500/8 blur-3xl" />
        <div className="pointer-events-none absolute bottom-0 left-1/3 h-24 w-48 rounded-full bg-orange-500/6 blur-2xl" />
        <div className="relative flex items-start justify-between gap-6">
          <div className="flex items-start gap-5">
            {/* Logo mark */}
            <div className="mt-1 flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-orange-400 via-orange-500 to-orange-600 shadow-xl shadow-orange-500/25">
              <svg viewBox="0 0 32 32" fill="none" className="h-6 w-6" aria-hidden="true">
                <path d="M22 4L28 10L11 27H5V21L22 4Z" stroke="white" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" fill="white" fillOpacity="0.15" />
                <path d="M18 8L24 14" stroke="white" strokeWidth="2.5" strokeLinecap="round" />
              </svg>
            </div>
            <div>
              <p className="text-[11px] font-bold uppercase tracking-[0.18em] text-orange-400/70">
                Tracer · Result
              </p>
              <h1 className="mt-1 text-3xl font-bold tracking-tight text-white">{run.system}</h1>
              <p className="mt-1.5 text-sm text-white/30">{run.date} · {run.time}</p>
            </div>
          </div>
          <div className="flex items-center gap-2 pt-1">
            <span className="rounded-lg border border-white/[0.08] bg-white/[0.04] px-3 py-1.5 text-xs font-medium text-white/40">
              {strategyLabel}
            </span>
            <span className="rounded-lg border border-white/[0.08] bg-white/[0.04] px-3 py-1.5 font-mono text-xs text-white/30">
              {run.model.split(":").pop()}
            </span>
            <button
              onClick={onNewRun}
              className="flex items-center gap-1.5 rounded-lg border border-orange-500/20 bg-orange-500/10 px-3 py-1.5 text-xs font-medium text-orange-300 transition-all hover:border-orange-500/30 hover:bg-orange-500/15"
            >
              <Plus className="h-3 w-3" />
              New Run
            </button>
          </div>
        </div>
      </div>

      {!artifacts ? (
        <div className="flex flex-1 items-center justify-center gap-3">
          <div className="h-5 w-5 animate-spin rounded-full border-2 border-white/10 border-t-orange-400" />
          <p className="text-sm text-white/25">Loading…</p>
        </div>
      ) : (
        <div className="flex flex-1 flex-col gap-5 overflow-auto p-10">

          {/* Diagram */}
          {artifacts.png && (
            <div className="overflow-hidden rounded-2xl border border-white/[0.07] bg-white/[0.02] shadow-2xl shadow-black/50 ring-1 ring-white/[0.04]">
              <img
                src={imageUrl(artifacts.png)}
                alt={`${run.system} state machine`}
                className="w-full"
              />
            </div>
          )}

          {/* Collapsible files */}
          {(artifacts.mmd || artifacts.llm_log || artifacts.txt) && (
            <div className="overflow-hidden rounded-2xl border border-white/[0.07] bg-white/[0.02] divide-y divide-white/[0.05]">
              {artifacts.mmd && (
                <CollapsibleSection title="Mermaid source" badge=".mmd">
                  <FileContent path={artifacts.mmd} />
                </CollapsibleSection>
              )}
              {artifacts.llm_log && (
                <CollapsibleSection title="LLM log">
                  <FileContent path={artifacts.llm_log} />
                </CollapsibleSection>
              )}
              {artifacts.txt && !artifacts.mmd && (
                <CollapsibleSection title="Raw output" badge=".txt">
                  <FileContent path={artifacts.txt} />
                </CollapsibleSection>
              )}
            </div>
          )}

          {!artifacts.png && !artifacts.mmd && !artifacts.txt && !artifacts.llm_log && (
            <div className="flex flex-1 items-center justify-center rounded-2xl border border-white/[0.06] bg-white/[0.02] py-20">
              <p className="text-sm text-white/20">No artifacts found.</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
