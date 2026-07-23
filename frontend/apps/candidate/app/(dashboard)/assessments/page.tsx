"use client";

import React, { useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import { useUser } from "@/lib/hooks/useAuth";
import { useGetProfile } from "@/lib/hooks/useProfile";
import { useGetAssessmentResult, useResetAssessment } from "@/lib/hooks/useAssessment";
import { useGetCodingResult } from "@/lib/hooks/useCoding";
import { useGetInterviewResult } from "@/lib/hooks/useInterview";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import {
  Lock, CheckCircle2, XCircle, PlayCircle, ChevronRight,
  Clock, ShieldCheck, AlertTriangle, Code2, Mic, Activity,
  ArrowRight, FileText
} from "lucide-react";
import { toast } from "sonner";
import { cn } from "@/lib/utils";

// ─── Helpers ──────────────────────────────────────────────────────────────────

function StatusBadge({ status }: { status: string }) {
  const map: Record<string, string> = {
    LOCKED: "bg-muted text-muted-foreground border",
    READY: "bg-blue-500/10 text-blue-600 border border-blue-500/20",
    PASSED: "bg-green-500/10 text-green-600 border border-green-500/20",
    PASS: "bg-green-500/10 text-green-600 border border-green-500/20",
    FAILED: "bg-red-500/10 text-red-600 border border-red-500/20",
    FAIL: "bg-red-500/10 text-red-600 border border-red-500/20",
    TERMINATED: "bg-orange-500/10 text-orange-600 border border-orange-500/20",
    IN_PROGRESS: "bg-yellow-500/10 text-yellow-600 border border-yellow-500/20",
    "Strong Hire": "bg-green-500/10 text-green-600 border border-green-500/20",
    "Recommended": "bg-green-500/10 text-green-600 border border-green-500/20",
    "Not Recommended": "bg-red-500/10 text-red-600 border border-red-500/20",
  };
  return (
    <span className={cn("text-xs font-semibold px-2.5 py-1 rounded-full uppercase tracking-wide", map[status] || "bg-muted text-muted-foreground")}>
      {status}
    </span>
  );
}

// ─── Stage Card ───────────────────────────────────────────────────────────────

interface StageCardProps {
  number: number;
  icon: React.ReactNode;
  title: string;
  subtitle: string;
  duration: string;
  questions: string;
  status: string;
  locked: boolean;
  completed: boolean;
  result?: React.ReactNode;
  onStart?: () => void;
  onReset?: () => void;
}

function StageCard({ number, icon, title, subtitle, duration, questions, status, locked, completed, result, onStart, onReset }: StageCardProps) {
  return (
    <Card className={cn(
      "relative overflow-hidden border-2 transition-all duration-300",
      locked && "opacity-60 border-border",
      !locked && !completed && "border-primary/30 hover:border-primary/60 shadow-sm hover:shadow-md",
      completed && status === "PASSED" || completed && status === "PASS" || completed && status === "Strong Hire" || completed && status === "Recommended"
        ? "border-green-500/30 bg-green-500/5"
        : completed && (status === "FAILED" || status === "FAIL" || status === "Not Recommended")
        ? "border-red-500/30 bg-red-500/5"
        : completed && status === "TERMINATED"
        ? "border-orange-500/30 bg-orange-500/5"
        : ""
    )}>
      {/* Stage Number */}
      <div className="absolute top-4 right-4 w-8 h-8 rounded-full bg-muted flex items-center justify-center text-sm font-bold text-muted-foreground">
        {number}
      </div>

      <CardContent className="p-6">
        {/* Header */}
        <div className="flex items-start gap-4 mb-5">
          <div className={cn(
            "w-12 h-12 rounded-xl flex items-center justify-center shrink-0",
            locked ? "bg-muted text-muted-foreground" : "bg-primary/10 text-primary"
          )}>
            {locked ? <Lock className="w-5 h-5" /> : icon}
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 flex-wrap">
              <h3 className="font-bold text-lg">{title}</h3>
              <StatusBadge status={status} />
            </div>
            <p className="text-sm text-muted-foreground mt-0.5">{subtitle}</p>
          </div>
        </div>

        {/* Meta */}
        {!completed && (
          <div className="flex gap-4 text-sm text-muted-foreground mb-5">
            <span className="flex items-center gap-1.5"><Clock className="w-3.5 h-3.5" />{duration}</span>
            <span className="flex items-center gap-1.5"><CheckCircle2 className="w-3.5 h-3.5" />{questions}</span>
            <span className="flex items-center gap-1.5 text-amber-600"><ShieldCheck className="w-3.5 h-3.5" />Proctor</span>
          </div>
        )}

        {/* Result content */}
        {completed && result}

        {/* Actions */}
        <div className="flex items-center justify-between mt-4">
          {onReset && (
            <Button variant="ghost" size="sm" className="text-muted-foreground text-xs" onClick={onReset}>
              Reset (Dev)
            </Button>
          )}
          {!locked && !completed && onStart && (
            <Button size="sm" className="ml-auto gap-2" onClick={onStart}>
              <PlayCircle className="w-4 h-4" />
              {status === "IN_PROGRESS" ? "Resume" : "Start"}
            </Button>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

// ─── Main Page ────────────────────────────────────────────────────────────────

export default function AssessmentHubPage() {
  const router = useRouter();
  const { data: user } = useUser();
  const candidateId = user?.id;

  const { data: profile, isLoading: profileLoading } = useGetProfile(candidateId);
  const { data: aptResult, isLoading: aptLoading } = useGetAssessmentResult(candidateId);
  const { data: codingResult, isLoading: codingLoading } = useGetCodingResult(candidateId);
  const { data: interviewResult, isLoading: interviewLoading } = useGetInterviewResult(candidateId);
  const resetApt = useResetAssessment();

  const isLoading = profileLoading || aptLoading || codingLoading || interviewLoading;

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-[60vh]">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary" />
      </div>
    );
  }

  const profilePct = profile?.profile_completion ?? 0;
  const isEligible = profilePct >= 70;

  // Stage statuses
  const aptStatus = !isEligible ? "LOCKED"
    : aptResult ? aptResult.status
    : "READY";
  const aptPassed = aptResult?.status === "PASSED";

  const codingStatus = !aptPassed ? "LOCKED"
    : codingResult ? codingResult.status
    : "READY";
  const codingPassed = codingResult?.status === "PASS";

  const interviewStatus = !codingPassed ? "LOCKED"
    : interviewResult ? (interviewResult.hiring_recommendation ?? "COMPLETED")
    : "READY";

  const handleResetApt = async () => {
    if (confirm("Reset Aptitude? This is a dev-only action.")) {
      await resetApt.mutateAsync();
      toast.success("Aptitude reset.");
    }
  };

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Assessment Center</h1>
        <p className="text-muted-foreground mt-1">
          Complete all three stages to unlock job applications.
        </p>
      </div>

      {/* Profile gate warning */}
      {!isEligible && (
        <div className="bg-amber-500/10 border border-amber-500/20 text-amber-700 p-4 rounded-xl flex items-start gap-3">
          <AlertTriangle className="w-5 h-5 shrink-0 mt-0.5" />
          <div>
            <p className="font-semibold text-sm">Profile Incomplete — Assessments Locked</p>
            <p className="text-xs mt-1">Your profile is {profilePct}% complete. Reach 70% to unlock the Aptitude Assessment.</p>
            <Button size="sm" variant="outline" className="mt-2" onClick={() => router.push("/profile")}>
              Complete Profile
            </Button>
          </div>
        </div>
      )}

      {/* Pipeline connector */}
      <div className="space-y-2">
        {/* ── Stage 1: Aptitude ── */}
        <StageCard
          number={1}
          icon={<Activity className="w-5 h-5" />}
          title="Aptitude Assessment"
          subtitle="Quantitative · Logical · Verbal · Analytical"
          duration="25 minutes"
          questions="25 MCQs"
          status={aptStatus}
          locked={!isEligible}
          completed={!!aptResult}
          onStart={() => router.push("/assessments/take")}
          onReset={aptResult ? handleResetApt : undefined}
          result={aptResult && (
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-3xl font-bold">{Math.round(aptResult.aptitude_score)}%</span>
                <div className="text-right text-sm text-muted-foreground">
                  <div>{aptResult.total_correct} correct · {aptResult.total_wrong} wrong</div>
                  <div className="text-xs">{new Date(aptResult.created_at).toLocaleDateString()}</div>
                </div>
              </div>
              <Progress value={aptResult.aptitude_score} className="h-2" />
              <div className="grid grid-cols-3 gap-2 text-xs mt-2">
                {[
                  ["Quantitative", aptResult.quantitative_score],
                  ["Logical", aptResult.logical_score],
                  ["Verbal", aptResult.verbal_score],
                ].map(([label, val]) => (
                  <div key={label as string} className="bg-muted/40 p-2 rounded-lg text-center">
                    <div className="font-bold">{Math.round(val as number)}%</div>
                    <div className="text-muted-foreground">{label}</div>
                  </div>
                ))}
              </div>
            </div>
          )}
        />

        {/* Arrow connector */}
        <div className="flex justify-center py-1">
          <ArrowRight className={cn("w-5 h-5 rotate-90 transition-colors", aptPassed ? "text-primary" : "text-muted-foreground/30")} />
        </div>

        {/* ── Stage 2: Coding ── */}
        <StageCard
          number={2}
          icon={<Code2 className="w-5 h-5" />}
          title="Coding Assessment"
          subtitle="Python 3 · Data Structures · Algorithms"
          duration="60 minutes"
          questions="5 Problems (Easy/Medium/Hard)"
          status={codingStatus}
          locked={!aptPassed}
          completed={!!codingResult}
          onStart={() => router.push("/assessments/coding")}
          result={codingResult && (
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-3xl font-bold">{Math.round(codingResult.total_score)}%</span>
                <div className="text-right text-sm text-muted-foreground">
                  <div>{codingResult.questions_solved}/{codingResult.questions_attempted} solved</div>
                </div>
              </div>
              <Progress value={codingResult.total_score} className="h-2" />
              <div className="grid grid-cols-3 gap-2 text-xs mt-2">
                {[
                  ["Easy", codingResult.easy_score],
                  ["Medium", codingResult.medium_score],
                  ["Hard", codingResult.hard_score],
                ].map(([label, val]) => (
                  <div key={label as string} className="bg-muted/40 p-2 rounded-lg text-center">
                    <div className="font-bold">{Math.round(val as number)}%</div>
                    <div className="text-muted-foreground">{label}</div>
                  </div>
                ))}
              </div>
            </div>
          )}
        />

        {/* Arrow connector */}
        <div className="flex justify-center py-1">
          <ArrowRight className={cn("w-5 h-5 rotate-90 transition-colors", codingPassed ? "text-primary" : "text-muted-foreground/30")} />
        </div>

        {/* ── Stage 3: Professional Assessment ── */}
        <StageCard
          number={3}
          icon={<FileText className="w-5 h-5" />}
          title="Professional Assessment"
          subtitle="Problem Solving · Technical · Analytical"
          duration="60 minutes"
          questions="10 Descriptive Questions"
          status={interviewStatus}
          locked={!codingPassed}
          completed={!!interviewResult}
          onStart={() => router.push("/interviews")}
          result={interviewResult && (
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <div>
                  <span className="text-3xl font-bold">{Math.round(interviewResult.total_score)}</span>
                  <span className="text-muted-foreground text-sm ml-1">/100</span>
                </div>
                <div className="text-right text-sm">
                  <div className="font-semibold">Grade: {interviewResult.grade}</div>
                  <div className="text-muted-foreground text-xs">{interviewResult.hiring_recommendation}</div>
                </div>
              </div>
              <Progress value={interviewResult.total_score} className="h-2" />
              <div className="grid grid-cols-3 gap-2 text-xs mt-2">
                {[
                  ["Tech", interviewResult.technical_score, 15],
                  ["Comm", interviewResult.communication_score, 15],
                  ["Reasoning", interviewResult.professionalism_score, 10],
                ].map(([label, val, max]) => (
                  <div key={label as string} className="bg-muted/40 p-2 rounded-lg text-center">
                    <div className="font-bold">{Math.round(val as number)}<span className="text-muted-foreground font-normal">/{max}</span></div>
                    <div className="text-muted-foreground">{label}</div>
                  </div>
                ))}
              </div>
            </div>
          )}
        />
      </div>

      {/* All complete banner */}
      {aptPassed && codingPassed && interviewResult && (
        <div className="bg-green-500/10 border border-green-500/20 text-green-700 p-4 rounded-xl flex items-center gap-3">
          <CheckCircle2 className="w-5 h-5 shrink-0" />
          <div>
            <p className="font-semibold text-sm">All Assessments Completed!</p>
            <p className="text-xs mt-0.5">Your profile is now visible to recruiters and you can apply to premium jobs.</p>
          </div>
        </div>
      )}
    </div>
  );
}
