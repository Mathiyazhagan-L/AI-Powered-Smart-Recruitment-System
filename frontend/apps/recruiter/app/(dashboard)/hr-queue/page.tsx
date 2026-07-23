"use client";

import { useState } from "react";
import Link from "next/link";
import { Search, Filter, Check, X, Clock, BrainCircuit, FileCode2, ChevronRight, ChevronLeft } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { useHRQueue, useUpdateHRReviewStatus, HRReview } from "@/lib/hooks/useHRQueue";
import ScheduleInterviewModal from "@/components/ScheduleInterviewModal";

export default function HRQueuePage() {
  const { data: queue, isLoading } = useHRQueue();
  const updateStatus = useUpdateHRReviewStatus();
  const [selectedCandidate, setSelectedCandidate] = useState<HRReview | null>(null);
  const [notes, setNotes] = useState("");

  const activeQueue = queue || [];
  
  // Set first candidate automatically if none selected and queue loads
  if (!selectedCandidate && activeQueue.length > 0) {
    setSelectedCandidate(activeQueue[0] || null);
  }

  const handleStatusUpdate = (status: string) => {
    if (!selectedCandidate) return;
    updateStatus.mutate({ id: selectedCandidate.id, status, notes }, {
      onSuccess: () => {
        setNotes("");
        // Optimistically we can just let React Query refetch
      }
    });
  };

  return (
    <div className="flex flex-col h-full space-y-4">
      {/* Sticky Header */}
      <div className="sticky top-0 z-10 bg-muted/20 backdrop-blur-md pb-4 border-b border-border/50 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h2 className="text-3xl font-bold tracking-tight text-foreground">HR Review Queue</h2>
          <p className="text-muted-foreground mt-1">Review top candidates highlighted by the ATS.</p>
        </div>
        <div className="flex space-x-2">
          <Badge variant="secondary" className="px-3 py-1 text-sm bg-warning/20 text-warning hover:bg-warning/30 border-warning/30">
            {activeQueue.length} Pending
          </Badge>
        </div>
      </div>

      <div className="flex flex-1 overflow-hidden gap-6">
        {/* Left Pane: Queue List */}
        <div className="w-1/3 flex flex-col border rounded-lg bg-background shadow-sm overflow-hidden">
          <div className="p-3 border-b bg-muted/30">
            <div className="relative">
              <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
              <Input placeholder="Search queue..." className="pl-9 bg-background w-full" />
            </div>
          </div>
          <div className="flex-1 overflow-y-auto">
            {isLoading ? (
              <div className="p-8 text-center text-muted-foreground flex flex-col items-center">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mb-2"></div>
                <p>Loading queue...</p>
              </div>
            ) : activeQueue.length === 0 ? (
              <div className="p-8 text-center text-muted-foreground">
                <p>No candidates in the HR queue.</p>
              </div>
            ) : (
              activeQueue.map((c) => (
                <div 
                  key={c.id} 
                  onClick={() => setSelectedCandidate(c)}
                  className={`p-4 border-b cursor-pointer transition-colors hover:bg-muted/50 ${selectedCandidate?.id === c.id ? 'bg-primary/5 border-l-4 border-l-primary' : 'border-l-4 border-l-transparent'}`}
                >
                  <div className="flex justify-between items-start mb-1">
                    <h4 className="font-semibold text-sm">{c.candidate_name || `Candidate #${c.candidate_id}`}</h4>
                    <span className="text-xs text-muted-foreground">{c.status}</span>
                  </div>
                  <p className="text-xs text-muted-foreground mb-3">{c.job_title || `Job #${c.job_id}`}</p>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Right Pane: Review Workspace */}
        <div className="flex-1 border rounded-lg bg-background shadow-sm flex flex-col overflow-hidden">
          {!selectedCandidate ? (
            <div className="flex-1 flex items-center justify-center text-muted-foreground">
              Select a candidate from the queue to review
            </div>
          ) : (
            <>
          <div className="p-6 border-b flex justify-between items-start bg-muted/10">
            <div className="flex items-center space-x-4">
              <Avatar className="h-16 w-16 border-2 border-border">
                <AvatarFallback className="text-xl bg-primary/10 text-primary">{(selectedCandidate.candidate_name || "C")[0]}</AvatarFallback>
              </Avatar>
              <div>
                <h3 className="text-2xl font-bold">{selectedCandidate.candidate_name || `Candidate #${selectedCandidate.candidate_id}`}</h3>
                <p className="text-muted-foreground flex items-center mt-1">
                  {selectedCandidate.job_title || `Job #${selectedCandidate.job_id}`}
                </p>
              </div>
            </div>
            <div className="flex space-x-2 items-center">
              {selectedCandidate.status === "Approved" && (
                <div className="mr-4">
                  <ScheduleInterviewModal 
                    jobId={selectedCandidate.job_id}
                    candidateId={selectedCandidate.candidate_id}
                    candidateName={selectedCandidate.candidate_name || `Candidate #${selectedCandidate.candidate_id}`}
                    triggerElement={
                      <Button variant="default" className="bg-primary text-primary-foreground hover:bg-primary/90">
                        Schedule HR Interview
                      </Button>
                    }
                  />
                </div>
              )}
              
              <Button 
                onClick={() => handleStatusUpdate("Approved")} 
                disabled={updateStatus.isPending || selectedCandidate.status === "Approved" || selectedCandidate.status === "Rejected"} 
                className={selectedCandidate.status === "Approved" ? "bg-success text-success-foreground cursor-not-allowed opacity-80" : "bg-success/10 text-success hover:bg-success hover:text-success-foreground border-transparent"}
                variant={selectedCandidate.status === "Approved" ? "default" : "outline"}
              >
                <Check className="mr-2 h-4 w-4" /> {selectedCandidate.status === "Approved" ? "Approved" : "Approve"}
              </Button>
              <Button 
                onClick={() => handleStatusUpdate("On Hold")} 
                disabled={updateStatus.isPending || selectedCandidate.status === "On Hold" || selectedCandidate.status === "Approved" || selectedCandidate.status === "Rejected"} 
                className={selectedCandidate.status === "On Hold" ? "bg-warning text-warning-foreground cursor-not-allowed opacity-80" : "bg-warning/10 text-warning hover:bg-warning hover:text-warning-foreground border-transparent"}
                variant={selectedCandidate.status === "On Hold" ? "default" : "outline"}
              >
                <Clock className="mr-2 h-4 w-4" /> {selectedCandidate.status === "On Hold" ? "On Hold" : "Hold"}
              </Button>
              <Button 
                onClick={() => handleStatusUpdate("Rejected")} 
                disabled={updateStatus.isPending || selectedCandidate.status === "Rejected" || selectedCandidate.status === "Approved"} 
                className={selectedCandidate.status === "Rejected" ? "bg-destructive text-destructive-foreground cursor-not-allowed opacity-80" : "bg-destructive/10 text-destructive hover:bg-destructive hover:text-destructive-foreground border-transparent"}
                variant={selectedCandidate.status === "Rejected" ? "default" : "outline"}
              >
                <X className="mr-2 h-4 w-4" /> {selectedCandidate.status === "Rejected" ? "Rejected" : "Reject"}
              </Button>
            </div>
          </div>
          
          <div className="flex-1 overflow-y-auto p-6">
            <div className="grid grid-cols-2 gap-6">
              <Card className="shadow-none border-border/50 bg-muted/20">
                <CardHeader className="pb-3">
                  <CardTitle className="text-sm font-medium flex items-center text-muted-foreground">
                    <BrainCircuit className="mr-2 h-4 w-4" /> ATS Summary
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-3xl font-bold text-foreground mb-2">{selectedCandidate.ats}/100</div>
                  <p className="text-sm text-muted-foreground">
                    Strong match for requirements. Extensive experience with Python, SQL, and Machine Learning frameworks.
                  </p>
                </CardContent>
              </Card>
              <Card className="shadow-none border-border/50 bg-muted/20">
                <CardHeader className="pb-3">
                  <CardTitle className="text-sm font-medium flex items-center text-muted-foreground">
                    <FileCode2 className="mr-2 h-4 w-4" /> Tech Assessment
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-3xl font-bold text-foreground mb-2">{selectedCandidate.tech}/100</div>
                  <p className="text-sm text-muted-foreground">
                    Exceptional algorithmic skills. Completed the Data Engineering challenge 15 minutes early.
                  </p>
                </CardContent>
              </Card>
            </div>

            <Separator className="my-8" />

            <div>
              <h4 className="font-semibold text-lg mb-4">HR Notes</h4>
              <textarea 
                className="w-full h-32 p-3 border rounded-md bg-background resize-none focus:outline-none focus:ring-1 focus:ring-primary/50"
                placeholder="Add review notes here before deciding..."
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
              ></textarea>
            </div>
          </div>
          </>
          )}
        </div>
      </div>
    </div>
  );
}
