"use client";

import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { useUser } from "@/lib/hooks/useAuth";
import { useGetExperience, useCreateExperience, useUpdateExperience, useDeleteExperience, CandidateExperience } from "@/lib/hooks/useProfile";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent } from "@/components/ui/card";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Loader2, Plus, Pencil, Trash2, Briefcase } from "lucide-react";
import { toast } from "sonner";
import { Skeleton } from "@/components/ui/skeleton";

const experienceSchema = z.object({
  company_name: z.string().min(2, "Company name must be at least 2 characters"),
  job_title: z.string().min(2, "Job title must be at least 2 characters"),
  employment_type: z.string().min(2, "Employment type is required"),
  start_date: z.string().min(10, "Start date is required"),
  end_date: z.string().optional().nullable(),
  currently_working: z.boolean().default(false),
  description: z.string().optional().nullable(),
}).refine(data => data.currently_working || (data.end_date && data.end_date.length >= 10), {
  message: "End date is required if you are not currently working here",
  path: ["end_date"]
}).refine(data => !data.end_date || data.end_date >= data.start_date, {
  message: "End date must be after start date",
  path: ["end_date"]
});

type ExperienceFormValues = z.infer<typeof experienceSchema>;

export default function ProfileExperiencePage() {
  const { data: user } = useUser();
  const { data: experienceList, isLoading } = useGetExperience(user?.id);
  const createExperience = useCreateExperience();
  const updateExperience = useUpdateExperience();
  const deleteExperience = useDeleteExperience();
  
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [editingItem, setEditingItem] = useState<CandidateExperience | null>(null);

  const form = useForm<ExperienceFormValues>({
    resolver: zodResolver(experienceSchema),
    defaultValues: {
      company_name: "",
      job_title: "",
      employment_type: "Full-time",
      start_date: "",
      end_date: "",
      currently_working: false,
      description: "",
    },
  });

  const currentlyWorking = form.watch("currently_working");

  const openAddDialog = () => {
    setEditingItem(null);
    form.reset({
      company_name: "",
      job_title: "",
      employment_type: "Full-time",
      start_date: "",
      end_date: "",
      currently_working: false,
      description: "",
    });
    setIsDialogOpen(true);
  };

  const openEditDialog = (item: CandidateExperience) => {
    setEditingItem(item);
    form.reset({
      company_name: item.company_name,
      job_title: item.job_title,
      employment_type: item.employment_type,
      start_date: item.start_date,
      end_date: item.end_date || "",
      currently_working: item.currently_working,
      description: item.description || "",
    });
    setIsDialogOpen(true);
  };

  const onSubmit = async (data: ExperienceFormValues) => {
    if (!user) return;
    
    const payload = {
      ...data,
      user_id: user.id,
      end_date: data.currently_working ? null : (data.end_date || null),
    };

    try {
      if (editingItem) {
        await updateExperience.mutateAsync({ id: editingItem.id, payload });
        toast.success("Experience updated successfully");
      } else {
        await createExperience.mutateAsync(payload);
        toast.success("Experience added successfully");
      }
      setIsDialogOpen(false);
    } catch (error: any) {
      toast.error(error.response?.data?.detail || "Failed to save experience");
    }
  };

  const handleDelete = async (id: number) => {
    if (confirm("Are you sure you want to delete this experience entry?")) {
      try {
        await deleteExperience.mutateAsync(id);
        toast.success("Experience deleted successfully");
      } catch (error) {
        toast.error("Failed to delete experience");
      }
    }
  };

  if (isLoading) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-[100px] w-full" />
        <Skeleton className="h-[100px] w-full" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold tracking-tight">Experience</h2>
          <p className="text-muted-foreground">Add your professional work experience.</p>
        </div>
        <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
          <DialogTrigger asChild>
            <Button onClick={openAddDialog} className="gap-2">
              <Plus className="h-4 w-4" /> Add Experience
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-xl">
            <DialogHeader>
              <DialogTitle>{editingItem ? "Edit Experience" : "Add Experience"}</DialogTitle>
            </DialogHeader>
            <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4 mt-4">
              <div className="space-y-2">
                <Label htmlFor="job_title">Job Title</Label>
                <Input id="job_title" {...form.register("job_title")} placeholder="e.g. Senior Software Engineer" />
                {form.formState.errors.job_title && <p className="text-xs text-destructive">{form.formState.errors.job_title.message}</p>}
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="company_name">Company Name</Label>
                  <Input id="company_name" {...form.register("company_name")} placeholder="e.g. Google" />
                  {form.formState.errors.company_name && <p className="text-xs text-destructive">{form.formState.errors.company_name.message}</p>}
                </div>
                <div className="space-y-2">
                  <Label htmlFor="employment_type">Employment Type</Label>
                  <Input id="employment_type" {...form.register("employment_type")} placeholder="e.g. Full-time, Internship" />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4 items-end">
                <div className="space-y-2">
                  <Label htmlFor="start_date">Start Date</Label>
                  <Input id="start_date" type="date" {...form.register("start_date")} />
                  {form.formState.errors.start_date && <p className="text-xs text-destructive">{form.formState.errors.start_date.message}</p>}
                </div>
                <div className="space-y-2">
                  <Label htmlFor="end_date">End Date</Label>
                  <Input id="end_date" type="date" {...form.register("end_date")} disabled={currentlyWorking} />
                  {form.formState.errors.end_date && <p className="text-xs text-destructive">{form.formState.errors.end_date.message}</p>}
                </div>
              </div>
              <div className="flex items-center space-x-2 pt-2">
                <input 
                  type="checkbox" 
                  id="currently_working" 
                  className="h-4 w-4 rounded border-gray-300 text-primary focus:ring-primary"
                  {...form.register("currently_working")} 
                />
                <Label htmlFor="currently_working">I currently work here</Label>
              </div>
              <div className="space-y-2">
                <Label htmlFor="description">Description (Optional)</Label>
                <Textarea id="description" {...form.register("description")} placeholder="Responsibilities and achievements..." rows={4} />
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

      {!experienceList?.length ? (
        <Card className="border-dashed shadow-sm">
          <CardContent className="flex flex-col items-center justify-center p-12 text-center">
            <div className="bg-primary/10 p-4 rounded-full mb-4">
              <Briefcase className="h-8 w-8 text-primary" />
            </div>
            <h3 className="text-lg font-semibold mb-2">No experience added yet</h3>
            <p className="text-muted-foreground mb-4 max-w-sm">
              Showcase your career progression by adding your work history.
            </p>
            <Button onClick={openAddDialog} variant="outline" className="gap-2">
              <Plus className="h-4 w-4" /> Add your first role
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-4">
          {experienceList.map((exp) => (
            <Card key={exp.id} className="group relative shadow-sm">
              <CardContent className="p-6">
                <div className="flex justify-between items-start">
                  <div>
                    <h3 className="text-lg font-semibold">{exp.job_title}</h3>
                    <p className="text-muted-foreground font-medium">{exp.company_name} • {exp.employment_type}</p>
                    <p className="text-sm text-muted-foreground mt-1">
                      {new Date(exp.start_date).toLocaleDateString()} - {exp.currently_working ? "Present" : exp.end_date ? new Date(exp.end_date).toLocaleDateString() : ""}
                    </p>
                  </div>
                  <div className="flex opacity-0 group-hover:opacity-100 transition-opacity gap-2">
                    <Button variant="ghost" size="icon" onClick={() => openEditDialog(exp)}>
                      <Pencil className="h-4 w-4 text-muted-foreground" />
                    </Button>
                    <Button variant="ghost" size="icon" onClick={() => handleDelete(exp.id)}>
                      <Trash2 className="h-4 w-4 text-destructive" />
                    </Button>
                  </div>
                </div>
                {exp.description && (
                  <p className="mt-4 text-sm whitespace-pre-wrap">{exp.description}</p>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
