"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Search, Filter, Calendar as CalendarIcon, ChevronLeft, ChevronRight, Video, MapPin, User, Clock, Plus, RefreshCw } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Button, buttonVariants } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from "@/components/ui/dropdown-menu";
import { useInterviews, useUpdateInterviewStatus, Interview } from "@/lib/hooks/useInterviews";

export default function InterviewsPage() {
  const { data: interviews, isLoading } = useInterviews();
  const updateStatus = useUpdateInterviewStatus();
  const router = useRouter();

  const [date, setDate] = useState(new Date());
  const [view, setView] = useState("Day");
  const [isSyncing, setIsSyncing] = useState(false);

  const activeInterviews = interviews || [];
  
  const formattedDate = date.toLocaleDateString('en-US', { weekday: 'long', month: 'short', day: 'numeric', year: 'numeric' });

  const handlePrev = () => {
    const newDate = new Date(date);
    newDate.setDate(date.getDate() - 1);
    setDate(newDate);
  };
  
  const handleNext = () => {
    const newDate = new Date(date);
    newDate.setDate(date.getDate() + 1);
    setDate(newDate);
  };

  const handleSync = () => {
    setIsSyncing(true);
    setTimeout(() => {
      setIsSyncing(false);
      alert("Calendar successfully synced with external provider!");
    }, 1000);
  };
  return (
    <div className="flex flex-col h-full space-y-4">
      {/* Sticky Header */}
      <div className="sticky top-0 z-10 bg-muted/20 backdrop-blur-md pb-4 border-b border-border/50 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h2 className="text-3xl font-bold tracking-tight text-foreground">Interview Management</h2>
          <p className="text-muted-foreground mt-1">Schedule and manage candidate interviews.</p>
        </div>
        <div className="flex space-x-2">
          <Button variant="outline" className="bg-background" onClick={handleSync} disabled={isSyncing}>
            {isSyncing ? <RefreshCw className="mr-2 h-4 w-4 animate-spin" /> : <CalendarIcon className="mr-2 h-4 w-4" />} 
            {isSyncing ? "Syncing..." : "Sync Calendar"}
          </Button>
          <Button className="bg-secondary text-secondary-foreground hover:bg-secondary/90" onClick={() => router.push("/hr-queue")}>
            <Plus className="mr-2 h-4 w-4" /> Schedule Interview
          </Button>
        </div>
      </div>

      {/* Calendar Controls */}
      <div className="flex items-center justify-between py-2">
        <div className="flex items-center space-x-4">
          <h3 className="text-xl font-semibold">{formattedDate}</h3>
          <div className="flex items-center space-x-1 border rounded-md p-0.5 bg-background shadow-sm">
            <Button variant="ghost" size="icon" className="h-7 w-7" onClick={handlePrev}><ChevronLeft className="h-4 w-4" /></Button>
            <Button variant="ghost" size="sm" className="h-7 px-2 font-medium" onClick={() => setDate(new Date())}>Today</Button>
            <Button variant="ghost" size="icon" className="h-7 w-7" onClick={handleNext}><ChevronRight className="h-4 w-4" /></Button>
          </div>
        </div>
        <div className="flex space-x-2">
          <div className="relative hidden md:block">
            <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
            <Input placeholder="Search interviews..." className="pl-9 bg-background w-48 h-9" />
          </div>
          <div className="flex items-center space-x-1 border rounded-md p-0.5 bg-background shadow-sm">
            <Button variant={view === "Day" ? "secondary" : "ghost"} size="sm" className="h-7 px-3 font-medium shadow-none" onClick={() => setView("Day")}>Day</Button>
            <Button variant={view === "Week" ? "secondary" : "ghost"} size="sm" className="h-7 px-3 font-medium shadow-none" onClick={() => setView("Week")}>Week</Button>
            <Button variant={view === "Month" ? "secondary" : "ghost"} size="sm" className="h-7 px-3 font-medium shadow-none" onClick={() => setView("Month")}>Month</Button>
          </div>
        </div>
      </div>

      {/* Schedule View */}
      <div className="flex-1 border rounded-lg bg-background shadow-sm overflow-hidden flex flex-col">
        <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-muted/10">
          
          {isLoading ? (
            <div className="p-8 text-center text-muted-foreground flex flex-col items-center">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mb-2"></div>
              <p>Loading interviews...</p>
            </div>
          ) : activeInterviews.length === 0 ? (
            <div className="p-8 text-center text-muted-foreground">
              <p>No interviews scheduled.</p>
            </div>
          ) : (
            activeInterviews.map((interview: Interview) => {
              const isExpired = (() => {
                if (!interview.interview_date || !interview.interview_time) return false;
                const start = new Date(`${interview.interview_date}T${interview.interview_time}`);
                if (isNaN(start.getTime())) return false;
                const end = new Date(start.getTime() + (interview.duration_minutes || 60) * 60 * 1000);
                return new Date() > end;
              })();

              return (
                <div key={interview.id} className="flex gap-4 group mt-2">
                  <div className="w-20 text-right text-sm text-muted-foreground font-medium pt-2">
                    {interview.interview_time || "TBD"}
                  </div>
                  <Card className={`flex-1 border-l-4 shadow-sm hover:shadow-md transition-shadow cursor-pointer ${interview.interview_type === 'On-site' ? 'border-l-purple-500' : 'border-l-blue-500'}`}>
                    <CardContent className="p-4 flex justify-between items-center">
                      <div className="flex items-start space-x-4">
                        <Avatar className="h-10 w-10 mt-1">
                          <AvatarFallback className={interview.interview_type === 'On-site' ? "bg-purple-100 text-purple-700" : "bg-primary/10 text-primary"}>
                            {(interview.candidate_name || "C")[0]}
                          </AvatarFallback>
                        </Avatar>
                        <div>
                          <h4 className="font-semibold text-lg leading-tight">{interview.candidate_name || `Candidate #${interview.candidate_id}`}</h4>
                          <p className="text-sm text-muted-foreground mt-0.5">{interview.job_title || `Job #${interview.job_id}`}</p>
                          <div className="flex flex-wrap gap-3 mt-2 text-xs text-muted-foreground">
                            <span className="flex items-center"><Clock className="mr-1 h-3 w-3" /> {interview.duration_minutes}m</span>
                            <span className={`flex items-center ${interview.interview_type === 'On-site' ? 'text-purple-600' : 'text-blue-500'}`}>
                              {interview.interview_type === 'On-site' ? <MapPin className="mr-1 h-3 w-3" /> : <Video className="mr-1 h-3 w-3" />} 
                              {interview.interview_type}
                            </span>
                            <span className="flex items-center"><CalendarIcon className="mr-1 h-3 w-3" /> {interview.interview_date}</span>
                          </div>
                        </div>
                      </div>
                      <div className="flex flex-col items-end space-y-2">
                        <Badge variant="outline" className={`border-blue-200 ${interview.status === 'Completed' ? 'bg-success/10 text-success border-success/30' : 'bg-blue-50 text-blue-700'}`}>
                          {interview.status}
                        </Badge>
                        <div className="flex space-x-2">
                          {interview.meeting_link && (
                            <Button 
                              variant="outline" 
                              size="sm" 
                              disabled={isExpired}
                              onClick={() => window.open(interview.meeting_link, "_blank", "noopener,noreferrer")}
                            >
                              Join Meeting
                            </Button>
                          )}
                        <DropdownMenu>
                          <DropdownMenuTrigger className={buttonVariants({ variant: "outline", size: "sm" })}>
                            Update Status
                          </DropdownMenuTrigger>
                          <DropdownMenuContent>
                            <DropdownMenuItem onClick={() => updateStatus.mutate({ id: interview.id, status: "Selected" })}>Selected</DropdownMenuItem>
                            <DropdownMenuItem onClick={() => updateStatus.mutate({ id: interview.id, status: "Waiting" })}>Waiting</DropdownMenuItem>
                            <DropdownMenuItem onClick={() => updateStatus.mutate({ id: interview.id, status: "Rejected" })}>Rejected</DropdownMenuItem>
                          </DropdownMenuContent>
                        </DropdownMenu>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </div>
            );
          })
          )}
        </div>
      </div>
    </div>
  );
}
