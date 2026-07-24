"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Search, MoreHorizontal, Plus, Briefcase, Play, Pause } from "lucide-react";
import { 
  DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuLabel, 
  DropdownMenuSeparator, DropdownMenuTrigger 
} from "@/components/ui/dropdown-menu";
import { useJobs, usePublishJob, useCloseJob, useCreateJob, useDeleteJob, Job } from "@/lib/hooks/useJobs";

const getStatusColor = (status: string) => {
  switch (status) {
    case "published": return "bg-success text-success-foreground border-transparent";
    case "draft": return "bg-warning text-warning-foreground border-transparent";
    case "closed": return "bg-destructive text-destructive-foreground border-transparent";
    default: return "bg-muted text-muted-foreground";
  }
};

const triggerButtonClass =
  "inline-flex items-center justify-center rounded-md text-sm font-medium transition-colors " +
  "focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring " +
  "disabled:pointer-events-none disabled:opacity-50 hover:bg-accent hover:text-accent-foreground " +
  "h-8 w-8 p-0 opacity-0 group-hover:opacity-100";

const defaultForm = {
  title: "", description: "", required_skills: "", preferred_skills: "",
  experience: "", package: "", location: "", openings: "1", deadline: "", criteria: "",
  selection_rounds: "HR Round"
};

const formatApiError = (detail: any, fallback: string): string => {
  if (!detail) return fallback;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    return detail.map((err: any) => {
      if (typeof err === "string") return err;
      if (err && typeof err === "object") {
        const field = Array.isArray(err.loc) ? err.loc.slice(1).join(".") : "";
        return field ? `${field}: ${err.msg || "Invalid"}` : (err.msg || JSON.stringify(err));
      }
      return String(err);
    }).join("; ");
  }
  if (typeof detail === "object" && detail !== null) {
    return detail.msg || JSON.stringify(detail);
  }
  return String(detail);
};

