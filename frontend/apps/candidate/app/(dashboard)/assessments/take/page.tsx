"use client";

import React, { useState, useEffect, useCallback, useRef } from "react";
import { useRouter } from "next/navigation";
import { useUser } from "@/lib/hooks/useAuth";
import { useStartAssessment, useSaveAnswer, useSubmitAssessment, AssessmentStartResponse, AssessmentQuestion } from "@/lib/hooks/useAssessment";
import { useStartProctoring, useStopProctoring } from "@/lib/hooks/useProctoring";
import ProctoringMonitor from "@/components/assessment/ProctoringMonitor";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { Label } from "@/components/ui/label";
import { Loader2, Clock, CheckCircle2, Circle, AlertCircle, ShieldCheck } from "lucide-react";
import { toast } from "sonner";

export default function AssessmentTakePage() {
  const router = useRouter();
  const { data: user } = useUser();
  const candidateId = user?.id;

  const startAssessment = useStartAssessment();
  const saveAnswer = useSaveAnswer();
  const submitAssessment = useSubmitAssessment();
  const startProctoring = useStartProctoring();
  const stopProctoring = useStopProctoring();

  const [assessmentState, setAssessmentState] = useState<AssessmentStartResponse | null>(null);
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [remainingSeconds, setRemainingSeconds] = useState(0);
  const [isInitializing, setIsInitializing] = useState(true);
  const hasInitialized = useRef(false);

  // Load Assessment State
  useEffect(() => {
    if (!candidateId || hasInitialized.current) return;
    hasInitialized.current = true;

    const init = async () => {
      try {
        await startProctoring.mutateAsync({ candidate_id: candidateId, assessment_type: "APTITUDE" });
        const res = await startAssessment.mutateAsync();
        setAssessmentState(res);
        setRemainingSeconds(res.remaining_seconds);
      } catch (err: any) {
        console.error("Assessment start error:", err);
        toast.error(err.response?.data?.detail || err.message || "Failed to start assessment.");
        router.replace("/assessments");
      } finally {
        setIsInitializing(false);
      }
    };

    init();
  }, [candidateId, router]);

  // Timer logic
  useEffect(() => {
    if (!assessmentState || remainingSeconds <= 0) return;

    const interval = setInterval(() => {
      setRemainingSeconds((prev) => {
        if (prev <= 1) {
          clearInterval(interval);
          handleAutoSubmit();
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(interval);
  }, [assessmentState, remainingSeconds]);

  const handleAutoSubmit = useCallback(async () => {
    if (!assessmentState || !candidateId) return;
    toast.info("Time is up! Auto-submitting your assessment.");
    
    // Construct answers
    const answers = assessmentState.questions.map(q => ({
      question_id: q.question_id,
      selected_answer: q.selected_answer || null
    }));

    try {
      await stopProctoring.mutateAsync({ candidate_id: candidateId, assessment_type: "APTITUDE" });
      await submitAssessment.mutateAsync({ attempt_id: assessmentState.attempt_id, answers });
      router.replace("/assessments");
    } catch (e) {
      toast.error("Failed to auto-submit.");
      router.replace("/assessments");
    }
  }, [assessmentState, candidateId, stopProctoring, submitAssessment, router]);

  const handleTerminated = useCallback(async () => {
    toast.error("Assessment terminated due to integrity violation.");
    if (document.fullscreenElement) {
      document.exitFullscreen().catch(e => console.log(e));
    }
    router.replace("/assessments");
  }, [router]);

  const handleManualSubmit = async () => {
    if (!assessmentState || !candidateId) return;
    if (confirm("Are you sure you want to finish and submit your assessment?")) {
      const answers = assessmentState.questions.map(q => ({
        question_id: q.question_id,
        selected_answer: q.selected_answer || null
      }));

      try {
        await stopProctoring.mutateAsync({ candidate_id: candidateId, assessment_type: "APTITUDE" });
        await submitAssessment.mutateAsync({ attempt_id: assessmentState.attempt_id, answers });
        
        if (document.fullscreenElement) {
          document.exitFullscreen().catch(e => console.log(e));
        }
        
        toast.success("Assessment submitted successfully.");
        router.replace("/assessments");
      } catch (e: any) {
        toast.error(e.response?.data?.detail || "Failed to submit.");
      }
    }
  };

  const handleOptionSelect = async (questionId: number, value: string) => {
    if (!assessmentState) return;

    // Optimistically update state
    const newQuestions = [...assessmentState.questions];
    const qIndex = newQuestions.findIndex(q => q.question_id === questionId);
    if (qIndex > -1) {
      const targetQ = newQuestions[qIndex];
      if (targetQ) {
        targetQ.selected_answer = value;
        setAssessmentState({ ...assessmentState, questions: newQuestions });
      }
    }

    // Auto-save
    try {
      await saveAnswer.mutateAsync({
        attempt_id: assessmentState.attempt_id,
        question_id: questionId,
        selected_answer: value
      });
    } catch (e) {
      toast.error("Failed to save answer. Please check your connection.");
    }
  };

  const formatTime = (seconds: number) => {
    const m = Math.floor(seconds / 60).toString().padStart(2, "0");
    const s = (seconds % 60).toString().padStart(2, "0");
    return `${m}:${s}`;
  };

  if (isInitializing) {
    return (
      <div className="fixed inset-0 bg-background flex flex-col items-center justify-center z-50">
        <Loader2 className="w-10 h-10 animate-spin text-primary mb-4" />
        <h2 className="text-lg font-medium">Initializing Secure Environment...</h2>
        <p className="text-sm text-muted-foreground mt-2">Checking camera and setting up session.</p>
      </div>
    );
  }

  if (!assessmentState || !candidateId) {
    return null; // Will redirect shortly
  }

  const currentQuestion = assessmentState.questions[currentQuestionIndex];
  if (!currentQuestion) {
    return null;
  }
  const isLastQuestion = currentQuestionIndex === assessmentState.questions.length - 1;

  return (
    <div className="fixed inset-0 bg-muted/20 z-50 flex flex-col">
      {/* Hidden top-level tracker */}
      <ProctoringMonitor 
        candidateId={candidateId} 
        assessmentType="APTITUDE" 
        onTerminated={handleTerminated} 
      />

      {/* TOP BAR */}
      <header className="bg-background border-b px-6 py-4 flex items-center justify-between shrink-0 shadow-sm">
        <div className="flex items-center gap-2">
          <div className="bg-primary/10 text-primary p-1.5 rounded-md">
            <ShieldCheck className="w-5 h-5" />
          </div>
          <h1 className="font-bold tracking-tight">AIHire Aptitude Assessment</h1>
        </div>
        
        <div className="flex items-center gap-6">
          <div className="flex items-center gap-2 bg-muted/50 px-4 py-2 rounded-lg border font-mono text-lg font-semibold tracking-wider">
            <Clock className={`w-5 h-5 ${remainingSeconds < 300 ? "text-destructive animate-pulse" : "text-muted-foreground"}`} />
            <span className={remainingSeconds < 300 ? "text-destructive" : "text-foreground"}>
              {formatTime(remainingSeconds)}
            </span>
          </div>
          <Button variant="destructive" onClick={handleManualSubmit}>
            Finish & Submit
          </Button>
        </div>
      </header>

      <div className="flex flex-1 overflow-hidden">
        {/* MAIN QUESTION AREA */}
        <main className="flex-1 overflow-y-auto p-8">
          <div className="max-w-3xl mx-auto">
            <div className="mb-6 flex justify-between items-center text-sm font-medium text-muted-foreground">
              <span>Question {currentQuestionIndex + 1} of {assessmentState.questions.length}</span>
              <span className="uppercase tracking-wider px-2.5 py-1 bg-muted rounded-md">{currentQuestion.category}</span>
            </div>

            <Card className="border-2 shadow-sm">
              <CardContent className="p-8">
                <h2 className="text-xl font-medium leading-relaxed mb-8 whitespace-pre-wrap">
                  {currentQuestion.question}
                </h2>

                <RadioGroup 
                  value={currentQuestion.selected_answer || ""} 
                  onValueChange={(val) => handleOptionSelect(currentQuestion.question_id, val)}
                  className="space-y-3"
                >
                  {(["A", "B", "C", "D"] as const).map((opt) => (
                    currentQuestion.options[opt] && (
                      <div key={opt} className="flex items-center">
                        <RadioGroupItem value={opt} id={`option-${opt}`} className="peer sr-only" />
                        <Label
                          htmlFor={`option-${opt}`}
                          className="flex flex-1 items-center justify-between rounded-xl border-2 border-muted bg-transparent p-4 hover:bg-muted hover:text-accent-foreground peer-data-[state=checked]:border-primary peer-data-[state=checked]:bg-primary/5 cursor-pointer transition-all"
                        >
                          <div className="flex items-start gap-4">
                            <div className="flex items-center justify-center w-6 h-6 rounded border font-semibold text-xs shrink-0 peer-data-[state=checked]:bg-primary peer-data-[state=checked]:text-primary-foreground peer-data-[state=checked]:border-primary">
                              {opt}
                            </div>
                            <span className="text-sm sm:text-base leading-tight mt-0.5">{currentQuestion.options[opt]}</span>
                          </div>
                        </Label>
                      </div>
                    )
                  ))}
                </RadioGroup>
              </CardContent>
            </Card>

            <div className="flex justify-between mt-8">
              <Button 
                variant="outline" 
                disabled={currentQuestionIndex === 0}
                onClick={() => setCurrentQuestionIndex(prev => prev - 1)}
              >
                Previous
              </Button>
              {isLastQuestion ? (
                <Button 
                  className="bg-primary hover:bg-primary/95 text-primary-foreground font-semibold"
                  onClick={handleManualSubmit}
                >
                  Finish & Submit
                </Button>
              ) : (
                <Button 
                  onClick={() => setCurrentQuestionIndex(prev => prev + 1)}
                >
                  Next
                </Button>
              )}
            </div>
          </div>
        </main>

        {/* SIDEBAR NAVIGATION */}
        <aside className="w-80 bg-background border-l shrink-0 flex flex-col shadow-sm">
          <div className="p-4 border-b">
            <h3 className="font-semibold text-sm">Question Palette</h3>
            <div className="flex gap-4 mt-3 text-xs">
              <div className="flex items-center gap-1"><div className="w-3 h-3 bg-primary rounded-sm"></div> Answered</div>
              <div className="flex items-center gap-1"><div className="w-3 h-3 bg-muted rounded-sm border"></div> Unanswered</div>
            </div>
          </div>
          
          <div className="p-4 flex-1 overflow-y-auto">
            <div className="grid grid-cols-5 gap-2">
              {assessmentState.questions.map((q, idx) => {
                const isCurrent = idx === currentQuestionIndex;
                const isAnswered = !!q.selected_answer;
                
                return (
                  <button
                    key={q.question_id}
                    onClick={() => setCurrentQuestionIndex(idx)}
                    className={`
                      h-10 rounded-md text-sm font-medium transition-colors
                      ${isCurrent ? "ring-2 ring-primary ring-offset-2" : ""}
                      ${isAnswered ? "bg-primary text-primary-foreground hover:bg-primary/90" : "bg-muted border hover:bg-muted/80 text-foreground"}
                    `}
                  >
                    {idx + 1}
                  </button>
                )
              })}
            </div>
          </div>

          <div className="p-4 bg-muted/20 border-t mt-auto text-xs text-muted-foreground flex items-start gap-2">
            <AlertCircle className="w-4 h-4 shrink-0 text-amber-500" />
            <p>Your actions are monitored. Navigating away from this screen will result in an integrity violation.</p>
          </div>
        </aside>
      </div>
    </div>
  );
}
