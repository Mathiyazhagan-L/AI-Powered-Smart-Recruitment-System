"use client";

import React from "react";
import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@/lib/apiClient";
import { useUser } from "@/lib/hooks/useAuth";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Calendar, Clock, Video } from "lucide-react";

export default function CandidateInterviewsPage() {
  const { data: user } = useUser();
  const candidateId = user?.id || 0;

  const { data: interviews, isLoading } = useQuery({
    queryKey: ["candidateInterviews", candidateId],
    queryFn: async () => {
      const res = await apiClient.get(`/interviews/candidate/${candidateId}`);
      return res.data || [];
    },
    enabled: !!candidateId,
  });

  return (
    <div className="flex flex-col h-full space-y-6">
      <div>
        <h2 className="text-3xl font-bold tracking-tight text-foreground">My Interviews</h2>
        <p className="text-muted-foreground mt-1">View and manage your scheduled interviews.</p>
      </div>

      <div className="flex-1 overflow-y-auto space-y-4">
        {isLoading ? (
          <div className="p-8 text-center text-muted-foreground flex flex-col items-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mb-2"></div>
            <p>Loading interviews...</p>
          </div>
        ) : !interviews || interviews.length === 0 ? (
          <Card>
            <CardContent className="p-8 text-center text-muted-foreground">
              <p>You have no scheduled interviews at this time.</p>
            </CardContent>
          </Card>
        ) : (
          interviews.map((interview: any) => {
            const isExpired = (() => {
              if (!interview.interview_date || !interview.interview_time) return false;
              const start = new Date(`${interview.interview_date}T${interview.interview_time}`);
              if (isNaN(start.getTime())) return false;
              const end = new Date(start.getTime() + (interview.duration_minutes || 60) * 60 * 1000);
              return new Date() > end;
            })();

            return (
              <Card key={interview.id} className="border-l-4 border-l-primary shadow-sm hover:shadow-md transition-shadow">
                <CardContent className="p-6 flex justify-between items-center">
                  <div>
                    <h3 className="text-xl font-bold">
                      {interview.interview_title}
                      {interview.company_name ? ` with ${interview.company_name}` : ""}
                    </h3>
                    {interview.job_title && (
                      <p className="text-sm font-medium text-muted-foreground mt-1">For {interview.job_title}</p>
                    )}
                    <div className="flex space-x-4 mt-3 text-sm text-muted-foreground">
                      <span className="flex items-center"><Calendar className="mr-1 h-4 w-4" /> {interview.interview_date}</span>
                      <span className="flex items-center"><Clock className="mr-1 h-4 w-4" /> {interview.interview_time} ({interview.duration_minutes}m)</span>
                      <span className="flex items-center"><Video className="mr-1 h-4 w-4" /> {interview.interview_mode}</span>
                    </div>
                  </div>
                  
                  <div className="flex flex-col items-end space-y-2">
                    <Badge variant="outline" className="bg-primary/10 text-primary">
                      {interview.status}
                    </Badge>
                    {interview.meeting_link && (
                      <Button 
                        disabled={
                          !["scheduled", "confirmed", "rescheduled"].includes(interview.status?.toLowerCase()) ||
                          isExpired
                        }
                        onClick={() => window.open(interview.meeting_link, "_blank")}
                      >
                        Join Meeting
                      </Button>
                    )}
                  </div>
                </CardContent>
              </Card>
            );
          })
        )}
      </div>
    </div>
  );
}