export default function JobsPage() {
  const router = useRouter();
  const [searchTerm, setSearchTerm] = useState("");
  const [createOpen, setCreateOpen] = useState(false);
  const [form, setForm] = useState(defaultForm);
  const [formError, setFormError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const { data: jobs, isLoading } = useJobs();
  const publishJob = usePublishJob();
  const closeJob = useCloseJob();
  const deleteJob = useDeleteJob();
  const createJob = useCreateJob();

  const filteredJobs = (jobs || []).filter((j: Job) => 
    (j.title || "").toLowerCase().includes(searchTerm.toLowerCase()) || 
    (j.location || "").toLowerCase().includes(searchTerm.toLowerCase())
  );

  const handleCreate = async () => {
    if (!form.title.trim()) { setFormError("Job title is required."); return; }
    if (!form.location.trim()) { setFormError("Location is required."); return; }
    if (!form.deadline) { setFormError("Deadline is required."); return; }
    setFormError("");
    setIsSubmitting(true);
    try {
      const rounds = form.selection_rounds.split(",").map(s => s.trim()).filter(Boolean);
      await createJob.mutateAsync({
        title: form.title,
        description: form.description,
        required_skills: form.required_skills.split(",").map(s => s.trim()).filter(Boolean),
        preferred_skills: form.preferred_skills.split(",").map(s => s.trim()).filter(Boolean),
        experience: form.experience,
        package: form.package,
        location: form.location,
        openings: Number(form.openings) || 1,
        deadline: form.deadline,
        criteria: form.criteria,
        selection_rounds: rounds.length > 0 ? (rounds as any) : (["HR Round"] as any)
      });
      setForm(defaultForm);
      setCreateOpen(false);
    } catch (err: any) {
      setFormError(formatApiError(err?.response?.data?.detail, "Failed to create job."));
    } finally {
      setIsSubmitting(false);
    }
  };

  const setField = (field: keyof typeof defaultForm) => (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => 
    setForm(f => ({ ...f, [field]: e.target.value }));

  return (
    <div className="flex flex-col h-full space-y-4">
      {/* Header */}
      <div className="sticky top-0 z-10 bg-muted/20 backdrop-blur-md pb-4 border-b border-border/50 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h2 className="text-3xl font-bold tracking-tight text-foreground">Job Management</h2>
          <p className="text-muted-foreground mt-1">Create, publish, and track open roles.</p>
        </div>
        <Button className="bg-secondary text-secondary-foreground hover:bg-secondary/90" onClick={() => { setCreateOpen(true); setFormError(""); }}>
          <Plus className="mr-2 h-4 w-4" /> Create Job
        </Button>
      </div>

      {/* Search */}
      <div className="flex gap-4 py-2">
        <div className="flex flex-1 items-center max-w-md relative">
          <Search className="absolute left-3 h-4 w-4 text-muted-foreground" />
          <Input placeholder="Search jobs..." className="pl-9 bg-background" value={searchTerm} onChange={e => setSearchTerm(e.target.value)} />
        </div>
      </div>

      {/* Table */}
      <div className="border rounded-lg bg-background flex-1 overflow-auto shadow-sm">
        <Table>
          <TableHeader className="bg-muted/50 sticky top-0 z-10 backdrop-blur-sm">
            <TableRow>
              <TableHead className="w-[80px]">Job ID</TableHead>
              <TableHead>Title</TableHead>
              <TableHead>Location</TableHead>
              <TableHead>Experience</TableHead>
              <TableHead>Package</TableHead>
              <TableHead>Deadline</TableHead>
              <TableHead>Status</TableHead>
              <TableHead className="text-right">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {isLoading ? (
              <TableRow><TableCell colSpan={8} className="h-40 text-center text-muted-foreground">
                <div className="flex flex-col items-center justify-center">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mb-2"></div>
                  <p>Loading jobs...</p>
                </div>
              </TableCell></TableRow>
            ) : filteredJobs.length === 0 ? (
              <TableRow><TableCell colSpan={8} className="h-40 text-center text-muted-foreground">
                <div className="flex flex-col items-center justify-center">
                  <Briefcase className="h-8 w-8 mb-2 opacity-20" />
                  <p>No jobs found. Click "Create Job" to add one.</p>
                </div>
              </TableCell></TableRow>
            ) : (
              filteredJobs.map((job: Job) => (
                <TableRow key={job.id} className="hover:bg-muted/30 transition-colors group">
                  <TableCell className="font-medium text-muted-foreground">#{job.id}</TableCell>
                  <TableCell className="font-semibold text-foreground">{job.title}</TableCell>
                  <TableCell>{job.location}</TableCell>
                  <TableCell>{job.experience || "—"}</TableCell>
                  <TableCell>{job.package || "—"}</TableCell>
                  <TableCell className="text-muted-foreground">{job.deadline ? new Date(job.deadline).toLocaleDateString() : "—"}</TableCell>
                  <TableCell>
                    <Badge variant="secondary" className={`${getStatusColor(job.status)} uppercase text-[10px]`}>{job.status}</Badge>
                  </TableCell>
                  <TableCell className="text-right">
                    <DropdownMenu>
                      <DropdownMenuTrigger className={triggerButtonClass}>
                        <span className="sr-only">Open menu</span>
                        <MoreHorizontal className="h-4 w-4" />
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end">
                        <div className="px-2 py-1.5 text-sm font-semibold text-muted-foreground">Actions</div>
                        <DropdownMenuItem onClick={() => router.push(`/jobs/${job.id}/pipeline`)}>Hiring Pipeline</DropdownMenuItem>
                        <DropdownMenuItem onClick={() => router.push(`/jobs/${job.id}/recommendations`)}>AI Recommendations</DropdownMenuItem>
                        <DropdownMenuSeparator />
                        {job.status === "draft" && (
                          <DropdownMenuItem onClick={() => publishJob.mutate(job.id)}>
                            <Play className="mr-2 h-4 w-4 text-success" /> Publish Job
                          </DropdownMenuItem>
                        )}
                        {job.status === "published" && (
                          <DropdownMenuItem onClick={() => closeJob.mutate(job.id)}>
                            <Pause className="mr-2 h-4 w-4 text-destructive" /> Close Job
                          </DropdownMenuItem>
                        )}
                        <DropdownMenuSeparator />
                        <DropdownMenuItem onClick={() => {
                          if (confirm("Are you sure you want to delete this job?")) {
                            deleteJob.mutate(job.id);
                          }
                        }} className="text-destructive">
                          Delete Job
                        </DropdownMenuItem>
                      </DropdownMenuContent>
                    </DropdownMenu>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </div>

      {/* Create Job Dialog */}
      <Dialog open={createOpen} onOpenChange={setCreateOpen}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Create New Job</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="col-span-2">
                <Label>Job Title *</Label>
                <Input value={form.title} onChange={setField("title")} placeholder="e.g. Senior Software Engineer" className="mt-1" />
              </div>
              <div className="col-span-2">
                <Label>Job Description</Label>
                <Textarea rows={4} value={form.description} onChange={setField("description")} placeholder="Describe the role, responsibilities, and requirements..." className="mt-1" />
              </div>
              <div>
                <Label>Required Skills (comma-separated)</Label>
                <Input value={form.required_skills} onChange={setField("required_skills")} placeholder="React, TypeScript, Node.js" className="mt-1" />
              </div>
              <div>
                <Label>Preferred Skills (comma-separated)</Label>
                <Input value={form.preferred_skills} onChange={setField("preferred_skills")} placeholder="GraphQL, Docker" className="mt-1" />
              </div>
              <div>
                <Label>Experience Required</Label>
                <Input value={form.experience} onChange={setField("experience")} placeholder="e.g. 3-5 years" className="mt-1" />
              </div>
              <div>
                <Label>Package / Salary</Label>
                <Input value={form.package} onChange={setField("package")} placeholder="e.g. ₹12-18 LPA" className="mt-1" />
              </div>
              <div>
                <Label>Location *</Label>
                <Input value={form.location} onChange={setField("location")} placeholder="e.g. Bangalore, Remote" className="mt-1" />
              </div>
              <div>
                <Label>Number of Openings</Label>
                <Input type="number" min={1} value={form.openings} onChange={setField("openings")} className="mt-1" />
              </div>
              <div>
                <Label>Application Deadline *</Label>
                <Input type="date" value={form.deadline} onChange={setField("deadline")} className="mt-1" />
              </div>
              <div>
                <Label>Selection Rounds (comma-separated)</Label>
                <Input value={form.selection_rounds} onChange={setField("selection_rounds")} placeholder="e.g. HR Round, Technical Round" className="mt-1" />
              </div>
              <div>
                <Label>Additional Criteria</Label>
                <Input value={form.criteria} onChange={setField("criteria")} placeholder="Any other requirements..." className="mt-1" />
              </div>
            </div>
            {formError && <p className="text-destructive text-sm">{formError}</p>}
          </div>
          <DialogFooter className="mt-2">
            <Button variant="outline" onClick={() => setCreateOpen(false)}>Cancel</Button>
            <Button onClick={handleCreate} className="bg-secondary text-secondary-foreground" disabled={isSubmitting}>
              {isSubmitting ? "Creating..." : "Create Job"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
