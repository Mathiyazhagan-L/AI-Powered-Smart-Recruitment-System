"use client";

import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Briefcase, Calendar, CheckSquare, ChevronRight, Clock, Building, MapPin } from "lucide-react";
import Link from "next/link";
import { useUser } from "@/lib/hooks/useAuth";
import { useCandidateDashboard } from "@/lib/hooks/useDashboard";
import { useProfileCompletion, useGetProfile } from "@/lib/hooks/useProfile";
import { Progress } from "@/components/ui/progress";

export default function CandidateDashboard() {
  const { data: user } = useUser();
  const { data: profile } = useGetProfile(user?.id);
  const { applications, interviews, assessments, recommendedJobs, isLoading } = useCandidateDashboard();
  const { completionPercentage, isLoading: isProfileLoading } = useProfileCompletion(user?.id);
  
  if (isLoading) {
    return <div className="flex items-center justify-center h-full min-h-[50vh]"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div></div>;
  }
  return (
    <div className="space-y-8">
      <div className="grid gap-6 md:grid-cols-[1fr_300px]">
        {/* Welcome Banner */}
        <div className="bg-gradient-to-r from-primary to-primary/80 rounded-2xl p-8 text-primary-foreground shadow-lg flex flex-col justify-center">
          <div>
            <h1 className="text-3xl font-bold mb-2">Welcome back, {profile?.full_name || user?.username || 'Candidate'}!</h1>
            <p className="text-primary-foreground/80 max-w-xl">
              You have {interviews?.length || 0} upcoming interviews. Make sure to review the preparation materials.
            </p>
          </div>
          <div className="mt-6">
            <Button className="bg-secondary text-secondary-foreground hover:bg-secondary/90 shadow-md border-none whitespace-nowrap">
              <Calendar className="mr-2 h-4 w-4" /> View Schedule
            </Button>
          </div>
        </div>

        {/* Profile Strength */}
        <Card className="shadow-sm border-none bg-card/50 backdrop-blur-sm">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-semibold uppercase tracking-wider text-muted-foreground">Profile Strength</CardTitle>
          </CardHeader>
          <CardContent className="flex flex-col justify-center h-full pb-8">
            <div className="flex justify-between items-end mb-2">
              <span className="text-3xl font-bold text-primary">{isProfileLoading ? "..." : completionPercentage}%</span>
            </div>
            <Progress value={completionPercentage} className="h-2 mb-3" />
            <p className="text-xs text-muted-foreground">
              {completionPercentage < 50 && "You need 50% to apply for jobs."}
              {completionPercentage >= 50 && completionPercentage < 70 && "You need 70% to take assessments."}
              {completionPercentage >= 70 && completionPercentage < 100 && "You need 100% to unlock AI Review."}
              {completionPercentage === 100 && "All features unlocked!"}
            </p>
            <Link href="/profile" className="text-xs text-primary font-medium hover:underline mt-2 inline-block">
              Improve Profile →
            </Link>
          </CardContent>
        </Card>
      </div>

      {/* KPI Cards */}
      <div className="grid gap-4 md:grid-cols-3">
        <Link href="/applications" className="block">
          <Card className="hover:border-primary/50 transition-colors shadow-sm cursor-pointer h-full">
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium">Active Applications</CardTitle>
              <Briefcase className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{applications?.length || 0}</div>
              <p className="text-xs text-muted-foreground mt-1">Total submitted</p>
            </CardContent>
          </Card>
        </Link>
        <Link href="/interviews" className="block">
          <Card className="hover:border-primary/50 transition-colors shadow-sm cursor-pointer h-full">
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium">Upcoming Interviews</CardTitle>
              <Calendar className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{interviews?.length || 0}</div>
              <p className="text-xs text-muted-foreground mt-1">Scheduled sessions</p>
            </CardContent>
          </Card>
        </Link>
        <Link href="/assessments" className="block">
          <Card className="hover:border-primary/50 transition-colors shadow-sm cursor-pointer h-full">
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium">Completed Assessments</CardTitle>
              <CheckSquare className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{assessments?.length || 0}</div>
              <p className="text-xs text-muted-foreground mt-1 text-success font-medium">
                {assessments?.length ? `${assessments.filter((a: any) => a?.status === 'PASSED' || a?.hiring_recommendation === 'Recommended').length} passed` : "No scores yet"}
              </p>
            </CardContent>
          </Card>
        </Link>
      </div>

      <div className="grid gap-6 md:grid-cols-3">
        {/* Main Content Area */}
        <div className="md:col-span-2 space-y-6">
          <div className="flex justify-between items-center">
            <h2 className="text-xl font-bold tracking-tight text-foreground">Recent Activity</h2>
            <Link href="/applications" className="text-sm text-primary hover:underline font-medium">View All</Link>
          </div>
          
          <div className="space-y-4">
            {/* Activity Items */}
            {interviews?.length > 0 ? (
              interviews.slice(0, 3).map((interview: any) => (
                <Card key={interview.id} className="shadow-sm">
                  <CardContent className="p-6">
                    <div className="flex items-start justify-between">
                      <div className="flex items-start space-x-4">
                        <div className="h-10 w-10 rounded-full bg-blue-100 flex items-center justify-center border border-blue-200 mt-1">
                          <Calendar className="h-5 w-5 text-blue-600" />
                        </div>
                        <div>
                          <div className="flex items-center gap-2 mb-1">
                            <h4 className="font-semibold text-lg">{interview.interview_title || "Interview Scheduled"}</h4>
                            <Badge className="bg-blue-500 hover:bg-blue-600 border-none text-white">{interview.status}</Badge>
                          </div>
                          <p className="text-muted-foreground text-sm">
                            With <strong>{interview.interviewer_name || "AI Reviewer"}</strong>
                          </p>
                          <div className="flex items-center text-xs text-muted-foreground mt-3 bg-muted/50 w-fit px-3 py-1.5 rounded-md border border-border/50">
                            <Clock className="mr-1.5 h-3.5 w-3.5" /> {interview.interview_date} at {interview.interview_time} ({interview.duration_minutes} min)
                          </div>
                        </div>
                      </div>
                      <Button variant="outline" size="sm">Details</Button>
                    </div>
                  </CardContent>
                </Card>
              ))
            ) : (
              <p className="text-muted-foreground text-sm p-4 border rounded-md bg-muted/20">No recent activity found.</p>
            )}
          </div>
        </div>

        {/* Sidebar / Recommended Jobs */}
        <div className="space-y-6">
          <h2 className="text-xl font-bold tracking-tight text-foreground">Recommended Jobs</h2>
          
          {recommendedJobs?.length > 0 ? (
            recommendedJobs.slice(0, 3).map((job: any) => (
              <Link key={job.id} href={`/jobs?search=${encodeURIComponent(job.title)}`} className="block">
                <Card className="shadow-sm hover:border-primary/50 transition-colors group cursor-pointer h-full">
                  <CardContent className="p-5">
                    <div className="flex justify-between items-start mb-2">
                      <h4 className="font-semibold text-primary group-hover:text-secondary transition-colors">{job.title}</h4>
                      {job.match_score !== undefined && <Badge variant="outline" className="text-xs bg-background">Match {Math.max(0, Math.min(100, Math.round(job.match_score)))}%</Badge>}
                    </div>
                    <div className="space-y-2 mt-3 text-sm text-muted-foreground">
                      <div className="flex items-center"><Building className="mr-2 h-4 w-4" /> {job.company_name || 'AIHire Partner'}</div>
                      <div className="flex items-center"><MapPin className="mr-2 h-4 w-4" /> {job.location || 'Remote'}</div>
                    </div>
                  </CardContent>
                </Card>
              </Link>
            ))
          ) : (
            <p className="text-muted-foreground text-sm">No specific recommendations yet. Fill out your profile!</p>
          )}

          <Link href="/jobs" className="block w-full">
            <Button variant="outline" className="w-full">View All Openings</Button>
          </Link>
        </div>
      </div>
    </div>
  );
}
