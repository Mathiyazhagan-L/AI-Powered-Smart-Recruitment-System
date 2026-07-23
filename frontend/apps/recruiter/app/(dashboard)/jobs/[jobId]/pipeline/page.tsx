"use client";
import { apiClient } from "@/lib/apiClient";

import React, { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import { DndContext, DragOverlay, closestCorners, KeyboardSensor, PointerSensor, useSensor, useSensors, DragStartEvent, DragEndEvent } from "@dnd-kit/core";
import { SortableContext, arrayMove, sortableKeyboardCoordinates, verticalListSortingStrategy } from "@dnd-kit/sortable";
import { ArrowLeft, Users, AlertCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { useSortable } from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";

// Define the stages
const STAGES = [
  "Applied",
  "Resume Screening",
  "Aptitude Test",
  "Coding Challenge",
  "Interview",
  "HR Review",
  "Offer Released",
  "Rejected"
];

// Sortable Item Component (Candidate Card)
function SortableCandidateCard({ candidate }: { candidate: any }) {
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } = useSortable({ id: candidate.candidate_id });
  
  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.4 : 1,
  };

  return (
    <div
      ref={setNodeRef}
      style={style}
      {...attributes}
      {...listeners}
      className="bg-card border border-border rounded-lg p-3 mb-2 shadow-sm cursor-grab active:cursor-grabbing hover:border-primary/50 transition-colors"
    >
      <div className="font-semibold text-sm mb-1">{candidate.candidate_name || `Candidate #${candidate.candidate_id}`}</div>
      <div className="flex items-center gap-2 mb-2">
        <Badge variant="outline" className="text-[10px] py-0">Score: {candidate.overall_score ? Math.round(candidate.overall_score) : 'N/A'}</Badge>
        {candidate.integrity_score && candidate.integrity_score < 70 && (
          <Badge variant="destructive" className="text-[10px] py-0"><AlertCircle className="w-3 h-3 mr-1" />Review</Badge>
        )}
      </div>
      <div className="text-xs text-muted-foreground flex justify-between">
        <span>ATS: {candidate.ats_score || 0}</span>
        <span>Apt: {candidate.aptitude_score || 0}</span>
      </div>
    </div>
  );
}

// Column Component
function PipelineColumn({ id, title, candidates }: { id: string; title: string; candidates: any[] }) {
  return (
    <div className="flex flex-col bg-muted/20 border border-border rounded-xl w-[280px] min-w-[280px] h-[calc(100vh-200px)] overflow-hidden">
      <div className="p-3 border-b bg-muted/40 font-semibold flex items-center justify-between">
        <span>{title}</span>
        <Badge variant="secondary" className="text-xs">{candidates.length}</Badge>
      </div>
      <div className="flex-1 overflow-y-auto p-2">
        <SortableContext id={id} items={candidates.map(c => c.candidate_id)} strategy={verticalListSortingStrategy}>
          {candidates.map((cand) => (
            <SortableCandidateCard key={cand.candidate_id} candidate={cand} />
          ))}
          {candidates.length === 0 && (
            <div className="h-full w-full border-2 border-dashed border-border/50 rounded-lg flex items-center justify-center text-muted-foreground text-sm p-4 text-center">
              Drop candidates here
            </div>
          )}
        </SortableContext>
      </div>
    </div>
  );
}

