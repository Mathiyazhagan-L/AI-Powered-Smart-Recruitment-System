"use client";

import React, { useState } from "react";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogTrigger } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";

import { useScheduleInterview } from "@/lib/hooks/useInterviews";
import { useUser } from "@/lib/hooks/useAuth";

interface ScheduleInterviewModalProps {
  jobId: number;
  candidateId: number;
  candidateName: string;
  triggerElement?: React.ReactNode;
}

export default function ScheduleInterviewModal({ jobId, candidateId, candidateName, triggerElement }: ScheduleInterviewModalProps) {
  const [open, setOpen] = useState(false);
  const [date, setDate] = useState("");
  const [time, setTime] = useState("");
  const [duration, setDuration] = useState("45");
  const [interviewType, setInterviewType] = useState("Technical");
  const [meetingLink, setMeetingLink] = useState("");
  const [notes, setNotes] = useState("");

  const { data: user } = useUser();
  const scheduleMutation = useScheduleInterview();

  const handleSchedule = () => {
    if (!date || !time) return;

    scheduleMutation.mutate({
      job_id: jobId,
      candidate_id: candidateId,
      recruiter_id: user?.id || 1,
      interview_title: `${interviewType} Interview`,
      interview_mode: "Online",
      interview_date: date,
      interview_time: time,
      duration_minutes: parseInt(duration),
      meeting_link: meetingLink,
      interview_notes: notes
    }, {
      onSuccess: () => {
        setOpen(false);
        alert("Interview successfully scheduled and candidate notified!");
      },
      onError: (err: any) => {
        alert("Failed to schedule interview: " + (err.response?.data?.detail || err.message));
      }
    });
  };

  return (
    <>
      <div onClick={() => setOpen(true)} className="inline-block cursor-pointer">
        {triggerElement || <Button>Schedule Interview</Button>}
      </div>
      <Dialog open={open} onOpenChange={setOpen}>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle>Schedule Interview for {candidateName}</DialogTitle>
        </DialogHeader>
        <div className="grid gap-4 py-4">
          <div className="grid grid-cols-4 items-center gap-4">
            <Label className="text-right">Type</Label>
            <select 
              value={interviewType} 
              onChange={e => setInterviewType(e.target.value)} 
              className="col-span-3 flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-sm transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
            >
              <option value="HR">HR Screen</option>
              <option value="Technical">Technical</option>
              <option value="Behavioral">Behavioral</option>
              <option value="Final">Final</option>
            </select>
          </div>
          <div className="grid grid-cols-4 items-center gap-4">
            <Label className="text-right">Date</Label>
            <Input type="date" value={date} onChange={e => setDate(e.target.value)} className="col-span-3" />
          </div>
          <div className="grid grid-cols-4 items-center gap-4">
            <Label className="text-right">Time</Label>
            <Input type="time" value={time} onChange={e => setTime(e.target.value)} className="col-span-3" />
          </div>
          <div className="grid grid-cols-4 items-center gap-4">
            <Label className="text-right">Duration (min)</Label>
            <Input type="number" value={duration} onChange={e => setDuration(e.target.value)} className="col-span-3" />
          </div>
          <div className="grid grid-cols-4 items-center gap-4">
            <Label className="text-right">Meet Link</Label>
            <Input type="url" placeholder="https://meet.google.com/..." value={meetingLink} onChange={e => setMeetingLink(e.target.value)} className="col-span-3" />
          </div>
          <div className="grid grid-cols-4 items-center gap-4">
            <Label className="text-right">Notes</Label>
            <Textarea placeholder="Notes for interviewer/candidate" value={notes} onChange={e => setNotes(e.target.value)} className="col-span-3" />
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => setOpen(false)}>Cancel</Button>
          <Button onClick={handleSchedule} disabled={scheduleMutation.isPending || !date || !time}>
            {scheduleMutation.isPending ? "Scheduling..." : "Schedule & Notify"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
    </>
  );
}
