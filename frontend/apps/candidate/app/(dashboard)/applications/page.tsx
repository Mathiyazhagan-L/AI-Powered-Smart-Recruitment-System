"use client";

import React from "react";
import { useGetMyApplications, Job } from "@/lib/hooks/useJobs";
import { useUser } from "@/lib/hooks/useAuth";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Briefcase, Building2, MapPin, Calendar, CheckCircle2, Clock, XCircle, ChevronRight } from "lucide-react";
import { format } from "date-fns";
import { cn } from "@/lib/utils";

// Helper hook to fetch single job details for each application
import { useGetJob } from "@/lib/hooks/useJobs";

function ApplicationCard({ application }: { application: any }) {
  const { data: job, isLoading } = useGetJob(application.job_id);

  if (isLoading) {
    return <Card className="animate-pulse h-32 bg-muted/20" />;
  }

  if (!job) return null;

  const statuses = [
    { id: "Applied", label: "Applied" },
    { id: "Screening", label: "Screening" },
    { id: "Assessment", label: "Assessment" },
    { id: "Interview", label: "Interview" },
    { id: "Selected", label: "Selected" },
  ];

  const mapStatusToStep = (status: string): { step: string; isRejected: boolean } => {
    const s = (status || "").toLowerCase();
    
    if (s.includes("hr rejected") || s.includes("screening rejected") || s.includes("rejected")) {
      const step = s.includes("interview") ? "Interview" : 
                   s.includes("recommendation") || s.includes("review") || s.includes("assessment") || s.includes("test") ? "Assessment" : "Screening";
      return { step, isRejected: true };
    }
    if (s.includes("declined") || s.includes("expired") || s.includes("no show")) {
      return { step: "Selected", isRejected: true };
    }
    if (s.includes("selected") || s.includes("hired") || s.includes("joined") || s.includes("offer") || s.includes("accepted")) {
      return { step: "Selected", isRejected: false };
    }
    if (s.includes("hr interview") || s.includes("interview")) {
      return { step: "Interview", isRejected: false };
    }
    if (s.includes("ai recommendation") || s.includes("recruiter review") || s.includes("assessment") || s.includes("test")) {
      return { step: "Assessment", isRejected: false };
    }
    if (s.includes("ai screening") || s.includes("screening") || s.includes("approved") || s.includes("shortlisted")) {
      return { step: "Screening", isRejected: false };
    }
    return { step: "Applied", isRejected: false }; // Fallback for "Applied", "HR Review", "NEW"
  };

  const { step: mappedStatus, isRejected } = mapStatusToStep(application.status);
  const currentStatusIndex = statuses.findIndex(s => s.id === mappedStatus);

  return (
    <Card className="overflow-hidden">
      <CardContent className="p-6">
        <div className="flex flex-col md:flex-row gap-6">
          
          <div className="w-16 h-16 rounded-xl bg-primary/10 flex items-center justify-center shrink-0 border">
            <Building2 className="w-8 h-8 text-primary" />
          </div>

          <div className="flex-1 space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4">
              <div>
                <h3 className="text-xl font-bold">{job.title}</h3>
                <div className="flex items-center gap-2 mt-1 text-sm text-muted-foreground">
                  <span>AIHire Platform</span>
                  <span>•</span>
                  <span className="flex items-center gap-1"><MapPin className="w-3.5 h-3.5" /> {job.location}</span>
                </div>
              </div>
              <div className="text-right">
                <div className="text-sm font-medium text-foreground">Applied on</div>
                <div className="text-sm text-muted-foreground flex items-center justify-end gap-1 mt-0.5">
                  <Calendar className="w-3.5 h-3.5" />
                  {format(new Date(application.created_at), "MMM d, yyyy")}
                </div>
              </div>
            </div>

            {/* Timeline View */}
            <div className="pt-4 mt-4 border-t relative">
              <div className="flex items-center justify-between">
                {statuses.map((status, index) => {
                  const isActive = isRejected ? index < currentStatusIndex : currentStatusIndex >= index;
                  const isCurrent = isRejected ? index === currentStatusIndex : currentStatusIndex === index;
                  
                  return (
                    <div key={status.id} className="flex flex-col items-center gap-2 relative z-10">
                      <div className={cn(
                        "w-8 h-8 rounded-full flex items-center justify-center border-2 transition-colors bg-background",
                        isActive ? "border-primary text-primary" : "border-muted text-muted-foreground",
                        isCurrent && !isRejected && "bg-primary text-primary-foreground border-primary",
                        isRejected && index === currentStatusIndex && "border-destructive text-destructive bg-destructive/10"
                      )}>
                        {isActive && !isCurrent ? <CheckCircle2 className="w-5 h-5 text-primary" /> : 
                         isRejected && index === currentStatusIndex ? <XCircle className="w-5 h-5 text-destructive" /> :
                         <span className="text-xs font-bold">{index + 1}</span>}
                      </div>
                      <span className={cn(
                        "text-xs font-medium absolute -bottom-6 w-20 text-center",
                        isActive ? "text-foreground" : "text-muted-foreground"
                      )}>
                        {status.label}
                      </span>
                    </div>
                  );
                })}
              </div>

              {/* Progress Line */}
              <div className="absolute top-8 left-4 right-4 h-0.5 bg-muted -z-0">
                <div 
                  className={cn("h-full transition-all duration-500", isRejected ? "bg-destructive" : "bg-primary")} 
                  style={{ width: `${(currentStatusIndex / (statuses.length - 1)) * 100}%` }} 
                />
              </div>
            </div>

            {isRejected && (
              <div className="mt-8 bg-destructive/10 text-destructive border border-destructive/20 p-3 rounded-lg text-sm flex items-center gap-2">
                <XCircle className="w-4 h-4 shrink-0" />
                <span>Your application was unfortunately not selected to move forward for this role.</span>
              </div>
            )}
            
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

export default function ApplicationsPage() {
  const { data: user } = useUser();
  const candidateId = user?.id;

  const { data: applications, isLoading, error } = useGetMyApplications(candidateId);

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">My Applications</h1>
        <p className="text-muted-foreground mt-2">Track the status of all your submitted job applications.</p>
      </div>

      {isLoading ? (
        <div className="space-y-4 pt-4">
          {[1, 2, 3].map(i => (
            <Card key={i} className="animate-pulse h-48 bg-muted/20" />
          ))}
        </div>
      ) : error ? (
        <div className="text-center py-10 text-destructive bg-destructive/10 rounded-xl border border-destructive/20 mt-4">
          Failed to load applications.
        </div>
      ) : !applications || applications.length === 0 ? (
        <div className="text-center py-20 bg-muted/10 rounded-xl border border-dashed flex flex-col items-center mt-4">
          <Briefcase className="w-12 h-12 text-muted-foreground/50 mb-4" />
          <h3 className="text-lg font-semibold text-foreground">No applications found</h3>
          <p className="text-muted-foreground text-sm max-w-sm mt-2">
            You haven't applied to any jobs yet. Browse the job board to find your next opportunity!
          </p>
        </div>
      ) : (
        <div className="space-y-6 pt-4 pb-10">
          {applications.sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime()).map((app) => (
            <ApplicationCard key={app.id} application={app} />
          ))}
        </div>
      )}
    </div>
  );
}
