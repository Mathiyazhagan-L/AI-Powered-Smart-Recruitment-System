"use client";

import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { useUser } from "@/lib/hooks/useAuth";
import { useGetProfile, useCreateProfile, useUpdateProfile } from "@/lib/hooks/useProfile";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Loader2, Camera, ExternalLink, RefreshCw, User } from "lucide-react";
import { toast } from "sonner";
import { Skeleton } from "@/components/ui/skeleton";
import Link from "next/link";
import { apiClient } from "@/lib/apiClient";

const profileSchema = z.object({
  full_name: z.string().min(2, "Name must be at least 2 characters"),
  email: z.string().email(),
  phone: z.string().optional().nullable(),
  date_of_birth: z.string().optional().nullable(),
  gender: z.string().optional().nullable(),
  location: z.string().optional().nullable(),
  headline: z.string().optional().nullable(),
  summary: z.string().optional().nullable(),
  linkedin_url: z.string().url("Must be a valid URL").optional().or(z.literal("")).nullable(),
  github_url: z.string().url("Must be a valid URL").optional().or(z.literal("")).nullable(),
  portfolio_url: z.string().url("Must be a valid URL").optional().or(z.literal("")).nullable(),
  leetcode_url: z.string().url("Must be a valid URL").optional().or(z.literal("")).nullable(),
  hackerrank_url: z.string().url("Must be a valid URL").optional().or(z.literal("")).nullable(),
  school_name: z.string().optional().nullable(),
  twelfth_percentage: z.preprocess((a) => (a === "" ? null : Number(a)), z.number().min(0).max(100).optional().nullable()),
  college_name: z.string().optional().nullable(),
  cgpa: z.preprocess((a) => (a === "" ? null : Number(a)), z.number().min(0).max(10).optional().nullable()),
});

type ProfileFormValues = z.infer<typeof profileSchema>;

