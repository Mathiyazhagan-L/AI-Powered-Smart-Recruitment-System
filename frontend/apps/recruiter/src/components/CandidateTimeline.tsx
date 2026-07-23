"use client";

import React, { useState, useEffect } from "react";
import { apiClient } from "@/lib/apiClient";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Activity, Clock } from "lucide-react";

interface TimelineEvent {
  id: number;
  candidate_id: number;
  event_type: string;
  description: string;
  triggered_by: string;
  created_at: string;
}

export default function CandidateTimeline({ candidateId }: { candidateId: string | number }) {
  const [events, setEvents] = useState<TimelineEvent[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchTimeline = async () => {
      try {
        const res = await apiClient.get(`/recruiter-workspace/timeline/candidate/${candidateId}`);
        setEvents(res.data);
      } catch (e) {
        console.error("Failed to fetch timeline", e);
      } finally {
        setLoading(false);
      }
    };
    fetchTimeline();
  }, [candidateId]);

  return (
    <Card className="flex flex-col h-full border-border/50">
      <CardHeader className="pb-3 border-b bg-muted/20">
        <CardTitle className="flex items-center text-lg">
          <Activity className="mr-2 h-5 w-5 text-primary" /> Activity Timeline
        </CardTitle>
      </CardHeader>
      <CardContent className="flex-1 p-4 overflow-y-auto">
        {loading ? (
          <div className="flex justify-center p-4"><div className="animate-spin rounded-full h-5 w-5 border-b-2 border-primary"></div></div>
        ) : events.length === 0 ? (
          <div className="text-center py-8 text-muted-foreground text-sm italic">
            No activity recorded yet.
          </div>
        ) : (
          <div className="relative border-l-2 border-border ml-3 space-y-6 mt-2 mb-2">
            {events.map((event, index) => (
              <div key={event.id} className="relative pl-6">
                <div className="absolute -left-[9px] top-1 h-4 w-4 rounded-full bg-background border-2 border-primary"></div>
                <div className="flex flex-col">
                  <span className="text-sm font-semibold">{event.event_type}</span>
                  <span className="text-xs text-muted-foreground flex items-center mt-0.5">
                    <Clock className="h-3 w-3 mr-1" /> {new Date(event.created_at).toLocaleString()} 
                    <span className="mx-2">•</span> 
                    By {event.triggered_by}
                  </span>
                  <p className="text-sm mt-1.5 text-foreground/80">{event.description}</p>
                </div>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
