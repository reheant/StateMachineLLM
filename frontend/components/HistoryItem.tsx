"use client";

import type { Run } from "@/lib/types";
import { cn } from "@/lib/utils";

interface Props {
  run: Run;
  selected: boolean;
  isNew: boolean;
  onClick: () => void;
}

const STRATEGY_CONFIG: Record<string, { label: string; badge: string; accent: string }> = {
  single_prompt: {
    label: "1-shot",
    badge: "bg-orange-400/15 text-orange-300",
    accent: "bg-gradient-to-b from-orange-300 to-orange-500",
  },
  two_shot_prompt: {
    label: "2-shot",
    badge: "bg-sky-400/15 text-sky-300",
    accent: "bg-gradient-to-b from-sky-300 to-sky-500",
  },
  mermaid_compiler: {
    label: "Compiler",
    badge: "bg-emerald-400/15 text-emerald-300",
    accent: "bg-gradient-to-b from-emerald-300 to-emerald-500",
  },
  automatic_grader: {
    label: "Grader",
    badge: "bg-amber-400/15 text-amber-300",
    accent: "bg-gradient-to-b from-amber-300 to-amber-500",
  },
};

function cleanName(raw: string): string {
  return raw
    .replace(/[_ ]+(winter|spring|summer|fall)[_ ]+\d{4}.*/i, "")
    .replace(/_/g, " ")
    .trim();
}

export function HistoryItem({ run, selected, isNew, onClick }: Props) {
  const config = STRATEGY_CONFIG[run.strategy] ?? { label: run.strategy, badge: "bg-white/[0.06] text-white/30", accent: "bg-gradient-to-b from-white/20 to-white/10" };
  const modelShort = run.model.split(":").pop()?.replace(/-/g, " ") ?? run.model;
  const displayName = cleanName(run.system);
  const isFailed = run.run_status === "failed";
  const isPartial = run.run_status === "partial";

  return (
    <button
      onClick={onClick}
      className={cn(
        "group relative w-full rounded-xl border px-3.5 py-3 text-left transition-all duration-150",
        selected
          ? "border-orange-400/20 bg-orange-400/8"
          : "border-white/[0.06] bg-white/[0.02] hover:border-white/[0.10] hover:bg-white/[0.04]"
      )}
    >
      {/* Left strategy accent — always visible, brighter when selected */}
      <span className={cn(
        "absolute left-0 top-2.5 bottom-2.5 w-[3px] rounded-full transition-opacity",
        isFailed ? "bg-gradient-to-b from-red-400 to-red-600" : isPartial ? "bg-gradient-to-b from-amber-400 to-amber-600" : config.accent,
        selected ? "opacity-100" : "opacity-30 group-hover:opacity-50"
      )} />

      <div className="flex items-start justify-between gap-2 pl-1">
        <span className={cn(
          "truncate text-[13px] font-semibold leading-snug",
          selected ? "text-white" : "text-white/60 group-hover:text-white/80"
        )}>
          {displayName}
        </span>
        <div className="flex shrink-0 items-center gap-1 pt-0.5">
          {(isFailed || isPartial) && (
            <span className={cn(
              "rounded-md px-1.5 py-0.5 text-[9px] font-bold uppercase tracking-wide ring-1",
              isFailed
                ? "bg-red-500/20 text-red-400 ring-red-500/30"
                : "bg-amber-500/20 text-amber-400 ring-amber-500/30"
            )}>
              {isFailed ? "Failed" : "Partial"}
            </span>
          )}
          {isNew && (
            <span className="animate-pulse rounded-md bg-red-500/25 px-1.5 py-0.5 text-[9px] font-bold uppercase tracking-wide text-red-400 ring-1 ring-red-500/40">
              New
            </span>
          )}
          <span className={cn("rounded-md px-1.5 py-0.5 text-[10px] font-semibold", config.badge)}>
            {config.label}
          </span>
        </div>
      </div>

      <div className="mt-1.5 flex items-center justify-between pl-1">
        <span className={cn(
          "text-[11px] capitalize",
          selected ? "text-white/45" : "text-white/25"
        )}>
          {modelShort}
        </span>
        <span className={cn(
          "shrink-0 text-[11px] tabular-nums",
          selected ? "text-white/35" : "text-white/20"
        )}>
          {run.date}
        </span>
      </div>
    </button>
  );
}