export default function ProfileBasicDetailsPage() {
  const { data: user } = useUser();
  const { data: profile, isLoading, refetch } = useGetProfile(user?.id);
  const createProfile = useCreateProfile();
  const updateProfile = useUpdateProfile();
  const [isUploading, setIsUploading] = useState(false);
  const [isRefreshingGithub, setIsRefreshingGithub] = useState(false);

  const form = useForm<ProfileFormValues>({
    resolver: zodResolver(profileSchema),
    defaultValues: {
      full_name: "",
      email: "",
      phone: "",
      date_of_birth: "",
      gender: "",
      location: "",
      headline: "",
      summary: "",
      linkedin_url: "",
      github_url: "",
      portfolio_url: "",
      leetcode_url: "",
      hackerrank_url: "",
      school_name: "",
      twelfth_percentage: "",
      college_name: "",
      cgpa: "",
    },
  });

  useEffect(() => {
    if (profile) {
      form.reset({
        full_name: profile.full_name,
        email: profile.email,
        phone: profile.phone || "",
        date_of_birth: profile.date_of_birth || "",
        gender: profile.gender || "",
        location: profile.location || "",
        headline: profile.headline || "",
        summary: profile.summary || "",
        linkedin_url: profile.linkedin_url || "",
        github_url: profile.github_url || "",
        portfolio_url: profile.portfolio_url || "",
        leetcode_url: profile.leetcode_url || "",
        hackerrank_url: profile.hackerrank_url || "",
        school_name: profile.school_name || "",
        twelfth_percentage: profile.twelfth_percentage || "",
        college_name: profile.college_name || "",
        cgpa: profile.cgpa || "",
      });
    } else if (user) {
      form.reset({
        full_name: user.full_name || "",
        email: user.email || "",
      });
    }
  }, [profile, user, form]);

  const onSubmit = async (data: ProfileFormValues) => {
    if (!user) return;
    
    // Clean up empty strings to null for URLs
    const payload = {
      ...data,
      linkedin_url: data.linkedin_url || null,
      github_url: data.github_url || null,
      portfolio_url: data.portfolio_url || null,
      leetcode_url: data.leetcode_url || null,
      hackerrank_url: data.hackerrank_url || null,
    };

    try {
      if (profile) {
        await updateProfile.mutateAsync({ userId: user.id, payload });
        toast.success("Profile updated successfully!");
      } else {
        await createProfile.mutateAsync({ ...payload, user_id: user.id });
        toast.success("Profile created successfully!");
      }
    } catch (error: any) {
      toast.error(error.response?.data?.detail || "Failed to save profile");
    }
  };

  const handleAvatarUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files?.[0] || !user || !profile) return;
    const file = e.target.files[0];
    const formData = new FormData();
    formData.append("file", file);
    
    setIsUploading(true);
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch((process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000') + "/uploads/image", {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
        },
        body: formData,
      });
      
      if (!response.ok) throw new Error("Upload failed");
      const responseData = await response.json();
      const imageUrl = responseData.url;
      await updateProfile.mutateAsync({ 
        userId: user.id, 
        payload: { profile_image: imageUrl } 
      });
      toast.success("Profile picture updated");
    } catch (error) {
      toast.error("Failed to upload image");
    } finally {
      setIsUploading(false);
    }
  };

  const handleRefreshGithub = async () => {
    if (!user || !profile?.github_url) return;
    setIsRefreshingGithub(true);
    try {
      await apiClient.post(`/candidate/profile/${user.id}/refresh-github`);
      toast.success("GitHub stats refreshed!");
      refetch();
    } catch (error) {
      toast.error("Failed to refresh GitHub stats");
    } finally {
      setIsRefreshingGithub(false);
    }
  };

  if (isLoading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-[200px] w-full rounded-xl" />
        <Skeleton className="h-[400px] w-full rounded-xl" />
      </div>
    );
  }

  return (
    <div className="space-y-6 max-w-4xl">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold tracking-tight">Basic Details</h2>
          <p className="text-muted-foreground">Manage your public candidate profile and contact information.</p>
        </div>
        {profile && (
          <Button variant="outline" className="shrink-0 gap-2" asChild>
            <Link href={`/public/candidate/${profile.candidate_code || profile.id}`} target="_blank">
              <ExternalLink className="h-4 w-4" />
              View Public Profile
            </Link>
          </Button>
        )}
      </div>

      <div className="grid gap-6 md:grid-cols-[200px_1fr]">
        <Card className="border-none shadow-sm bg-card/50">
          <CardContent className="p-6 flex flex-col items-center gap-4 text-center">
            <div className="relative group">
              <div className="w-32 h-32 rounded-full border-4 border-background shadow-sm overflow-hidden bg-muted flex items-center justify-center">
                {profile?.profile_image ? (
                  <img src={profile.profile_image} alt="Avatar" className="w-full h-full object-cover" />
                ) : (
                  <User className="h-12 w-12 text-muted-foreground" />
                )}
              </div>
              <Label 
                htmlFor="avatar-upload" 
                className="absolute inset-0 bg-black/60 text-white flex flex-col items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity rounded-full cursor-pointer"
              >
                {isUploading ? <Loader2 className="h-6 w-6 animate-spin" /> : <Camera className="h-6 w-6" />}
                <span className="text-xs mt-1">Upload</span>
              </Label>
              <Input 
                id="avatar-upload" 
                type="file" 
                accept="image/*" 
                className="hidden" 
                onChange={handleAvatarUpload}
                disabled={isUploading || !profile}
              />
            </div>
            {!profile && <p className="text-xs text-muted-foreground">Save your profile first to upload an avatar.</p>}
          </CardContent>
        </Card>

        <Card className="border-none shadow-sm bg-card/50">
          <CardContent className="p-6">
            <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
              <div className="grid gap-4 sm:grid-cols-2">
                <div className="space-y-2">
                  <Label htmlFor="full_name">Full Name</Label>
                  <Input id="full_name" {...form.register("full_name")} />
                  {form.formState.errors.full_name && (
                    <p className="text-xs text-destructive">{form.formState.errors.full_name.message}</p>
                  )}
                </div>
                <div className="space-y-2">
                  <Label htmlFor="email">Email</Label>
                  <Input id="email" {...form.register("email")} disabled />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="phone">Phone Number</Label>
                  <Input id="phone" {...form.register("phone")} />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="date_of_birth">Date of Birth</Label>
                  <Input id="date_of_birth" type="date" {...form.register("date_of_birth")} />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="gender">Gender</Label>
                  <Select 
                    value={form.watch("gender") || ""} 
                    onValueChange={(val) => form.setValue("gender", val)}
                  >
                    <SelectTrigger id="gender">
                      <SelectValue placeholder="Select gender" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="Male">Male</SelectItem>
                      <SelectItem value="Female">Female</SelectItem>
                      <SelectItem value="Non-binary">Non-binary</SelectItem>
                      <SelectItem value="Prefer not to say">Prefer not to say</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="location">Location</Label>
                  <Input id="location" placeholder="City, Country" {...form.register("location")} />
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="headline">Professional Headline</Label>
                <Input id="headline" placeholder="e.g. Senior Frontend Engineer | React Specialist" {...form.register("headline")} />
              </div>

              <div className="space-y-2">
                <Label htmlFor="summary">About Me / Summary</Label>
                <Textarea 
                  id="summary" 
                  rows={4} 
                  placeholder="Write a brief overview of your background, achievements, and career goals."
                  {...form.register("summary")} 
                />
              </div>

              <div className="pt-4 border-t border-border">
                <h3 className="text-lg font-medium mb-4">Educational Details</h3>
                <div className="grid gap-4 sm:grid-cols-2">
                  <div className="space-y-2">
                    <Label htmlFor="school_name">School Name (12th)</Label>
                    <Input id="school_name" placeholder="E.g. XYZ High School" {...form.register("school_name")} />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="twelfth_percentage">12th Percentage (%)</Label>
                    <Input id="twelfth_percentage" type="number" step="0.01" placeholder="E.g. 95.5" {...form.register("twelfth_percentage")} />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="college_name">College / University</Label>
                    <Input id="college_name" placeholder="E.g. University of Technology" {...form.register("college_name")} />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="cgpa">College CGPA (out of 10)</Label>
                    <Input id="cgpa" type="number" step="0.01" placeholder="E.g. 8.5" {...form.register("cgpa")} />
                  </div>
                </div>
              </div>

              <div className="pt-4 border-t border-border">
                <h3 className="text-lg font-medium mb-4">Social & Links</h3>
                <div className="grid gap-4 sm:grid-cols-2">
                  <div className="space-y-2">
                    <Label htmlFor="linkedin_url">LinkedIn URL</Label>
                    <Input id="linkedin_url" placeholder="https://linkedin.com/in/..." {...form.register("linkedin_url")} />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="github_url">GitHub URL</Label>
                    <div className="flex gap-2">
                      <Input id="github_url" placeholder="https://github.com/..." {...form.register("github_url")} />
                      {profile?.github_url && (
                        <Button 
                          type="button" 
                          variant="outline" 
                          size="icon" 
                          onClick={handleRefreshGithub}
                          disabled={isRefreshingGithub}
                          title="Refresh GitHub Stats"
                        >
                          <RefreshCw className={`h-4 w-4 ${isRefreshingGithub ? 'animate-spin' : ''}`} />
                        </Button>
                      )}
                    </div>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="portfolio_url">Portfolio URL</Label>
                    <Input id="portfolio_url" placeholder="https://yourwebsite.com" {...form.register("portfolio_url")} />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="leetcode_url">LeetCode URL</Label>
                    <Input id="leetcode_url" placeholder="https://leetcode.com/..." {...form.register("leetcode_url")} />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="hackerrank_url">HackerRank URL</Label>
                    <Input id="hackerrank_url" placeholder="https://hackerrank.com/..." {...form.register("hackerrank_url")} />
                  </div>
                </div>
              </div>

              <div className="flex justify-end gap-4 pt-4 border-t border-border">
                <Button 
                  type="submit" 
                  disabled={form.formState.isSubmitting}
                >
                  {form.formState.isSubmitting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                  {profile ? "Save Changes" : "Create Profile"}
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
