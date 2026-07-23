"use client";

import React, { useState, useEffect } from "react";
import { useGetJobFeed, useGetEligibility, useApplyJob, useToggleSaveJob, useGetSavedJobs, useGetMyApplications, Job } from "@/lib/hooks/useJobs";
import { useUser } from "@/lib/hooks/useAuth";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Search, MapPin, Briefcase, DollarSign, Bookmark, BookmarkCheck, AlertCircle, Building2, Layers, CheckCircle2 } from "lucide-react";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from "@/components/ui/dialog";
import { toast } from "sonner";
import { cn } from "@/lib/utils";

// Make a debounced hook inline for simplicity
function useDebounce<T>(value: T, delay: number): T {
  const [debouncedValue, setDebouncedValue] = useState<T>(value);
  useEffect(() => {
    const handler = setTimeout(() => setDebouncedValue(value), delay);
    return () => clearTimeout(handler);
  }, [value, delay]);
  return debouncedValue;
}

export default function JobsPage() {
  const { data: user } = useUser();
  const candidateId = user?.id;

  // Filters State
  const [searchQuery, setSearchQuery] = useState("");
  useEffect(() => {
    if (typeof window !== "undefined") {
      const params = new URLSearchParams(window.location.search);
      const search = params.get("search");
      if (search) {
        setSearchQuery(search);
      }
    }
  }, []);
  const debouncedSearch = useDebounce(searchQuery, 500);
  const [location, setLocation] = useState("");
  const debouncedLocation = useDebounce(location, 500);
  const [jobType, setJobType] = useState("");
  const [experience, setExperience] = useState("");
  const [workMode, setWorkMode] = useState("");
  
  // Modals & Selection
  const [selectedJob, setSelectedJob] = useState<Job | null>(null);
  const [isApplyModalOpen, setIsApplyModalOpen] = useState(false);

  // Queries
  const { data: jobs, isLoading, error } = useGetJobFeed(candidateId, {
    search_query: debouncedSearch || undefined,
    location: debouncedLocation || undefined,
    job_type: jobType || undefined,
    experience: experience || undefined,
    work_mode: workMode || undefined,
  });

  const { data: savedJobsList } = useGetSavedJobs(candidateId);
  const { data: applications } = useGetMyApplications(candidateId);
  const { data: eligibility } = useGetEligibility(candidateId);
  
  // Mutations
  const applyMutation = useApplyJob();
  const toggleSaveMutation = useToggleSaveJob();

  // Derived state
  const savedJobIds = new Set(savedJobsList?.map((j) => j.id) || []);
  const appliedJobIds = new Set(applications?.map((a) => a.job_id) || []);
  
  // Guard profile
  const isProfileIncomplete = eligibility?.profile_complete === false;

  const handleApplyClick = (job: Job) => {
    if (isProfileIncomplete) {
      toast.error("Complete your profile (at least 50%) before applying.");
      return;
    }
    if (!eligibility?.resume_uploaded) {
      toast.error("Please upload and parse your resume before applying.");
      return;
    }
    setSelectedJob(job);
    setIsApplyModalOpen(true);
  };

  const confirmApply = async () => {
    if (!selectedJob || !candidateId) return;
    try {
      await applyMutation.mutateAsync({ jobId: selectedJob.id, candidateId });
      toast.success(`Successfully applied to ${selectedJob.title}`);
      setIsApplyModalOpen(false);
    } catch (err: any) {
      toast.error(err.response?.data?.detail || "Failed to apply");
    }
  };

  const handleToggleSave = async (jobId: number, currentlySaved: boolean) => {
    if (!candidateId) return;
    try {
      await toggleSaveMutation.mutateAsync({ jobId, candidateId, isSaved: currentlySaved });
      if (currentlySaved) {
        toast.info("Job removed from saved");
      } else {
        toast.success("Job saved successfully");
      }
    } catch (err) {
      toast.error("Failed to toggle save");
    }
  };

  // Match Score Color Helper
  const getMatchColor = (score: number) => {
    if (score >= 80) return "text-green-500 bg-green-500/10 border-green-500/20";
    if (score >= 50) return "text-yellow-500 bg-yellow-500/10 border-yellow-500/20";
    return "text-red-500 bg-red-500/10 border-red-500/20";
  };

  return (
    <div className="flex flex-col md:flex-row gap-6">
      
      {/* LEFT SIDEBAR: Filters */}
      <div className="w-full md:w-64 shrink-0 space-y-6">
        <div className="bg-card border rounded-xl p-5 space-y-6 sticky top-24">
          <div>
            <h3 className="font-semibold mb-3 flex items-center gap-2"><Search className="w-4 h-4" /> Filters</h3>
            
            <div className="space-y-4">
              <div className="space-y-2">
                <label className="text-xs font-medium text-muted-foreground">Search Roles</label>
                <Input 
                  placeholder="e.g. AI Engineer..." 
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="bg-background"
                />
              </div>

              <div className="space-y-2">
                <label className="text-xs font-medium text-muted-foreground">Location</label>
                <div className="relative">
                  <MapPin className="absolute left-3 top-2.5 w-4 h-4 text-muted-foreground" />
                  <Input 
                    placeholder="City, Country..." 
                    className="pl-9 bg-background"
                    value={location}
                    onChange={(e) => setLocation(e.target.value)}
                  />
                </div>
              </div>

              <div className="space-y-2">
                <label className="text-xs font-medium text-muted-foreground">Work Mode</label>
                <select 
                  className="flex h-10 w-full items-center justify-between rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                  value={workMode}
                  onChange={(e) => setWorkMode(e.target.value)}
                >
                  <option value="">Any</option>
                  <option value="Remote">Remote</option>
                  <option value="Hybrid">Hybrid</option>
                  <option value="Onsite">On-site</option>
                </select>
              </div>

              <div className="space-y-2">
                <label className="text-xs font-medium text-muted-foreground">Experience Level</label>
                <select 
                  className="flex h-10 w-full items-center justify-between rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                  value={experience}
                  onChange={(e) => setExperience(e.target.value)}
                >
                  <option value="">Any</option>
                  <option value="Fresher">Fresher (0-1 yrs)</option>
                  <option value="Mid">Mid (2-5 yrs)</option>
                  <option value="Senior">Senior (5+ yrs)</option>
                </select>
              </div>

            </div>
          </div>
        </div>
      </div>

      {/* RIGHT SIDE: Job List */}
      <div className="flex-1 space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-2xl font-bold tracking-tight">Job Openings</h2>
          <Badge variant="outline" className="px-3 py-1 font-medium bg-muted/50">
            {jobs?.length || 0} Results
          </Badge>
        </div>

        {isProfileIncomplete && (
          <div className="bg-destructive/10 text-destructive border border-destructive/20 p-4 rounded-xl flex items-start gap-3">
            <AlertCircle className="w-5 h-5 mt-0.5 shrink-0" />
            <div className="text-sm">
              <p className="font-semibold">Profile Incomplete</p>
              <p>Your profile is currently below the 50% completion threshold. You must complete your basic details and upload a resume before you can apply to jobs.</p>
            </div>
          </div>
        )}

        {isLoading ? (
          <div className="space-y-4">
            {[1, 2, 3].map(i => (
              <Card key={i} className="animate-pulse h-40 bg-muted/20" />
            ))}
          </div>
        ) : error ? (
          <div className="text-center py-10 text-destructive bg-destructive/10 rounded-xl border border-destructive/20">
            Failed to load jobs.
          </div>
        ) : !jobs || jobs.length === 0 ? (
          <div className="text-center py-20 bg-muted/10 rounded-xl border border-dashed flex flex-col items-center">
            <Briefcase className="w-12 h-12 text-muted-foreground/50 mb-4" />
            <h3 className="text-lg font-semibold text-foreground">No jobs found</h3>
            <p className="text-muted-foreground text-sm max-w-sm mt-2">
              We couldn't find any jobs matching your current filters. Try adjusting your search criteria.
            </p>
          </div>
        ) : (
          <div className="space-y-4">
            {jobs.map((job) => {
              const rawMatchScore = job.match_score || 0;
              const matchScore = Math.max(0, Math.min(100, rawMatchScore));
              const isApplied = appliedJobIds.has(job.id);
              const isSaved = savedJobIds.has(job.id);
              
              return (
                <Card key={job.id} className="group overflow-hidden hover:border-primary/50 transition-colors">
                  <CardContent className="p-6">
                    <div className="flex flex-col sm:flex-row gap-6">
                      
                      {/* Logo Placeholder */}
                      <div className="w-16 h-16 rounded-xl bg-primary/10 flex items-center justify-center shrink-0 border">
                        <Building2 className="w-8 h-8 text-primary" />
                      </div>

                      <div className="flex-1 space-y-3">
                        <div className="flex items-start justify-between">
                          <div>
                            <h3 className="text-xl font-bold group-hover:text-primary transition-colors">{job.title}</h3>
                            <div className="flex items-center gap-2 mt-1 text-sm text-muted-foreground">
                              <span>AIHire Platform</span>
                              <span>•</span>
                              <span className="flex items-center gap-1"><MapPin className="w-3.5 h-3.5" /> {job.location}</span>
                            </div>
                          </div>
                          
                          {/* Match Score Badge */}
                          <Badge variant="outline" className={cn("px-3 py-1 text-xs sm:text-sm font-semibold border shrink-0", getMatchColor(matchScore))}>
                            {matchScore}% Match
                          </Badge>
                        </div>

                        {/* Badges Row */}
                        <div className="flex flex-wrap gap-2 text-xs font-medium">
                          <span className="flex items-center gap-1.5 bg-muted px-2.5 py-1 rounded-md text-foreground">
                            <Briefcase className="w-3.5 h-3.5 text-muted-foreground" /> {job.experience}
                          </span>
                          <span className="flex items-center gap-1.5 bg-muted px-2.5 py-1 rounded-md text-foreground">
                            <DollarSign className="w-3.5 h-3.5 text-muted-foreground" /> {job.package}
                          </span>
                          <span className="flex items-center gap-1.5 bg-muted px-2.5 py-1 rounded-md text-foreground">
                            <Layers className="w-3.5 h-3.5 text-muted-foreground" /> {job.openings} Openings
                          </span>
                        </div>

                        {/* Required Skills */}
                        {job.required_skills && job.required_skills.length > 0 && (
                          <div className="flex flex-wrap gap-1.5 pt-2">
                            {job.required_skills.slice(0, 5).map(s => (
                              <Badge key={s} variant="secondary" className="bg-primary/5 hover:bg-primary/10 font-normal text-xs">{s}</Badge>
                            ))}
                            {job.required_skills.length > 5 && (
                              <Badge variant="secondary" className="bg-primary/5 font-normal text-xs">+{job.required_skills.length - 5}</Badge>
                            )}
                          </div>
                        )}
                        
                      </div>

                      {/* Action Buttons */}
                      <div className="flex sm:flex-col gap-2 shrink-0 sm:min-w-[120px]">
                        <Button 
                          className="flex-1 w-full"
                          variant={isApplied ? "outline" : "default"}
                          disabled={isApplied || isProfileIncomplete || applyMutation.isPending}
                          onClick={() => handleApplyClick(job)}
                        >
                          {isApplied ? "Applied" : "Apply Now"}
                        </Button>
                        <Button 
                          className="flex-1 w-full text-muted-foreground hover:text-foreground"
                          variant="outline"
                          onClick={() => handleToggleSave(job.id, isSaved)}
                          disabled={toggleSaveMutation.isPending}
                        >
                          {isSaved ? <BookmarkCheck className="w-4 h-4 mr-2 text-primary fill-primary" /> : <Bookmark className="w-4 h-4 mr-2" />}
                          {isSaved ? "Saved" : "Save Job"}
                        </Button>
                      </div>

                    </div>
                  </CardContent>
                </Card>
              );
            })}
          </div>
        )}
      </div>

      {/* ONE-CLICK APPLY MODAL */}
      <Dialog open={isApplyModalOpen} onOpenChange={setIsApplyModalOpen}>
        <DialogContent className="sm:max-w-[425px]">
          <DialogHeader>
            <DialogTitle>1-Click Apply</DialogTitle>
            <DialogDescription>
              You are about to apply for the <span className="font-semibold text-foreground">{selectedJob?.title}</span> position.
            </DialogDescription>
          </DialogHeader>
          <div className="py-4 space-y-4 text-sm">
            <div className="bg-muted/50 p-4 rounded-lg flex gap-3 border">
              <CheckCircle2 className="w-5 h-5 text-primary shrink-0" />
              <div>
                <p className="font-medium text-foreground">Verified Profile</p>
                <p className="text-muted-foreground mt-0.5">Your parsed resume and profile details will be submitted to the recruiter automatically.</p>
              </div>
            </div>
            <p className="text-muted-foreground">Are you sure you want to proceed? No additional cover letters or questions are required.</p>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsApplyModalOpen(false)}>Cancel</Button>
            <Button onClick={confirmApply} disabled={applyMutation.isPending}>
              {applyMutation.isPending ? "Submitting..." : "Submit Application"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
