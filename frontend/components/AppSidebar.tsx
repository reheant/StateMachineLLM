"use client";

import { useEffect, useState } from "react";
import { fetchHistory } from "@/lib/api";
import type { Run } from "@/lib/types";
import { HistoryItem } from "./HistoryItem";
import { cn } from "@/lib/utils";
import {
  Sidebar,
  SidebarContent,
  SidebarHeader,
  SidebarFooter,
  SidebarTrigger,
} from "@/components/ui/sidebar";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Plus } from "lucide-react";

interface Props {
  selectedRun: Run | null;
  onSelectRun: (run: Run) => void;
  onNewRun: () => void;
  refreshToken: number;
  latestFolder: string | null;
}

type StrategyFilter =
  | "all"
  | "single_prompt"
  | "two_shot_prompt"
  | "mermaid_compiler"
  | "automatic_grader";

export function AppSidebar({ selectedRun, onSelectRun, onNewRun, refreshToken, latestFolder }: Props) {
  const [history, setHistory] = useState<Run[]>([]);
  const [strategyFilter, setStrategyFilter] = useState<StrategyFilter>("all");

  useEffect(() => {
    fetchHistory().then(setHistory).catch(console.error);
  }, [refreshToken]);

  useEffect(() => {
    const id = setInterval(() => {
      fetchHistory().then(setHistory).catch(console.error);
    }, 30_000);
    return () => clearInterval(id);
  }, []);

  const filtered = history.filter(
    (r) => strategyFilter === "all" || r.strategy === strategyFilter
  );

  return (
    <Sidebar collapsible="offcanvas" className="border-r border-white/[0.06] bg-sidebar">
      {/* Amber top accent line */}
      <div className="h-[2px] w-full bg-gradient-to-r from-orange-400/60 via-orange-400/40 to-transparent" />

      {/* Brand header */}
      <SidebarHeader className="p-0">
        <div className="relative overflow-hidden px-5 pt-5 pb-5">
          <div className="pointer-events-none absolute -top-8 -left-8 h-32 w-32 rounded-full bg-orange-500/6 blur-2xl" />
          <div className="relative flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-orange-400 via-orange-500 to-orange-600 shadow-lg shadow-orange-500/30">
                {/* Tracer logo: state node + outgoing transition arrow */}
                <svg viewBox="0 0 24 24" fill="none" className="h-5 w-5" aria-hidden="true">
                  <path d="M17 3L21 7L8 20H4V16L17 3Z" stroke="white" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" fill="white" fillOpacity="0.15" />
                  <path d="M14 6L18 10" stroke="white" strokeWidth="2.2" strokeLinecap="round" />
                </svg>
              </div>
              <div>
                <p className="text-xl font-black tracking-tight bg-gradient-to-br from-orange-300 via-orange-400 to-orange-600 bg-clip-text text-transparent">Tracer</p>
                <p className="text-[11px] leading-tight text-orange-400/50">Trace your system.</p>
              </div>
            </div>
            <SidebarTrigger className="h-7 w-7 rounded-lg text-white/30 hover:text-white/60 transition-colors" />
          </div>
          <button
            onClick={onNewRun}
            className="mt-4 flex w-full items-center justify-center gap-2 rounded-xl border border-orange-500/25 bg-orange-500/10 py-2.5 text-sm font-medium text-orange-300 transition-all hover:border-orange-500/40 hover:bg-orange-500/15 hover:text-orange-200 active:scale-[0.98]"
          >
            <Plus className="h-3.5 w-3.5" />
            New Run
          </button>
        </div>
        <div className="mx-4 border-t border-white/[0.06]" />
      </SidebarHeader>

      <SidebarContent className="flex min-h-0 flex-col pt-3">
        <div className="px-4 pb-3">
          <p className="mb-2 text-[10px] font-semibold uppercase tracking-widest text-white/25">
            History
          </p>
          <div className="flex gap-1.5">
            {([
              { value: "all",              label: "All",    active: "bg-white/10 text-white/80",           inactive: "text-white/35" },
              { value: "single_prompt",    label: "1-shot", active: "bg-orange-400/20 text-orange-300 ring-1 ring-orange-400/20", inactive: "text-orange-400/40 hover:text-orange-300/70" },
              { value: "two_shot_prompt",  label: "2-shot", active: "bg-sky-400/20 text-sky-300 ring-1 ring-sky-400/20", inactive: "text-sky-400/40 hover:text-sky-300/70" },
              { value: "mermaid_compiler", label: "Compiler", active: "bg-emerald-400/20 text-emerald-300 ring-1 ring-emerald-400/20", inactive: "text-emerald-400/40 hover:text-emerald-300/70" },
              { value: "automatic_grader", label: "Grader", active: "bg-amber-400/20 text-amber-300 ring-1 ring-amber-400/20", inactive: "text-amber-400/40 hover:text-amber-300/70" },
            ] as const).map((opt) => (
              <button
                key={opt.value}
                onClick={() => setStrategyFilter(opt.value)}
                className={cn(
                  "flex-1 rounded-lg px-2 py-1.5 text-[11px] font-semibold transition-all",
                  strategyFilter === opt.value ? opt.active : opt.inactive
                )}
              >
                {opt.label}
              </button>
            ))}
          </div>
        </div>

        <ScrollArea className="flex-1 px-3">
          {filtered.length === 0 ? (
            <div className="flex flex-col items-center justify-center gap-2 py-12">
              <div className="text-3xl opacity-30">📭</div>
              <p className="text-center text-xs text-white/25">No runs yet</p>
            </div>
          ) : (
            <div className="flex flex-col gap-1.5 pb-3">
              {filtered.map((run) => (
                <HistoryItem
                  key={run.folder}
                  run={run}
                  selected={selectedRun?.folder === run.folder}
                  isNew={run.folder === latestFolder}
                  onClick={() => onSelectRun(run)}
                />
              ))}
            </div>
          )}
        </ScrollArea>
      </SidebarContent>

      <SidebarFooter className="border-t border-white/[0.06] px-5 py-3">
        <p className="text-[11px] text-white/20">
          {filtered.length} run{filtered.length !== 1 ? "s" : ""}
        </p>
      </SidebarFooter>
    </Sidebar>
  );
}
