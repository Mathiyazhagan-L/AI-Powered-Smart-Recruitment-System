"use client";

import React, { useState, useEffect, useCallback, useRef } from "react";
import { useRouter } from "next/navigation";
import dynamic from "next/dynamic";
import { useUser } from "@/lib/hooks/useAuth";
import {
  useStartCoding, useRunCode, useSubmitSolution, useFinishCoding,
  CodingQuestion, TestCaseResult,
} from "@/lib/hooks/useCoding";
import ProctoringMonitor from "@/components/assessment/ProctoringMonitor";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { toast } from "sonner";
import {
  Play, Send, Clock, ChevronLeft, ChevronRight,
  CheckCircle2, XCircle, Loader2, ShieldCheck, AlertCircle,
  Code2, Save,
} from "lucide-react";
import { cn } from "@/lib/utils";

// Dynamically import Monaco to avoid SSR issues
const MonacoEditor = dynamic(() => import("@monaco-editor/react"), { ssr: false });

// ─── Helpers ─────────────────────────────────────────────────────────────────

const DIFFICULTY_COLOR: Record<string, string> = {
  Easy: "bg-green-500/10 text-green-600 border-green-500/20",
  Medium: "bg-yellow-500/10 text-yellow-600 border-yellow-500/20",
  Hard: "bg-red-500/10 text-red-600 border-red-500/20",
};

function formatTime(s: number) {
  const m = Math.floor(s / 60).toString().padStart(2, "0");
  const sec = (s % 60).toString().padStart(2, "0");
  return `${m}:${sec}`;
}

// ─── Test Result Panel ────────────────────────────────────────────────────────

function TestPanel({
  status, results, error, stdout, isRunning,
}: {
  status: string | null; results: TestCaseResult[]; error?: string; stdout?: string; isRunning: boolean;
}) {
  if (isRunning) return (
    <div className="flex items-center gap-2 text-muted-foreground p-4 text-sm">
      <Loader2 className="w-4 h-4 animate-spin" />Running your code...
    </div>
  );
  if (!status) return (
    <div className="p-4 text-sm text-muted-foreground">
      Click <strong>Run</strong> to test your code against sample cases.
    </div>
  );
  if (status === "TIMEOUT") return (
    <div className="p-4 flex items-center gap-2 text-red-600 text-sm">
      <Clock className="w-4 h-4" />Time Limit Exceeded (2s). Check for infinite loops.
    </div>
  );
  if (status === "COMPILE_ERROR" || status === "ERROR") return (
    <div className="p-4 text-red-600 text-sm font-mono whitespace-pre-wrap">{error}</div>
  );
  const passed = results.filter(r => r.passed).length;
  return (
    <div className="p-3 space-y-2">
      <div className="text-sm font-medium mb-2">
        {passed === results.length
          ? <span className="text-green-600">All {passed}/{results.length} test cases passed ✓</span>
          : <span className="text-red-600">{passed}/{results.length} test cases passed</span>}
      </div>
      {results.map((r, i) => (
        <div key={i} className={cn("rounded-lg border p-3 text-xs font-mono", r.passed ? "bg-green-500/5 border-green-500/20" : "bg-red-500/5 border-red-500/20")}>
          <div className="flex items-center gap-2 mb-1">
            {r.passed ? <CheckCircle2 className="w-3.5 h-3.5 text-green-500" /> : <XCircle className="w-3.5 h-3.5 text-red-500" />}
            <span className="font-semibold">Case {i + 1}</span>
          </div>
          <div className="text-muted-foreground space-y-0.5">
            <div>Input: <span className="text-foreground">{r.input}</span></div>
            <div>Expected: <span className="text-foreground">{r.expected}</span></div>
            {!r.passed && <div>Got: <span className="text-red-500">{r.actual ?? r.error}</span></div>}
          </div>
        </div>
      ))}
      {stdout && (
        <div className="mt-2 text-xs text-muted-foreground">
          <div className="font-medium mb-1">Stdout:</div>
          <pre className="bg-muted rounded p-2 whitespace-pre-wrap">{stdout}</pre>
        </div>
      )}
    </div>
  );
}

// ─── Main Page ────────────────────────────────────────────────────────────────

