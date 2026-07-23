"use client";

import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { useUser } from "@/lib/hooks/useAuth";
import { useGetProjects, useCreateProject, useUpdateProject, useDeleteProject, CandidateProject } from "@/lib/hooks/useProfile";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent } from "@/components/ui/card";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Loader2, Plus, Pencil, Trash2, FolderOpen, ExternalLink, GitBranch } from "lucide-react";
import { toast } from "sonner";
import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";

const projectSchema = z.object({
  project_name: z.string().min(2, "Project name must be at least 2 characters"),
  description: z.string().optional().nullable(),
  technologies: z.string(), // We will split this by comma
  github_url: z.string().url("Must be a valid URL").optional().or(z.literal("")).nullable(),
  live_url: z.string().url("Must be a valid URL").optional().or(z.literal("")).nullable(),
  start_date: z.string().optional().nullable(),
  end_date: z.string().optional().nullable(),
}).refine(data => !data.end_date || (data.start_date && data.end_date >= data.start_date), {
  message: "End date must be after start date",
  path: ["end_date"]
});

type ProjectFormValues = z.infer<typeof projectSchema>;

export default function ProfileProjectsPage() {
  const { data: user } = useUser();
  const { data: projectsList, isLoading } = useGetProjects(user?.id);
  const createProject = useCreateProject();
  const updateProject = useUpdateProject();
  const deleteProject = useDeleteProject();
  
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [editingItem, setEditingItem] = useState<CandidateProject | null>(null);

  const form = useForm<ProjectFormValues>({
    resolver: zodResolver(projectSchema),
    defaultValues: {
      project_name: "",
      description: "",
      technologies: "",
      github_url: "",
      live_url: "",
      start_date: "",
      end_date: "",
    },
  });

  const openAddDialog = () => {
    setEditingItem(null);
    form.reset({
      project_name: "",
      description: "",
      technologies: "",
      github_url: "",
      live_url: "",
      start_date: "",
      end_date: "",
    });
    setIsDialogOpen(true);
  };

  const openEditDialog = (item: CandidateProject) => {
    setEditingItem(item);
    form.reset({
      project_name: item.project_name,
      description: item.description || "",
      technologies: item.technologies.join(", "),
      github_url: item.github_url || "",
      live_url: item.live_url || "",
      start_date: item.start_date || "",
      end_date: item.end_date || "",
    });
    setIsDialogOpen(true);
  };

  const onSubmit = async (data: ProjectFormValues) => {
    if (!user) return;
    
    // Convert comma separated string to array and clean up
    const techArray = data.technologies
      .split(",")
      .map(t => t.trim())
      .filter(t => t.length > 0);

    const payload = {
      ...data,
      user_id: user.id,
      technologies: techArray,
      github_url: data.github_url || null,
      live_url: data.live_url || null,
      start_date: data.start_date || null,
      end_date: data.end_date || null,
    };

    try {
      if (editingItem) {
        await updateProject.mutateAsync({ id: editingItem.id, payload });
        toast.success("Project updated successfully");
      } else {
        await createProject.mutateAsync(payload);
        toast.success("Project added successfully");
      }
      setIsDialogOpen(false);
    } catch (error: any) {
      toast.error(error.response?.data?.detail || "Failed to save project");
    }
  };

  const handleDelete = async (id: number) => {
    if (confirm("Are you sure you want to delete this project?")) {
      try {
        await deleteProject.mutateAsync(id);
        toast.success("Project deleted successfully");
      } catch (error) {
        toast.error("Failed to delete project");
      }
    }
  };

  if (isLoading) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-[150px] w-full" />
        <Skeleton className="h-[150px] w-full" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold tracking-tight">Projects</h2>
          <p className="text-muted-foreground">Showcase your personal, academic, or professional projects.</p>
        </div>
        <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
          <DialogTrigger asChild>
            <Button onClick={openAddDialog} className="gap-2">
              <Plus className="h-4 w-4" /> Add Project
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-xl">
            <DialogHeader>
              <DialogTitle>{editingItem ? "Edit Project" : "Add Project"}</DialogTitle>
            </DialogHeader>
            <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4 mt-4">
              <div className="space-y-2">
                <Label htmlFor="project_name">Project Name</Label>
                <Input id="project_name" {...form.register("project_name")} placeholder="e.g. E-Commerce Platform" />
                {form.formState.errors.project_name && <p className="text-xs text-destructive">{form.formState.errors.project_name.message}</p>}
              </div>
              <div className="space-y-2">
                <Label htmlFor="technologies">Technologies Used (comma separated)</Label>
                <Input id="technologies" {...form.register("technologies")} placeholder="e.g. React, Node.js, PostgreSQL" />
              </div>
              <div className="space-y-2">
                <Label htmlFor="description">Description</Label>
                <Textarea id="description" {...form.register("description")} placeholder="What did you build? What problems did you solve?" rows={3} />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="github_url">GitHub URL (Optional)</Label>
                  <Input id="github_url" {...form.register("github_url")} placeholder="https://github.com/..." />
                  {form.formState.errors.github_url && <p className="text-xs text-destructive">{form.formState.errors.github_url.message}</p>}
                </div>
                <div className="space-y-2">
                  <Label htmlFor="live_url">Live URL (Optional)</Label>
                  <Input id="live_url" {...form.register("live_url")} placeholder="https://..." />
                  {form.formState.errors.live_url && <p className="text-xs text-destructive">{form.formState.errors.live_url.message}</p>}
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="start_date">Start Date (Optional)</Label>
                  <Input id="start_date" type="date" {...form.register("start_date")} />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="end_date">End Date (Optional)</Label>
                  <Input id="end_date" type="date" {...form.register("end_date")} />
                  {form.formState.errors.end_date && <p className="text-xs text-destructive">{form.formState.errors.end_date.message}</p>}
                </div>
              </div>
              <div className="flex justify-end gap-2 pt-4">
                <Button type="button" variant="outline" onClick={() => setIsDialogOpen(false)}>Cancel</Button>
                <Button type="submit" disabled={form.formState.isSubmitting}>
                  {form.formState.isSubmitting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                  Save
                </Button>
              </div>
            </form>
          </DialogContent>
        </Dialog>
      </div>

      {!projectsList?.length ? (
        <Card className="border-dashed shadow-sm">
          <CardContent className="flex flex-col items-center justify-center p-12 text-center">
            <div className="bg-primary/10 p-4 rounded-full mb-4">
              <FolderOpen className="h-8 w-8 text-primary" />
            </div>
            <h3 className="text-lg font-semibold mb-2">No projects added yet</h3>
            <p className="text-muted-foreground mb-4 max-w-sm">
              Showcase your technical skills with real-world examples.
            </p>
            <Button onClick={openAddDialog} variant="outline" className="gap-2">
              <Plus className="h-4 w-4" /> Add your first project
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4 md:grid-cols-2">
          {projectsList.map((project) => (
            <Card key={project.id} className="group relative shadow-sm flex flex-col">
              <CardContent className="p-6 flex-1 flex flex-col">
                <div className="flex justify-between items-start mb-2">
                  <h3 className="text-xl font-bold line-clamp-1">{project.project_name}</h3>
                  <div className="flex opacity-0 group-hover:opacity-100 transition-opacity shrink-0 ml-2">
                    <Button variant="ghost" size="icon" className="h-8 w-8" onClick={() => openEditDialog(project)}>
                      <Pencil className="h-4 w-4 text-muted-foreground" />
                    </Button>
                    <Button variant="ghost" size="icon" className="h-8 w-8 hover:text-destructive" onClick={() => handleDelete(project.id)}>
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
                
                {project.start_date && (
                  <p className="text-xs text-muted-foreground mb-3">
                    {new Date(project.start_date).toLocaleDateString()} {project.end_date ? `- ${new Date(project.end_date).toLocaleDateString()}` : "- Present"}
                  </p>
                )}

                <p className="text-sm text-muted-foreground mb-4 flex-1 line-clamp-3">
                  {project.description || "No description provided."}
                </p>

                <div className="flex flex-wrap gap-2 mb-4 mt-auto">
                  {project.technologies.slice(0, 5).map((tech, i) => (
                    <Badge key={i} variant="secondary" className="text-xs font-normal">
                      {tech}
                    </Badge>
                  ))}
                  {project.technologies.length > 5 && (
                    <Badge variant="outline" className="text-xs font-normal">
                      +{project.technologies.length - 5} more
                    </Badge>
                  )}
                </div>

                <div className="flex items-center gap-3 pt-4 border-t border-border/50">
                  {project.github_url && (
                    <a href={project.github_url} target="_blank" rel="noopener noreferrer" className="text-muted-foreground hover:text-foreground transition-colors flex items-center gap-1.5 text-sm font-medium">
                      <GitBranch className="h-4 w-4" /> Code
                    </a>
                  )}
                  {project.live_url && (
                    <a href={project.live_url} target="_blank" rel="noopener noreferrer" className="text-muted-foreground hover:text-foreground transition-colors flex items-center gap-1.5 text-sm font-medium">
                      <ExternalLink className="h-4 w-4" /> Live Demo
                    </a>
                  )}
                  {!project.github_url && !project.live_url && (
                    <span className="text-xs text-muted-foreground italic">No links provided</span>
                  )}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