export default function PipelinePage() {
  const params = useParams();
  const router = useRouter();
  const jobId = params.jobId as string;
  
  const [candidates, setCandidates] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeId, setActiveId] = useState<string | null>(null);

  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 5 } }),
    useSensor(KeyboardSensor, { coordinateGetter: sortableKeyboardCoordinates })
  );

  useEffect(() => {
    // We can fetch rankings to get all candidates and their current stages
    apiClient.get(`/ranking/job/${jobId}`)
      .then(res => {
        setCandidates(res.data);
        setLoading(false);
      })
      .catch(err => {
        console.error(err);
        setLoading(false);
      });
  }, [jobId]);

  const handleDragStart = (event: DragStartEvent) => {
    setActiveId(event.active.id as string);
  };

  const handleDragOver = (event: any) => {
    const { active, over } = event;
    if (!over) return;

    const activeId = active.id;
    const overId = over.id;

    if (activeId === overId) return;

    // Find the containers
    const activeCandidate = candidates.find(c => c.candidate_id === activeId);
    if (!activeCandidate) return;

    const activeContainer = activeCandidate.current_stage;
    
    // Check if over a column or another item
    const isOverAColumn = STAGES.includes(overId);
    const overCandidate = candidates.find(c => c.candidate_id === overId);
    const overContainer = isOverAColumn ? overId : (overCandidate?.current_stage || "Applied");

    if (activeContainer === overContainer) return;

    // Optimistic update
    setCandidates((prev) => {
      const activeItems = prev.filter(c => c.current_stage === activeContainer);
      const overItems = prev.filter(c => c.current_stage === overContainer);
      const activeIndex = activeItems.findIndex(c => c.candidate_id === activeId);
      const overIndex = isOverAColumn ? overItems.length : overItems.findIndex(c => c.candidate_id === overId);

      let newIndex;
      if (isOverAColumn) {
        newIndex = overItems.length + 1;
      } else {
        const isBelowOverItem =
          over &&
          active.rect.current.translated &&
          active.rect.current.translated.top > over.rect.top + over.rect.height;
        const modifier = isBelowOverItem ? 1 : 0;
        newIndex = overIndex >= 0 ? overIndex + modifier : overItems.length + 1;
      }

      return prev.map(c => {
        if (c.candidate_id === activeId) {
          return { ...c, current_stage: overContainer };
        }
        return c;
      });
    });
  };

  const handleDragEnd = async (event: DragEndEvent) => {
    setActiveId(null);
    const { active, over } = event;
    if (!over) return;

    const candidateId = active.id;
    const activeCandidate = candidates.find(c => c.candidate_id === candidateId);
    if (!activeCandidate) return;

    const newStage = activeCandidate.current_stage;

    // Call API to update the candidate's stage in the database
    try {
      await apiClient.put(`/recruiter-workspace/pipeline/job/${jobId}/candidate/${candidateId}/stage`, { stage: newStage });
    } catch (e) {
      console.error("Failed to update status", e);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>
    );
  }

  const activeCandidateData = candidates.find(c => c.candidate_id === activeId);

  return (
    <div className="flex flex-col space-y-4 h-[calc(100vh-80px)]">
      <div className="flex items-center justify-between border-b pb-4 shrink-0">
        <div className="flex items-center space-x-4">
          <Button variant="ghost" size="icon" onClick={() => router.push("/jobs")}>
            <ArrowLeft className="h-5 w-5" />
          </Button>
          <div>
            <h1 className="text-2xl font-bold flex items-center gap-2">
              <Users className="h-6 w-6 text-primary" /> Hiring Pipeline
            </h1>
            <p className="text-muted-foreground text-sm">Drag and drop candidates across stages for Job #{jobId}</p>
          </div>
        </div>
        <Button onClick={() => router.push(`/jobs/${jobId}/recommendations`)} variant="outline">
          AI Recommendations
        </Button>
      </div>

      <div className="flex-1 overflow-x-auto overflow-y-hidden pb-4">
        <div className="flex gap-4 h-full px-2">
          <DndContext
            sensors={sensors}
            collisionDetection={closestCorners}
            onDragStart={handleDragStart}
            onDragOver={handleDragOver}
            onDragEnd={handleDragEnd}
          >
            {STAGES.map(stage => (
              <PipelineColumn
                key={stage}
                id={stage}
                title={stage}
                candidates={candidates.filter(c => c.current_stage === stage)}
              />
            ))}
            <DragOverlay>
              {activeId && activeCandidateData ? (
                <div className="opacity-80 rotate-3">
                  <SortableCandidateCard candidate={activeCandidateData} />
                </div>
              ) : null}
            </DragOverlay>
          </DndContext>
        </div>
      </div>
    </div>
  );
}
