"use client";

import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { useUser } from "@/lib/hooks/useAuth";
import { useGetSkills, useCreateSkill, useUpdateSkill, useDeleteSkill, CandidateSkill } from "@/lib/hooks/useProfile";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent } from "@/components/ui/card";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Loader2, Plus, Pencil, Trash2, Code, Target } from "lucide-react";
import { toast } from "sonner";
import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";

const skillSchema = z.object({
  skill_name: z.string().min(1, "Skill name is required"),
  skill_category: z.string().optional().nullable(),
  proficiency_level: z.string().min(1, "Proficiency level is required"),
  years_of_experience: z.coerce.number().min(0, "Cannot be negative"),
});

type SkillFormValues = z.infer<typeof skillSchema>;

export default function ProfileSkillsPage() {
  const { data: user } = useUser();
  const { data: skillsList, isLoading } = useGetSkills(user?.id);
  const createSkill = useCreateSkill();
  const updateSkill = useUpdateSkill();
  const deleteSkill = useDeleteSkill();
  
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [editingItem, setEditingItem] = useState<CandidateSkill | null>(null);

  const form = useForm<SkillFormValues>({
    resolver: zodResolver(skillSchema),
    defaultValues: {
      skill_name: "",
      skill_category: "",
      proficiency_level: "intermediate",
      years_of_experience: 1,
    },
  });

  const openAddDialog = () => {
    setEditingItem(null);
    form.reset({
      skill_name: "",
      skill_category: "",
      proficiency_level: "intermediate",
      years_of_experience: 1,
    });
    setIsDialogOpen(true);
  };

  const openEditDialog = (item: CandidateSkill) => {
    setEditingItem(item);
    form.reset({
      skill_name: item.skill_name,
      skill_category: item.skill_category || "",
      proficiency_level: item.proficiency_level || "intermediate",
      years_of_experience: item.years_of_experience,
    });
    setIsDialogOpen(true);
  };

  const onSubmit = async (data: SkillFormValues) => {
    if (!user) return;
    
    const payload = {
      ...data,
      user_id: user.id,
    };

    try {
      if (editingItem) {
        await updateSkill.mutateAsync({ id: editingItem.id, payload });
        toast.success("Skill updated successfully");
      } else {
        await createSkill.mutateAsync(payload);
        toast.success("Skill added successfully");
      }
      setIsDialogOpen(false);
    } catch (error: any) {
      toast.error(error.response?.data?.detail || "Failed to save skill");
    }
  };

  const handleDelete = async (id: number) => {
    if (confirm("Are you sure you want to delete this skill?")) {
      try {
        await deleteSkill.mutateAsync(id);
        toast.success("Skill deleted successfully");
      } catch (error) {
        toast.error("Failed to delete skill");
      }
    }
  };

  const getProficiencyColor = (level: string) => {
    switch (level?.toLowerCase()) {
      case "expert": return "bg-green-100 text-green-800 border-green-200";
      case "advanced": return "bg-blue-100 text-blue-800 border-blue-200";
      case "intermediate": return "bg-yellow-100 text-yellow-800 border-yellow-200";
      case "beginner": return "bg-slate-100 text-slate-800 border-slate-200";
      default: return "bg-primary/10 text-primary border-primary/20";
    }
  };

  if (isLoading) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-[200px] w-full" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold tracking-tight">Skills</h2>
          <p className="text-muted-foreground">Highlight your technical and soft skills.</p>
        </div>
        <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
          <DialogTrigger asChild>
            <Button onClick={openAddDialog} className="gap-2">
              <Plus className="h-4 w-4" /> Add Skill
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>{editingItem ? "Edit Skill" : "Add Skill"}</DialogTitle>
            </DialogHeader>
            <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4 mt-4">
              <div className="space-y-2">
                <Label htmlFor="skill_name">Skill Name</Label>
                <Input id="skill_name" {...form.register("skill_name")} placeholder="e.g. React, Python, Leadership" />
                {form.formState.errors.skill_name && <p className="text-xs text-destructive">{form.formState.errors.skill_name.message}</p>}
              </div>
              <div className="space-y-2">
                <Label htmlFor="skill_category">Category (Optional)</Label>
                <Input id="skill_category" {...form.register("skill_category")} placeholder="e.g. Frontend, Backend, Soft Skill" />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="proficiency_level">Proficiency Level</Label>
                  <Select 
                    value={form.watch("proficiency_level") || "intermediate"} 
                    onValueChange={(val) => form.setValue("proficiency_level", val)}
                  >
                    <SelectTrigger id="proficiency_level">
                      <SelectValue placeholder="Select level" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="beginner">Beginner</SelectItem>
                      <SelectItem value="intermediate">Intermediate</SelectItem>
                      <SelectItem value="advanced">Advanced</SelectItem>
                      <SelectItem value="expert">Expert</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="years_of_experience">Years of Experience</Label>
                  <Input id="years_of_experience" type="number" {...form.register("years_of_experience")} min="0" step="1" />
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

      {!skillsList?.length ? (
        <Card className="border-dashed shadow-sm">
          <CardContent className="flex flex-col items-center justify-center p-12 text-center">
            <div className="bg-primary/10 p-4 rounded-full mb-4">
              <Code className="h-8 w-8 text-primary" />
            </div>
            <h3 className="text-lg font-semibold mb-2">No skills added yet</h3>
            <p className="text-muted-foreground mb-4 max-w-sm">
              List your proficiencies to match with the right jobs.
            </p>
            <Button onClick={openAddDialog} variant="outline" className="gap-2">
              <Plus className="h-4 w-4" /> Add your first skill
            </Button>
          </CardContent>
        </Card>
      ) : (
        <Card className="shadow-sm">
          <CardContent className="p-6">
            <div className="flex flex-wrap gap-3">
              {skillsList.map((skill) => (
                <div 
                  key={skill.id} 
                  className="group flex items-center gap-2 bg-background border rounded-full pl-3 pr-1 py-1 shadow-sm hover:border-primary/50 transition-colors"
                >
                  <div className="flex flex-col">
                    <span className="font-semibold text-sm leading-none">{skill.skill_name}</span>
                    <span className="text-[10px] text-muted-foreground mt-1">
                      {skill.years_of_experience} yrs {skill.skill_category ? `• ${skill.skill_category}` : ''}
                    </span>
                  </div>
                  <Badge variant="outline" className={`ml-2 border ${getProficiencyColor(skill.proficiency_level || '')}`}>
                    {skill.proficiency_level}
                  </Badge>
                  <div className="flex opacity-0 group-hover:opacity-100 transition-opacity ml-1">
                    <Button variant="ghost" size="icon" className="h-6 w-6 rounded-full" onClick={() => openEditDialog(skill)}>
                      <Pencil className="h-3 w-3" />
                    </Button>
                    <Button variant="ghost" size="icon" className="h-6 w-6 rounded-full hover:text-destructive" onClick={() => handleDelete(skill.id)}>
                      <Trash2 className="h-3 w-3" />
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
