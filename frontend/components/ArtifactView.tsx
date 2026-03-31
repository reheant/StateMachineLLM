"use client";

import { useEffect, useState } from "react";
import { fetchArtifacts, imageUrl, fileUrl } from "@/lib/api";
import type { Run, Artifacts } from "@/lib/types";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import { AlertTriangle, ChevronDown, Plus } from "lucide-react";
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

function GradingGrid({ path }: { path: string }) {
  const [rows, setRows] = useState<string[][] | null>(null);

  useEffect(() => {
    fetch(fileUrl(path))
      .then((r) => r.text())
      .then((text) => {
        const parsed = text
          .split(/\r?\n/)
          .filter((line) => line.trim().length > 0)
          .map((line) => line.split("\t"));
        setRows(parsed);
      })
      .catch(() => setRows([]));
  }, [path]);

  if (rows === null) {
    return <p className="text-sm text-white/20">Loading…</p>;
  }

  if (rows.length === 0) {
    return <p className="text-sm text-white/20">No grading rows found.</p>;
  }

  const [header, ...body] = rows;

  return (
    <div className="max-h-[60vh] overflow-auto rounded-xl border border-white/[0.06] bg-black/30">
      <table className="w-full border-collapse text-xs text-white/70">
        <thead className="sticky top-0 bg-white/[0.06] text-white/80">
          <tr>
            {header.map((cell, i) => (
              <th key={i} className="border-b border-white/[0.08] px-3 py-2 text-left font-semibold">
                {cell}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {body.map((row, rowIdx) => (
            <tr key={rowIdx} className="odd:bg-white/[0.02]">
              {row.map((cell, cellIdx) => (
                <td key={cellIdx} className="border-b border-white/[0.05] px-3 py-2 align-top leading-relaxed">
                  {cell}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export function ArtifactView({ run, onNewRun }: Props) {
  const [artifactsState, setArtifactsState] = useState<{
    folder: string;
    artifacts: Artifacts | null;
    error: string | null;
  }>({
    folder: run.folder,
    artifacts: null,
    error: null,
  });

  useEffect(() => {
    fetchArtifacts(run.folder)
      .then((artifacts) => {
        setArtifactsState({
          folder: run.folder,
          artifacts,
          error: null,
        });
      })
      .catch(() => {
        setArtifactsState({
          folder: run.folder,
          artifacts: null,
          error: "Failed to load artifacts.",
        });
      });
  }, [run.folder]);

  const isCurrentRunLoaded = artifactsState.folder === run.folder;
  const artifacts = isCurrentRunLoaded ? artifactsState.artifacts : null;
  const error = isCurrentRunLoaded ? artifactsState.error : null;

  const strategyLabel =
    run.strategy === "single_prompt"
      ? "Single Prompt"
      : run.strategy === "two_shot_prompt"
      ? "Two-Shot Prompt"
      : run.strategy === "mermaid_compiler"
      ? "Mermaid Compiler"
      : "Automatic Grader";
  const isTwoShot = run.strategy === "two_shot_prompt";

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

          {/* Error / partial-failure banner */}
          {artifacts.status &&
            (artifacts.status.status === "failed" ||
              artifacts.status.status === "partial") && (
              <div
                className={cn(
                  "flex items-start gap-3 rounded-2xl border px-5 py-4",
                  artifacts.status.status === "failed"
                    ? "border-red-500/25 bg-red-500/10"
                    : "border-amber-500/25 bg-amber-500/10"
                )}
              >
                <AlertTriangle
                  className={cn(
                    "mt-0.5 h-5 w-5 shrink-0",
                    artifacts.status.status === "failed"
                      ? "text-red-400"
                      : "text-amber-400"
                  )}
                />
                <div className="flex flex-col gap-1">
                  <p
                    className={cn(
                      "text-sm font-semibold",
                      artifacts.status.status === "failed"
                        ? "text-red-300"
                        : "text-amber-300"
                    )}
                  >
                    {artifacts.status.status === "failed"
                      ? "Run failed"
                      : "Grading issue"}
                  </p>
                  <p className="text-sm leading-relaxed text-white/50">
                    {artifacts.status.error?.message ??
                      "An error occurred during this run."}
                  </p>
                  {(() => {
                    const err = artifacts.status.error;
                    if (!err || !err.type) return null;
                    const attempts = err.attempts ?? 0;
                    return (
                      <span className="mt-1 w-fit rounded-md bg-white/[0.06] px-2 py-0.5 font-mono text-[10px] text-white/30">
                        {err.type}
                        {attempts > 0 &&
                          ` · ${attempts} attempt${attempts === 1 ? "" : "s"}`}
                      </span>
                    );
                  })()}
                </div>
              </div>
            )}

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
          {(artifacts.mmd || artifacts.llm_log || artifacts.txt || artifacts.shot1_mmd || artifacts.shot1_png || artifacts.shot1_txt || artifacts.grading_prompt || artifacts.grading_output || artifacts.ground_truth_csv || artifacts.grading_csv || artifacts.grading_tsv) && (
            <div className="overflow-hidden rounded-2xl border border-white/[0.07] bg-white/[0.02] divide-y divide-white/[0.05]">
              {isTwoShot && artifacts.txt && (
                <CollapsibleSection title="Shot 2 Mermaid code" badge=".txt">
                  <FileContent path={artifacts.txt} />
                </CollapsibleSection>
              )}
              {isTwoShot && artifacts.shot1_png && (
                <CollapsibleSection title="Shot 1 diagram" badge=".png">
                  <div className="overflow-hidden rounded-xl border border-white/[0.06] bg-black/20">
                    <img
                      src={imageUrl(artifacts.shot1_png)}
                      alt={`${run.system} shot 1 state machine`}
                      className="w-full"
                    />
                  </div>
                </CollapsibleSection>
              )}
              {isTwoShot && artifacts.shot1_txt && (
                <CollapsibleSection title="Shot 1 Mermaid code" badge=".txt">
                  <FileContent path={artifacts.shot1_txt} />
                </CollapsibleSection>
              )}
              {!isTwoShot && artifacts.mmd && (
                <CollapsibleSection title="Mermaid source" badge=".mmd">
                  <FileContent path={artifacts.mmd} />
                </CollapsibleSection>
              )}
              {artifacts.grading_tsv && (
                <CollapsibleSection title="Automatic grading grid" badge=".tsv">
                  <GradingGrid path={artifacts.grading_tsv} />
                </CollapsibleSection>
              )}
              {artifacts.ground_truth_csv && (
                <CollapsibleSection title="Ground truth grading sheet" badge=".csv">
                  <FileContent path={artifacts.ground_truth_csv} />
                </CollapsibleSection>
              )}
              {artifacts.grading_csv && (
                <CollapsibleSection title="Automatic grading results" badge=".csv">
                  <FileContent path={artifacts.grading_csv} />
                </CollapsibleSection>
              )}
              {artifacts.grading_tsv && (
                <CollapsibleSection title="Automatic grading results" badge=".tsv">
                  <FileContent path={artifacts.grading_tsv} />
                </CollapsibleSection>
              )}
              {artifacts.grading_prompt && (
                <CollapsibleSection title="Automatic grading prompt">
                  <FileContent path={artifacts.grading_prompt} />
                </CollapsibleSection>
              )}
              {artifacts.grading_output && (
                <CollapsibleSection title="Automatic grading output">
                  <FileContent path={artifacts.grading_output} />
                </CollapsibleSection>
              )}
              {artifacts.llm_log && (
                <CollapsibleSection title="LLM log">
                  <FileContent path={artifacts.llm_log} />
                </CollapsibleSection>
              )}
              {!isTwoShot && artifacts.txt && !artifacts.mmd && (
                <CollapsibleSection title="Raw output" badge=".txt">
                  <FileContent path={artifacts.txt} />
                </CollapsibleSection>
              )}
            </div>
          )}

          {!artifacts.png && !artifacts.mmd && !artifacts.txt && !artifacts.llm_log && !artifacts.grading_prompt && !artifacts.grading_output && !artifacts.ground_truth_csv && !artifacts.grading_csv && !artifacts.grading_tsv && (
            <div className="flex flex-1 flex-col items-center justify-center gap-3 rounded-2xl border border-white/[0.06] bg-white/[0.02] py-20">
              {artifacts.status &&
                (artifacts.status.status === "failed" ||
                  artifacts.status.status === "partial") ? (
                <>
                  <AlertTriangle className="h-6 w-6 text-red-400/50" />
                  <p className="text-sm text-white/30">
                    This run failed before producing output artifacts.
                  </p>
                </>
              ) : (
                <p className="text-sm text-white/20">No artifacts found.</p>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
