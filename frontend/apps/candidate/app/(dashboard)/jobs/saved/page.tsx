"use client";

import React from "react";
import { useGetSavedJobs, useToggleSaveJob, useApplyJob, useGetEligibility, Job } from "@/lib/hooks/useJobs";
import { useUser } from "@/lib/hooks/useAuth";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { MapPin, Briefcase, DollarSign, BookmarkCheck, Building2, Layers, AlertCircle } from "lucide-react";
import { toast } from "sonner";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from "@/components/ui/dialog";
import { CheckCircle2 } from "lucide-react";

export default function SavedJobsPage() {
  const { data: user } = useUser();
  const candidateId = user?.id;

  const { data: savedJobs, isLoading, error } = useGetSavedJobs(candidateId);
  const toggleSaveMutation = useToggleSaveJob();
  const applyMutation = useApplyJob();
  const { data: eligibility } = useGetEligibility(candidateId);

  const [selectedJob, setSelectedJob] = React.useState<Job | null>(null);
  const [isApplyModalOpen, setIsApplyModalOpen] = React.useState(false);

  const isProfileIncomplete = eligibility?.profile_complete === false;

  const handleToggleSave = async (jobId: number) => {
    if (!candidateId) return;
    try {
      await toggleSaveMutation.mutateAsync({ jobId, candidateId, isSaved: true }); // Always true because it's in the saved list
      toast.info("Job removed from saved");
    } catch (err) {
      toast.error("Failed to remove saved job");
    }
  };

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

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Saved Jobs</h1>
        <p className="text-muted-foreground mt-2">Jobs you have bookmarked for later consideration.</p>
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
          {[1, 2].map(i => (
            <Card key={i} className="animate-pulse h-40 bg-muted/20" />
          ))}
        </div>
      ) : error ? (
        <div className="text-center py-10 text-destructive bg-destructive/10 rounded-xl border border-destructive/20">
          Failed to load saved jobs.
        </div>
      ) : !savedJobs || savedJobs.length === 0 ? (
        <div className="text-center py-20 bg-muted/10 rounded-xl border border-dashed flex flex-col items-center">
          <BookmarkCheck className="w-12 h-12 text-muted-foreground/50 mb-4" />
          <h3 className="text-lg font-semibold text-foreground">No saved jobs</h3>
          <p className="text-muted-foreground text-sm max-w-sm mt-2">
            You haven't saved any jobs yet. Browse the job board and click the bookmark icon to save jobs you're interested in.
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {savedJobs.map((job) => (
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
                          <Badge key={s} variant="secondary" className="bg-primary/5 font-normal text-xs">{s}</Badge>
                        ))}
                      </div>
                    )}
                    
                  </div>

                  {/* Action Buttons */}
                  <div className="flex sm:flex-col gap-2 shrink-0 sm:min-w-[120px]">
                    <Button 
                      className="flex-1 w-full"
                      disabled={isProfileIncomplete || applyMutation.isPending}
                      onClick={() => handleApplyClick(job)}
                    >
                      Apply Now
                    </Button>
                    <Button 
                      className="flex-1 w-full text-destructive hover:text-destructive hover:bg-destructive/10"
                      variant="outline"
                      onClick={() => handleToggleSave(job.id)}
                      disabled={toggleSaveMutation.isPending}
                    >
                      Remove
                    </Button>
                  </div>

                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

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
