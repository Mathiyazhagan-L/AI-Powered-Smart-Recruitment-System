"use client";

import { useState, useMemo } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger, DropdownMenuLabel, DropdownMenuSeparator } from "@/components/ui/dropdown-menu";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Calendar, MoreHorizontal, Search, Filter, Briefcase, User, Eye, CheckCircle, XCircle } from "lucide-react";
import { useAllApplications, useUpdateApplicationStatus, Application } from "@/lib/hooks/useApplications";
import { useJobs, Job } from "@/lib/hooks/useJobs";
import { useCandidates, CandidateProfile } from "@/lib/hooks/useCandidates";
import Link from "next/link";

const STAGES = [
  "Applied",
  "AI Screening",
  "AI Recommendation",
  "Recruiter Review",
  "HR Interview",
  "Offer Generated",
  "Offer Accepted",
  "Background Verification",
  "Joined",
  "Rejected"
];

export default function ApplicationsPage() {
  const { data: jobs, isLoading: isLoadingJobs } = useJobs();
  const { data: applications, isLoading: isLoadingApps } = useAllApplications();
  const { data: candidates, isLoading: isLoadingCands } = useCandidates();
  const updateStatus = useUpdateApplicationStatus();

  const [searchQuery, setSearchQuery] = useState("");
  const [selectedJobId, setSelectedJobId] = useState<string>("all");
  const [selectedStatus, setSelectedStatus] = useState<string>("all");

  // Create a map of candidates for fast lookup
  const candidateMap = useMemo(() => {
    const map: Record<number, CandidateProfile> = {};
    if (candidates) {
      candidates.forEach(c => {
        map[c.user_id] = c;
      });
    }
    return map;
  }, [candidates]);

  // Create a map of jobs for fast lookup
  const jobMap = useMemo(() => {
    const map: Record<number, Job> = {};
    if (jobs) {
      jobs.forEach(j => {
        map[j.id] = j;
      });
    }
    return map;
  }, [jobs]);

  // Filtered applications list
  const filteredApplications = useMemo(() => {
    if (!applications) return [];

    return applications.filter((app: Application) => {
      const candidate = candidateMap[app.candidate_id];
      const job = jobMap[app.job_id];
      
      const candidateName = candidate?.full_name || `Candidate #${app.candidate_id}`;
      const candidateHeadline = candidate?.headline || "Applicant";
      const jobTitle = job?.title || `Job #${app.job_id}`;

      // Search match
      const matchesSearch = 
        candidateName.toLowerCase().includes(searchQuery.toLowerCase()) ||
        candidateHeadline.toLowerCase().includes(searchQuery.toLowerCase()) ||
        jobTitle.toLowerCase().includes(searchQuery.toLowerCase());

      // Job match
      const matchesJob = selectedJobId === "all" || app.job_id.toString() === selectedJobId;

      // Status match
      const matchesStatus = selectedStatus === "all" || app.status === selectedStatus;

      return matchesSearch && matchesJob && matchesStatus;
    });
  }, [applications, candidateMap, jobMap, searchQuery, selectedJobId, selectedStatus]);

  // Styling helper for status badges
  const getStatusBadgeStyles = (status: string) => {
    const normalized = status.toLowerCase();
    if (normalized === "applied") return "bg-blue-50 text-blue-700 border-blue-200";
    if (normalized.includes("screening")) return "bg-amber-50 text-amber-700 border-amber-200";
    if (normalized.includes("recommendation")) return "bg-purple-50 text-purple-700 border-purple-200";
    if (normalized.includes("review")) return "bg-orange-50 text-orange-700 border-orange-200";
    if (normalized.includes("interview")) return "bg-teal-50 text-teal-700 border-teal-200";
    if (normalized.includes("offer")) return "bg-indigo-50 text-indigo-700 border-indigo-200";
    if (normalized.includes("joined") || normalized.includes("approved")) return "bg-success/10 text-success border-success/30";
    if (normalized.includes("rejected") || normalized.includes("declined")) return "bg-destructive/10 text-destructive border-destructive/30";
    return "bg-secondary text-secondary-foreground";
  };

  // Styling helper for ATS badges
  const getAtsBadgeStyles = (score?: number) => {
    if (!score) return "bg-muted text-muted-foreground";
    if (score >= 80) return "bg-success/15 text-success border-success/30";
    if (score >= 60) return "bg-amber-500/15 text-amber-600 border-amber-500/30";
    return "bg-destructive/15 text-destructive border-destructive/30";
  };

  return (
    <div className="flex flex-col h-full space-y-6">
      {/* Page Header */}
      <div>
        <h2 className="text-3xl font-bold tracking-tight text-foreground">Candidate Applications</h2>
        <p className="text-muted-foreground mt-1">Review and manage all applicants submitted to your organization.</p>
      </div>

      {/* Filters Toolbar */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 p-4 rounded-xl border bg-card shadow-sm">
        {/* Search */}
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground pointer-events-none" />
          <Input
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search by candidate name, title, or job..."
            className="pl-9 h-10 bg-background"
          />
        </div>

        {/* Filters */}
        <div className="flex flex-wrap items-center gap-3">
          {/* Job Filter */}
          <div className="flex items-center space-x-2">
            <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wider flex items-center"><Briefcase className="h-3.5 w-3.5 mr-1" /> Job:</span>
            <select
              value={selectedJobId}
              onChange={(e) => setSelectedJobId(e.target.value)}
              className="h-10 rounded-md border border-input bg-background px-3 py-2 text-sm shadow-sm focus:outline-none focus:ring-1 focus:ring-ring"
            >
              <option value="all">All Job Posts</option>
              {jobs?.map((job: Job) => (
                <option key={job.id} value={job.id.toString()}>
                  {job.title}
                </option>
              ))}
            </select>
          </div>

          {/* Status Filter */}
          <div className="flex items-center space-x-2">
            <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wider flex items-center"><Filter className="h-3.5 w-3.5 mr-1" /> Stage:</span>
            <select
              value={selectedStatus}
              onChange={(e) => setSelectedStatus(e.target.value)}
              className="h-10 rounded-md border border-input bg-background px-3 py-2 text-sm shadow-sm focus:outline-none focus:ring-1 focus:ring-ring"
            >
              <option value="all">All Stages</option>
              {STAGES.map((stage) => (
                <option key={stage} value={stage}>
                  {stage}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Main Content Area */}
      {isLoadingJobs || isLoadingApps || isLoadingCands ? (
        <Card className="flex items-center justify-center h-64 border-dashed">
          <div className="flex flex-col items-center justify-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mb-3"></div>
            <p className="text-muted-foreground">Loading applications...</p>
          </div>
        </Card>
      ) : filteredApplications.length === 0 ? (
        <Card className="flex flex-col items-center justify-center p-12 text-center border-dashed">
          <div className="h-16 w-16 rounded-full bg-muted flex items-center justify-center mb-4">
            <User className="h-8 w-8 text-muted-foreground" />
          </div>
          <h3 className="text-xl font-bold mb-2">No Applications Found</h3>
          <p className="text-muted-foreground max-w-md">
            No applicant records match your current filters. Try adjusting your search query or dropdown selections.
          </p>
        </Card>
      ) : (
        <div className="border rounded-lg bg-background shadow-sm overflow-hidden flex-1">
          <Table suppressHydrationWarning>
            <TableHeader className="bg-muted/50 sticky top-0 z-10 backdrop-blur-sm">
              <TableRow>
                <TableHead>Candidate</TableHead>
                <TableHead>Job Title</TableHead>
                <TableHead>Applied Date</TableHead>
                <TableHead>ATS Match</TableHead>
                <TableHead>Hiring Stage</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredApplications.map((app: Application) => {
                const candidate = candidateMap[app.candidate_id];
                const job = jobMap[app.job_id];
                const candidateName = candidate?.full_name || `Candidate #${app.candidate_id}`;
                const candidateHeadline = candidate?.headline || "Applicant";
                const jobTitle = job?.title || `Job #${app.job_id}`;
                const appliedDate = new Date(app.created_at).toLocaleDateString(undefined, {
                  year: "numeric",
                  month: "short",
                  day: "numeric"
                });

                return (
                  <TableRow key={app.id} className="hover:bg-muted/30 transition-colors group">
                    {/* Candidate */}
                    <TableCell>
                      <div className="flex items-center space-x-3">
                        <User className="h-9 w-9 p-2 rounded-xl bg-primary/10 text-primary border border-primary/20 shrink-0" />
                        <div>
                          <Link href={`/candidates/${app.candidate_id}`} className="font-semibold text-foreground hover:underline text-sm block">
                            {candidateName}
                          </Link>
                          <span className="text-xs text-muted-foreground block truncate max-w-[200px]">{candidateHeadline}</span>
                        </div>
                      </div>
                    </TableCell>

                    {/* Job Title */}
                    <TableCell>
                      <span className="font-medium text-foreground">{jobTitle}</span>
                    </TableCell>

                    {/* Applied Date */}
                    <TableCell className="text-muted-foreground text-sm">
                      <div className="flex items-center">
                        <Calendar className="h-4 w-4 mr-1 text-muted-foreground/75" />
                        {appliedDate}
                      </div>
                    </TableCell>

                    {/* ATS Score */}
                    <TableCell>
                      <Badge variant="outline" className={`font-semibold ${getAtsBadgeStyles(app.ats_score)}`}>
                        {app.ats_score != null ? `${app.ats_score}% Match` : "N/A"}
                      </Badge>
                    </TableCell>

                    {/* Stage Dropdown Selector */}
                    <TableCell>
                      <select
                        value={app.status}
                        onChange={(e) => updateStatus.mutate({ id: app.id, status: e.target.value })}
                        className={`h-8 rounded-md border px-2.5 py-0.5 text-xs font-semibold shadow-sm focus:outline-none focus:ring-1 focus:ring-ring cursor-pointer transition-all ${getStatusBadgeStyles(app.status)}`}
                      >
                        {STAGES.map((stage) => (
                          <option key={stage} value={stage} className="bg-background text-foreground font-medium">
                            {stage}
                          </option>
                        ))}
                      </select>
                    </TableCell>

                    {/* Actions */}
                    <TableCell className="text-right">
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button variant="ghost" size="icon" className="h-8 w-8 p-0 opacity-0 group-hover:opacity-100 transition-opacity">
                            <MoreHorizontal className="h-4 w-4" />
                            <span className="sr-only">Open menu</span>
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end" className="w-[160px]">
                          <DropdownMenuLabel>Actions</DropdownMenuLabel>
                          <DropdownMenuItem onClick={() => window.location.href = `/candidates/${app.candidate_id}`}>
                            <Eye className="mr-2 h-4 w-4" /> View Profile
                          </DropdownMenuItem>
                          <DropdownMenuSeparator />
                          <DropdownMenuItem 
                            className="text-success font-medium"
                            onClick={() => updateStatus.mutate({ id: app.id, status: "Offer Generated" })}
                          >
                            <CheckCircle className="mr-2 h-4 w-4" /> Approve for Offer
                          </DropdownMenuItem>
                          <DropdownMenuItem 
                            className="text-destructive font-medium"
                            onClick={() => updateStatus.mutate({ id: app.id, status: "Rejected" })}
                          >
                            <XCircle className="mr-2 h-4 w-4" /> Reject Candidate
                          </DropdownMenuItem>
                        </DropdownMenuContent>
                      </DropdownMenu>
                    </TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
        </div>
      )}
    </div>
  );
}
