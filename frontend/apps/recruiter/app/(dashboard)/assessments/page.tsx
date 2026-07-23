"use client";
import React from "react";
export default function AssessmentsPage() {
  return (
    <div className="flex flex-col h-full space-y-4">
      <div className="sticky top-0 z-10 bg-muted/20 backdrop-blur-md pb-4 border-b border-border/50">
        <h2 className="text-3xl font-bold tracking-tight text-foreground">Assessments</h2>
        <p className="text-muted-foreground mt-1">Manage and review candidate assessments.</p>
      </div>
      <div className="flex items-center justify-center h-40">
        <p className="text-muted-foreground">Assessments module is coming soon.</p>
      </div>
    </div>
  );
}
