"use client";

import { useEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";
import type { Run } from "@/lib/types";
import { AppSidebar } from "@/components/AppSidebar";
import { RunForm } from "@/components/RunForm";
import { ArtifactView } from "@/components/ArtifactView";
import { SidebarProvider, SidebarInset, SidebarTrigger, useSidebar } from "@/components/ui/sidebar";

function CancelModal({ onKeep, onCancel }: { onKeep: () => void; onCancel: () => void }) {
  return createPortal(
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
      <div className="w-80 overflow-hidden rounded-2xl border border-white/[0.10] bg-[oklch(0.22_0.04_258)] shadow-2xl shadow-black/60">
        <div className="px-6 pt-6 pb-4">
          <p className="text-base font-semibold text-white/85">Cancel generation?</p>
          <p className="mt-1.5 text-sm text-white/40">A generation is still running. Cancel it and start a new run?</p>
        </div>
        <div className="flex gap-2 border-t border-white/[0.06] px-6 py-4">
          <button
            onClick={onKeep}
            className="flex-1 rounded-xl border border-white/[0.10] bg-white/[0.04] py-2 text-sm font-medium text-white/55 transition-all hover:border-white/[0.18] hover:bg-white/[0.07] hover:text-white/80"
          >
            Keep waiting
          </button>
          <button
            onClick={onCancel}
            className="flex-1 rounded-xl border border-red-500/30 bg-red-500/15 py-2 text-sm font-medium text-red-400 transition-all hover:border-red-500/50 hover:bg-red-500/25 hover:text-red-300"
          >
            Cancel & start over
          </button>
        </div>
      </div>
    </div>,
    document.body
  );
}

function CompletionToast({ run, onView, onDismiss }: { run: Run; onView: () => void; onDismiss: () => void }) {
  useEffect(() => {
    const t = setTimeout(onDismiss, 10_000);
    return () => clearTimeout(t);
  }, [onDismiss]);

  return createPortal(
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/55 backdrop-blur-sm">
      <div className="relative w-[min(30rem,calc(100vw-2rem))] overflow-hidden rounded-3xl border border-white/[0.10] bg-[oklch(0.22_0.04_258)] shadow-2xl shadow-black/70">
        <div className="pointer-events-none absolute -right-10 -top-10 h-36 w-36 rounded-full bg-orange-500/15 blur-3xl" />
        <button
          onClick={onDismiss}
          className="absolute right-4 top-4 text-white/25 transition-colors hover:text-white/55"
        >
          ✕
        </button>
        <div className="relative px-6 pb-5 pt-6">
          <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-2xl bg-orange-500/15 ring-1 ring-orange-400/25">
            <span className="h-2.5 w-2.5 rounded-full bg-orange-400" />
          </div>
          <p className="text-lg font-semibold text-white/85">Generation complete</p>
          <p className="mt-1 text-sm text-white/35">{run.system}</p>
          <p className="mt-4 text-sm leading-relaxed text-white/45">
            Your new diagram is ready. Open it now or stay on the current view.
          </p>
        </div>
        <div className="flex gap-2 border-t border-white/[0.06] px-6 py-4">
          <button
            onClick={onDismiss}
            className="flex-1 rounded-xl border border-white/[0.10] bg-white/[0.04] py-2 text-sm font-medium text-white/55 transition-all hover:border-white/[0.18] hover:bg-white/[0.07] hover:text-white/80"
          >
            Stay here
          </button>
          <button
            onClick={onView}
            className="flex-1 rounded-xl border border-orange-500/30 bg-orange-500/15 py-2 text-sm font-semibold text-orange-300 transition-all hover:border-orange-500/45 hover:bg-orange-500/22 hover:text-orange-200"
          >
            Check it out
          </button>
        </div>
      </div>
    </div>,
    document.body
  );
}

function FloatingTrigger() {
  const { open, isMobile, openMobile } = useSidebar();
  if (isMobile ? openMobile : open) return null;
  return (
    <div className="absolute top-3 left-3 z-50">
      <SidebarTrigger className="h-8 w-8 rounded-lg border border-white/[0.08] bg-white/[0.04] text-white/40 hover:text-white/70 transition-colors" />
    </div>
  );
}

export default function Home() {
  const [selectedRun, setSelectedRun] = useState<Run | null>(null);
  const [showForm, setShowForm] = useState(true);
  const [refreshToken, setRefreshToken] = useState(0);
  const [latestFolder, setLatestFolder] = useState<string | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [showCancelModal, setShowCancelModal] = useState(false);
  const [completedRun, setCompletedRun] = useState<Run | null>(null);

  // Refs so handleGenerationComplete always reads latest navigation state
  const showFormRef = useRef(showForm);
  const selectedRunRef = useRef(selectedRun);
  useEffect(() => { showFormRef.current = showForm; }, [showForm]);
  useEffect(() => { selectedRunRef.current = selectedRun; }, [selectedRun]);

  function handleSelectRun(run: Run) {
    setSelectedRun(run);
    setShowForm(false);
  }

  function handleNewRun() {
    if (isGenerating) {
      setShowCancelModal(true);
    } else {
      setSelectedRun(null);
      setShowForm(true);
    }
  }

  function handleModalKeep() {
    setShowCancelModal(false);
    setShowForm(true);
    setSelectedRun(null);
  }

  function handleModalCancel() {
    setShowCancelModal(false);
    setShowForm(false);
    setSelectedRun(null);
    setTimeout(() => setShowForm(true), 0);
  }

  function handleRefreshHistory() {
    setRefreshToken((t) => t + 1);
  }

  function handleGenerationComplete(run: Run) {
    setLatestFolder(run.folder);
    handleRefreshHistory();
    const viewingHistoryItem = selectedRunRef.current !== null;
    if (viewingHistoryItem) {
      setCompletedRun(run);
    } else {
      setCompletedRun(null);
      setSelectedRun(run);
      setShowForm(false);
    }
  }

  return (
    <SidebarProvider>
      {showCancelModal && (
        <CancelModal onKeep={handleModalKeep} onCancel={handleModalCancel} />
      )}
      {completedRun && (
        <CompletionToast
          run={completedRun}
          onView={() => {
            setSelectedRun(completedRun);
            setShowForm(false);
            setCompletedRun(null);
          }}
          onDismiss={() => setCompletedRun(null)}
        />
      )}
      <div className="relative flex h-screen w-full overflow-hidden bg-background">
        <AppSidebar
          selectedRun={selectedRun}
          onSelectRun={handleSelectRun}
          onNewRun={handleNewRun}
          refreshToken={refreshToken}
          latestFolder={latestFolder}
        />
        <SidebarInset className="relative flex flex-1 flex-col overflow-hidden">
          <FloatingTrigger />
          <div className="flex-1 overflow-auto">
            {/* Keep RunForm mounted to preserve generating state across navigation */}
            <div className={showForm && !selectedRun ? undefined : "hidden"}>
              <RunForm
                onComplete={handleGenerationComplete}
                onHistoryRefresh={handleRefreshHistory}
                onGeneratingChange={setIsGenerating}
              />
            </div>
            {selectedRun && (
              <ArtifactView run={selectedRun} onNewRun={handleNewRun} />
            )}
          </div>
        </SidebarInset>
      </div>
    </SidebarProvider>
  );
}