export default function CodingAssessmentPage() {
  const router = useRouter();
  const { data: user } = useUser();
  const candidateId = user?.id;

  const startCoding = useStartCoding();
  const runCode = useRunCode();
  const submitSolution = useSubmitSolution();
  const finishCoding = useFinishCoding();

  const [attemptId, setAttemptId] = useState<number | null>(null);
  const [questions, setQuestions] = useState<CodingQuestion[]>([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [codes, setCodes] = useState<Record<number, string>>({});
  const [submittedQs, setSubmittedQs] = useState<Set<number>>(new Set());
  const [remainingSeconds, setRemainingSeconds] = useState(0);
  const [isInitializing, setIsInitializing] = useState(true);

  // Test panel state
  const [runStatus, setRunStatus] = useState<string | null>(null);
  const [runResults, setRunResults] = useState<TestCaseResult[]>([]);
  const [runError, setRunError] = useState<string | undefined>();
  const [runStdout, setRunStdout] = useState<string | undefined>();
  const [isRunning, setIsRunning] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const hasInit = useRef(false);
  const lastSavedCode = useRef<Record<number, string>>({});
  const autoSaveTimer = useRef<NodeJS.Timeout | null>(null);

  // Initialize
  useEffect(() => {
    if (!candidateId || hasInit.current) return;
    hasInit.current = true;
    const init = async () => {
      try {
        const res = await startCoding.mutateAsync();
        setAttemptId(res.attempt_id);
        setQuestions(res.questions);
        setRemainingSeconds(res.remaining_seconds);

        // Restore codes from backend (saved submissions)
        const codeMap: Record<number, string> = {};
        const submittedSet = new Set<number>();
        res.questions.forEach(q => {
          codeMap[q.question_id] = q.template;
          if (q.submitted) submittedSet.add(q.question_id);
        });
        setCodes(codeMap);
        setSubmittedQs(submittedSet);
        lastSavedCode.current = { ...codeMap };

        // Restore question index from localStorage
        const savedIdx = localStorage.getItem(`coding_q_${res.attempt_id}`);
        if (savedIdx) setCurrentIndex(Math.min(parseInt(savedIdx), res.questions.length - 1));
      } catch (err: any) {
        toast.error(err.response?.data?.detail || "Failed to load coding assessment.");
        router.replace("/assessments");
      } finally {
        setIsInitializing(false);
      }
    };
    init();
  }, [candidateId]); // eslint-disable-line

  // Timer
  useEffect(() => {
    if (remainingSeconds <= 0 || !attemptId) return;
    const iv = setInterval(() => {
      setRemainingSeconds(prev => {
        if (prev <= 1) { clearInterval(iv); handleFinish(true); return 0; }
        return prev - 1;
      });
    }, 1000);
    return () => clearInterval(iv);
  }, [remainingSeconds, attemptId]); // eslint-disable-line

  // Auto-save every 10 seconds
  useEffect(() => {
    autoSaveTimer.current = setInterval(async () => {
      if (!attemptId || !questions.length) return;
      const currentQ = questions[currentIndex];
      if (!currentQ) return;
      const qid = currentQ.question_id;
      const code = codes[qid];
      if (!code || code === lastSavedCode.current[qid]) return;
      try {
        await runCode.mutateAsync({ attempt_id: attemptId, question_id: qid, source_code: code, language: "python" });
        lastSavedCode.current[qid] = code;
      } catch {} // silent
    }, 10000);
    return () => { if (autoSaveTimer.current) clearInterval(autoSaveTimer.current); };
  }, [attemptId, currentIndex, codes, questions]); // eslint-disable-line

  // Save on question change
  const handleNavigate = async (newIndex: number) => {
    if (!attemptId || !questions.length) return;
    const currentQ = questions[currentIndex];
    if (currentQ) {
      const qid = currentQ.question_id;
      const code = codes[qid];
      if (code && code !== lastSavedCode.current[qid]) {
        try {
          await runCode.mutateAsync({ attempt_id: attemptId, question_id: qid, source_code: code, language: "python" });
          lastSavedCode.current[qid] = code;
        } catch {}
      }
    }
    setCurrentIndex(newIndex);
    if (attemptId) localStorage.setItem(`coding_q_${attemptId}`, String(newIndex));
    // Reset run panel
    setRunStatus(null); setRunResults([]); setRunError(undefined); setRunStdout(undefined);
  };

  const handleRun = async () => {
    if (!attemptId || !questions.length) return;
    const q = questions[currentIndex]!;
    const code = codes[q.question_id] || q.template;
    setIsRunning(true); setRunStatus(null);
    try {
      const res = await runCode.mutateAsync({ attempt_id: attemptId, question_id: q.question_id, source_code: code, language: "python" });
      lastSavedCode.current[q.question_id] = code;
      setRunStatus(res.status);
      setRunResults(res.results || []);
      setRunError(res.error);
      setRunStdout(res.stdout);
    } catch (err: any) {
      toast.error(err.response?.data?.detail || "Failed to run code.");
    } finally {
      setIsRunning(false);
    }
  };

  const handleSubmit = async () => {
    if (!attemptId || !questions.length) return;
    const q = questions[currentIndex]!;
    const code = codes[q.question_id] || q.template;
    setIsSubmitting(true);
    try {
      const res = await submitSolution.mutateAsync({ attempt_id: attemptId, question_id: q.question_id, source_code: code, language: "python" });
      setSubmittedQs(prev => new Set([...prev, q.question_id]));
      lastSavedCode.current[q.question_id] = code;
      toast.success(`Submitted! ${res.passed_test_cases}/${res.total_test_cases} test cases passed (${Math.round(res.score)}%)`);
      setRunStatus("SUCCESS"); setRunResults(res.results || []); setRunStdout(res.stdout);
    } catch (err: any) {
      toast.error(err.response?.data?.detail || "Failed to submit solution.");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleFinish = useCallback(async (auto = false) => {
    if (!attemptId) return;
    if (!auto && !confirm("Finish and submit all solutions?")) return;
    try {
      await finishCoding.mutateAsync(attemptId);
      if (document.fullscreenElement) document.exitFullscreen().catch(() => {});
      toast.success("Coding assessment submitted!");
      router.replace("/assessments");
    } catch (err: any) {
      toast.error(err.response?.data?.detail || "Failed to finish assessment.");
      router.replace("/assessments");
    }
  }, [attemptId, finishCoding, router]);

  const handleTerminated = useCallback(() => {
    toast.error("Assessment terminated due to integrity violation.");
    router.replace("/assessments");
  }, [router]);

  if (isInitializing) return (
    <div className="fixed inset-0 bg-background flex flex-col items-center justify-center z-50">
      <Loader2 className="w-10 h-10 animate-spin text-primary mb-4" />
      <h2 className="text-lg font-medium">Loading Coding Environment...</h2>
      <p className="text-sm text-muted-foreground mt-2">Preparing your 5 problems.</p>
    </div>
  );

  if (!questions.length || !attemptId) return null;

  const q = questions[currentIndex]!;
  const currentCode = codes[q.question_id] ?? q.template;
  const isSubmitted = submittedQs.has(q.question_id);
  const isLowTime = remainingSeconds < 600;

  return (
    <div className="fixed inset-0 bg-background z-50 flex flex-col">
      {/* Proctoring */}
      <ProctoringMonitor candidateId={candidateId!} assessmentType="CODING" onTerminated={handleTerminated} />

      {/* ── Top Bar ── */}
      <header className="h-14 bg-background border-b flex items-center justify-between px-4 shrink-0 shadow-sm">
        <div className="flex items-center gap-2">
          <div className="bg-primary/10 text-primary p-1.5 rounded-md">
            <Code2 className="w-4 h-4" />
          </div>
          <span className="font-bold text-sm">AIHire Coding Assessment</span>
        </div>

        <div className="flex items-center gap-3">
          {/* Timer */}
          <div className={cn("flex items-center gap-1.5 px-3 py-1.5 rounded-lg border font-mono text-sm font-semibold", isLowTime ? "border-red-500/40 bg-red-500/10 text-red-600" : "bg-muted/50 text-foreground")}>
            <Clock className={cn("w-4 h-4", isLowTime && "animate-pulse")} />
            {formatTime(remainingSeconds)}
          </div>
          {/* Q navigator */}
          <div className="flex items-center gap-1">
            {questions.map((qitem, idx) => (
              <button
                key={qitem.question_id}
                onClick={() => handleNavigate(idx)}
                className={cn(
                  "w-8 h-8 rounded-md text-xs font-semibold transition-all",
                  idx === currentIndex ? "ring-2 ring-primary ring-offset-1 bg-primary text-primary-foreground" :
                    submittedQs.has(qitem.question_id) ? "bg-green-500/20 text-green-700 border border-green-500/30" :
                    "bg-muted hover:bg-muted/80"
                )}
              >
                {idx + 1}
              </button>
            ))}
          </div>
          <Button size="sm" variant="destructive" onClick={() => handleFinish(false)}>
            Finish & Submit
          </Button>
        </div>
      </header>

      {/* ── Main split layout ── */}
      <div className="flex flex-1 overflow-hidden">

        {/* ── LEFT: Problem Panel ── */}
        <div className="w-[420px] shrink-0 border-r flex flex-col overflow-y-auto bg-muted/10">
          <div className="p-5">
            {/* Title row */}
            <div className="flex items-start justify-between gap-2 mb-3">
              <h2 className="font-bold text-base leading-tight">{q.title}</h2>
              <Badge variant="outline" className={cn("text-xs shrink-0 border", DIFFICULTY_COLOR[q.difficulty])}>
                {q.difficulty}
              </Badge>
            </div>

            {isSubmitted && (
              <div className="flex items-center gap-2 text-green-600 text-xs bg-green-500/10 border border-green-500/20 px-3 py-2 rounded-lg mb-3">
                <CheckCircle2 className="w-3.5 h-3.5" />
                Solution submitted
              </div>
            )}

            {/* Problem */}
            <div className="prose prose-sm dark:prose-invert max-w-none">
              <h4 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-1.5">Problem</h4>
              <p className="text-sm leading-relaxed whitespace-pre-wrap">{q.problem_statement}</p>

              {q.constraints && (
                <>
                  <h4 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground mt-4 mb-1.5">Constraints</h4>
                  <pre className="text-xs bg-muted rounded-lg p-3 whitespace-pre-wrap font-mono">{q.constraints}</pre>
                </>
              )}

              <h4 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground mt-4 mb-1.5">Example</h4>
              <div className="bg-muted rounded-lg p-3 space-y-1.5 text-xs font-mono">
                <div><span className="text-muted-foreground">Input:</span>  {q.sample_input}</div>
                <div><span className="text-muted-foreground">Output:</span> {q.sample_output}</div>
              </div>
            </div>
          </div>
        </div>

        {/* ── RIGHT: Editor + Console ── */}
        <div className="flex-1 flex flex-col overflow-hidden">
          {/* Editor toolbar */}
          <div className="h-10 bg-zinc-900 border-b border-zinc-700 flex items-center justify-between px-3 shrink-0">
            <div className="flex items-center gap-2 text-xs text-zinc-400">
              <Code2 className="w-3.5 h-3.5" />
              <span>Python 3</span>
              {isSubmitted && <span className="text-green-400 flex items-center gap-1"><CheckCircle2 className="w-3 h-3" />Submitted</span>}
            </div>
            <div className="flex items-center gap-2">
              <Button
                size="sm" variant="ghost"
                className="h-7 text-xs text-zinc-300 hover:text-white hover:bg-zinc-700 gap-1.5"
                onClick={handleRun} disabled={isRunning || isSubmitted}
              >
                <Play className="w-3 h-3" />Run
              </Button>
              <Button
                size="sm"
                className="h-7 text-xs bg-green-600 hover:bg-green-700 text-white gap-1.5"
                onClick={handleSubmit} disabled={isSubmitting || isSubmitted}
              >
                {isSubmitting ? <Loader2 className="w-3 h-3 animate-spin" /> : <Send className="w-3 h-3" />}
                Submit
              </Button>
            </div>
          </div>

          {/* Monaco Editor */}
          <div className="flex-1 overflow-hidden">
            <MonacoEditor
              height="100%"
              language="python"
              theme="vs-dark"
              value={currentCode}
              onChange={(val) => {
                if (!isSubmitted) {
                  setCodes(prev => ({ ...prev, [q.question_id]: val ?? "" }));
                }
              }}
              options={{
                fontSize: 13,
                lineNumbers: "on",
                minimap: { enabled: false },
                scrollBeyondLastLine: false,
                automaticLayout: true,
                tabSize: 4,
                readOnly: isSubmitted,
                wordWrap: "on",
                padding: { top: 12 },
                fontFamily: "'JetBrains Mono', 'Fira Code', Consolas, monospace",
              }}
            />
          </div>

          {/* Console / Results Panel */}
          <div className="h-44 border-t bg-background overflow-y-auto shrink-0">
            <div className="flex items-center gap-2 px-3 py-2 border-b text-xs font-medium text-muted-foreground bg-muted/20">
              <AlertCircle className="w-3.5 h-3.5" />Console
            </div>
            <TestPanel
              status={runStatus}
              results={runResults}
              error={runError}
              stdout={runStdout}
              isRunning={isRunning}
            />
          </div>
        </div>
      </div>
    </div>
  );
}
