"use client";

import { useState } from "react";
import type { Run } from "@/lib/types";
import { AppSidebar } from "@/components/AppSidebar";
import { RunForm } from "@/components/RunForm";
import { ArtifactView } from "@/components/ArtifactView";
import { SidebarProvider, SidebarInset, SidebarTrigger, useSidebar } from "@/components/ui/sidebar";

function FloatingTrigger() {
  const { open } = useSidebar();
  if (open) return null;
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

  function handleSelectRun(run: Run) {
    setSelectedRun(run);
    setShowForm(false);
  }

  function handleNewRun() {
    setSelectedRun(null);
    setShowForm(true);
  }

  function handleRefreshHistory() {
    setRefreshToken((t) => t + 1);
  }

  function handleGenerationComplete(run: Run) {
    setLatestFolder(run.folder);
    setSelectedRun(run);
    setShowForm(false);
  }

  return (
    <SidebarProvider>
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
            {showForm ? (
              <RunForm
                onComplete={handleGenerationComplete}
                onHistoryRefresh={handleRefreshHistory}
              />
            ) : selectedRun ? (
              <ArtifactView run={selectedRun} onNewRun={handleNewRun} />
            ) : null}
          </div>
        </SidebarInset>
      </div>
    </SidebarProvider>
  );
}
