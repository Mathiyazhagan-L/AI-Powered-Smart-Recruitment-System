"use client";

import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { useUser } from "@/lib/hooks/useAuth";
import { useGetEducation, useCreateEducation, useUpdateEducation, useDeleteEducation, CandidateEducation } from "@/lib/hooks/useProfile";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent } from "@/components/ui/card";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Loader2, Plus, Pencil, Trash2, GraduationCap } from "lucide-react";
import { toast } from "sonner";
import { Skeleton } from "@/components/ui/skeleton";

const educationSchema = z.object({
  degree: z.string().min(2, "Degree must be at least 2 characters"),
  institution: z.string().min(2, "Institution must be at least 2 characters"),
  department: z.string().optional().nullable(),
  cgpa: z.coerce.number().min(0).max(10).optional().or(z.literal("")),
  start_year: z.coerce.number().min(1900),
  end_year: z.coerce.number().min(1900).optional().or(z.literal("")),
  description: z.string().optional().nullable(),
}).refine(data => !data.end_year || data.end_year >= data.start_year, {
  message: "End year must be greater than or equal to start year",
  path: ["end_year"]
});

type EducationFormValues = z.infer<typeof educationSchema>;

export default function ProfileEducationPage() {
  const { data: user } = useUser();
  const { data: educationList, isLoading } = useGetEducation(user?.id);
  const createEducation = useCreateEducation();
  const updateEducation = useUpdateEducation();
  const deleteEducation = useDeleteEducation();
  
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [editingItem, setEditingItem] = useState<CandidateEducation | null>(null);

  const form = useForm<EducationFormValues>({
    resolver: zodResolver(educationSchema),
    defaultValues: {
      degree: "",
      institution: "",
      department: "",
      cgpa: "",
      start_year: new Date().getFullYear(),
      end_year: "",
      description: "",
    },
  });

  const openAddDialog = () => {
    setEditingItem(null);
    form.reset({
      degree: "",
      institution: "",
      department: "",
      cgpa: "",
      start_year: new Date().getFullYear(),
      end_year: "",
      description: "",
    });
    setIsDialogOpen(true);
  };

  const openEditDialog = (item: CandidateEducation) => {
    setEditingItem(item);
    form.reset({
      degree: item.degree,
      institution: item.institution,
      department: item.department || "",
      cgpa: item.cgpa || "",
      start_year: item.start_year || new Date().getFullYear(),
      end_year: item.end_year || "",
      description: item.description || "",
    });
    setIsDialogOpen(true);
  };

  const onSubmit = async (data: EducationFormValues) => {
    if (!user) return;
    
    const payload = {
      ...data,
      user_id: user.id,
      cgpa: data.cgpa === "" ? null : Number(data.cgpa),
      end_year: data.end_year === "" ? null : Number(data.end_year),
    };

    try {
      if (editingItem) {
        await updateEducation.mutateAsync({ id: editingItem.id, payload });
        toast.success("Education updated successfully");
      } else {
        await createEducation.mutateAsync(payload);
        toast.success("Education added successfully");
      }
      setIsDialogOpen(false);
    } catch (error: any) {
      toast.error(error.response?.data?.detail || "Failed to save education");
    }
  };

  const handleDelete = async (id: number) => {
    if (confirm("Are you sure you want to delete this education entry?")) {
      try {
        await deleteEducation.mutateAsync(id);
        toast.success("Education deleted successfully");
      } catch (error) {
        toast.error("Failed to delete education");
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
          <h2 className="text-2xl font-bold tracking-tight">Education</h2>
          <p className="text-muted-foreground">Add your academic background and degrees.</p>
        </div>
        <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
          <DialogTrigger asChild>
            <Button onClick={openAddDialog} className="gap-2">
              <Plus className="h-4 w-4" /> Add Education
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-xl">
            <DialogHeader>
              <DialogTitle>{editingItem ? "Edit Education" : "Add Education"}</DialogTitle>
            </DialogHeader>
            <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4 mt-4">
              <div className="space-y-2">
                <Label htmlFor="institution">Institution / University</Label>
                <Input id="institution" {...form.register("institution")} placeholder="e.g. Stanford University" />
                {form.formState.errors.institution && <p className="text-xs text-destructive">{form.formState.errors.institution.message}</p>}
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="degree">Degree</Label>
                  <Input id="degree" {...form.register("degree")} placeholder="e.g. Bachelor of Science" />
                  {form.formState.errors.degree && <p className="text-xs text-destructive">{form.formState.errors.degree.message}</p>}
                </div>
                <div className="space-y-2">
                  <Label htmlFor="department">Field of Study</Label>
                  <Input id="department" {...form.register("department")} placeholder="e.g. Computer Science" />
                </div>
              </div>
              <div className="grid grid-cols-3 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="start_year">Start Year</Label>
                  <Input id="start_year" type="number" {...form.register("start_year")} />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="end_year">End Year (or Expected)</Label>
                  <Input id="end_year" type="number" {...form.register("end_year")} placeholder="e.g. 2024" />
                  {form.formState.errors.end_year && <p className="text-xs text-destructive">{form.formState.errors.end_year.message}</p>}
                </div>
                <div className="space-y-2">
                  <Label htmlFor="cgpa">CGPA / Grade</Label>
                  <Input id="cgpa" type="number" step="0.01" {...form.register("cgpa")} placeholder="e.g. 3.8" />
                </div>
              </div>
              <div className="space-y-2">
                <Label htmlFor="description">Description (Optional)</Label>
                <Textarea id="description" {...form.register("description")} placeholder="Achievements, relevant courses..." />
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

      {!educationList?.length ? (
        <Card className="border-dashed shadow-sm">
          <CardContent className="flex flex-col items-center justify-center p-12 text-center">
            <div className="bg-primary/10 p-4 rounded-full mb-4">
              <GraduationCap className="h-8 w-8 text-primary" />
            </div>
            <h3 className="text-lg font-semibold mb-2">No education added yet</h3>
            <p className="text-muted-foreground mb-4 max-w-sm">
              Add your educational background to help recruiters understand your academic history.
            </p>
            <Button onClick={openAddDialog} variant="outline" className="gap-2">
              <Plus className="h-4 w-4" /> Add your first education
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-4">
          {educationList.map((edu) => (
            <Card key={edu.id} className="group relative shadow-sm">
              <CardContent className="p-6">
                <div className="flex justify-between items-start">
                  <div>
                    <h3 className="text-lg font-semibold">{edu.degree} {edu.department ? `in ${edu.department}` : ''}</h3>
                    <p className="text-muted-foreground">{edu.institution}</p>
                    <p className="text-sm text-muted-foreground mt-1">
                      {edu.start_year} - {edu.end_year || "Present"} {edu.cgpa && `• CGPA: ${edu.cgpa}`}
                    </p>
                  </div>
                  <div className="flex opacity-0 group-hover:opacity-100 transition-opacity gap-2">
                    <Button variant="ghost" size="icon" onClick={() => openEditDialog(edu)}>
                      <Pencil className="h-4 w-4 text-muted-foreground" />
                    </Button>
                    <Button variant="ghost" size="icon" onClick={() => handleDelete(edu.id)}>
                      <Trash2 className="h-4 w-4 text-destructive" />
                    </Button>
                  </div>
                </div>
                {edu.description && (
                  <p className="mt-4 text-sm whitespace-pre-wrap">{edu.description}</p>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
