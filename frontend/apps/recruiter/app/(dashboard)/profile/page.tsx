"use client";

import { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle, CardFooter } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { useUser } from "@/lib/hooks/useAuth";
import { useCompanyProfile, useUpdateCompanyProfile } from "@/lib/hooks/useCompanyProfile";
import { Building2, Mail, Phone, Globe, MapPin, Edit2, Check, X, CalendarDays, Users, AlertCircle, Camera } from "lucide-react";

export default function ProfilePage() {
  const { data: user } = useUser();
  const { data: company, isLoading } = useCompanyProfile(user?.id);
  const updateCompany = useUpdateCompanyProfile();
  const [editing, setEditing] = useState(false);
  const [form, setForm] = useState<Record<string, string>>({});
  const [updateError, setUpdateError] = useState("");
  const [updateSuccess, setUpdateSuccess] = useState(false);

  const fullName = user?.full_name || user?.username || "Recruiter";
  const initials = fullName.split(" ").map((n: string) => n[0]).join("").toUpperCase().slice(0, 2);

  const startEdit = () => {
    setForm({
      company_name: company?.company_name || "",
      industry: company?.industry || "",
      website: company?.website || "",
      description: company?.description || "",
      location: company?.location || "",
      contact_email: company?.contact_email || "",
      contact_phone: company?.contact_phone || "",
    });
    setEditing(true);
    setUpdateError("");
    setUpdateSuccess(false);
  };

  const handleSave = async () => {
    if (!company?.id) return;
    try {
      await updateCompany.mutateAsync({ companyId: company.id, data: form });
      setEditing(false);
      setUpdateSuccess(true);
      setTimeout(() => setUpdateSuccess(false), 3000);
    } catch (err: any) {
      setUpdateError(err?.response?.data?.detail || "Failed to update profile.");
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full min-h-[400px]">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>
    );
  }

  return (
    <div className="space-y-8 max-w-5xl mx-auto pb-10">
      {/* Page Header */}
      <div>
        <h2 className="text-3xl font-bold tracking-tight text-foreground">Company Profile</h2>
        <p className="text-muted-foreground mt-2 text-lg">Manage your organization's public profile and branding.</p>
      </div>

      {/* Banner & Basic Info Section */}
      <div className="relative">
        <div className="h-48 w-full bg-gradient-to-r from-primary/80 to-primary/40 rounded-xl overflow-hidden shadow-sm">
          {/* A cool pattern overlay could go here */}
          <div className="absolute inset-0 bg-[url('/grid.svg')] opacity-20 bg-center"></div>
        </div>
        
        <Card className="mx-6 -mt-16 relative z-10 shadow-lg border-muted">
          <CardContent className="p-6">
            <div className="flex flex-col sm:flex-row gap-6 items-start sm:items-center justify-between">
              <div className="flex flex-col sm:flex-row items-center gap-6 w-full">
                <div className="relative group">
                  <Avatar className="h-28 w-28 border-4 border-background shadow-md">
                    <AvatarFallback className="text-4xl bg-primary/10 text-primary font-bold">
                      {company?.company_name ? company.company_name.substring(0,2).toUpperCase() : <Building2 className="h-12 w-12" />}
                    </AvatarFallback>
                  </Avatar>
                  <button className="absolute bottom-0 right-0 p-2 bg-primary text-primary-foreground rounded-full shadow-sm opacity-0 group-hover:opacity-100 transition-opacity">
                    <Camera className="h-4 w-4" />
                  </button>
                </div>
                
                <div className="text-center sm:text-left flex-1">
                  <h3 className="text-2xl font-bold">{company?.company_name || "Company Name"}</h3>
                  <div className="flex flex-wrap items-center justify-center sm:justify-start gap-2 mt-2">
                    {company?.industry && <Badge variant="secondary" className="px-2 py-0.5">{company.industry}</Badge>}
                    {company?.location && (
                      <span className="text-muted-foreground text-sm flex items-center">
                        <MapPin className="h-4 w-4 mr-1" /> {company.location}
                      </span>
                    )}
                  </div>
                </div>
              </div>
              
              {!editing && (
                <Button onClick={startEdit} className="shrink-0">
                  <Edit2 className="h-4 w-4 mr-2" /> Edit Profile
                </Button>
              )}
            </div>
          </CardContent>
        </Card>
      </div>

      {!company && !editing ? (
        <Card className="border-dashed border-2 bg-muted/20">
          <CardContent className="flex flex-col items-center justify-center py-16 text-center">
            <div className="h-16 w-16 bg-primary/10 rounded-full flex items-center justify-center mb-4">
              <Building2 className="h-8 w-8 text-primary" />
            </div>
            <h3 className="text-xl font-semibold mb-2">No Profile Configured</h3>
            <p className="text-muted-foreground max-w-md mb-6">You haven't set up your company profile yet. A complete profile helps attract top candidates.</p>
            <Button size="lg" onClick={startEdit}>Set Up Profile Now</Button>
          </CardContent>
        </Card>
      ) : editing ? (
        <Card className="shadow-sm">
          <CardHeader>
            <CardTitle>Edit Company Details</CardTitle>
            <CardDescription>Update your public-facing company information.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="space-y-2">
                <Label htmlFor="company_name">Company Name</Label>
                <Input id="company_name" value={form.company_name || ""} onChange={e => setForm(f => ({ ...f, company_name: e.target.value }))} />
              </div>
              <div className="space-y-2">
                <Label htmlFor="industry">Industry</Label>
                <Input id="industry" value={form.industry || ""} onChange={e => setForm(f => ({ ...f, industry: e.target.value }))} placeholder="e.g. Software, Finance" />
              </div>
              <div className="space-y-2">
                <Label htmlFor="location">Headquarters Location</Label>
                <Input id="location" value={form.location || ""} onChange={e => setForm(f => ({ ...f, location: e.target.value }))} placeholder="City, Country" />
              </div>
              <div className="space-y-2">
                <Label htmlFor="website">Website URL</Label>
                <Input id="website" type="url" value={form.website || ""} onChange={e => setForm(f => ({ ...f, website: e.target.value }))} placeholder="https://example.com" />
              </div>
              <div className="space-y-2">
                <Label htmlFor="contact_email">Public Contact Email</Label>
                <Input id="contact_email" type="email" value={form.contact_email || ""} onChange={e => setForm(f => ({ ...f, contact_email: e.target.value }))} />
              </div>
              <div className="space-y-2">
                <Label htmlFor="contact_phone">Contact Phone</Label>
                <Input id="contact_phone" type="tel" value={form.contact_phone || ""} onChange={e => setForm(f => ({ ...f, contact_phone: e.target.value }))} />
              </div>
            </div>
            
            <Separator />
            
            <div className="space-y-2">
              <Label htmlFor="description">About the Company</Label>
              <Textarea 
                id="description" 
                value={form.description || ""} 
                onChange={e => setForm(f => ({ ...f, description: e.target.value }))} 
                rows={5} 
                placeholder="Write a compelling description of your company, mission, and culture..." 
                className="resize-none"
              />
              <p className="text-xs text-muted-foreground text-right">{form.description?.length || 0} characters</p>
            </div>

            {updateError && (
              <div className="flex items-center gap-2 p-3 bg-destructive/10 text-destructive rounded-md text-sm">
                <AlertCircle className="h-4 w-4 shrink-0" />
                <p>{updateError}</p>
              </div>
            )}
          </CardContent>
          <CardFooter className="bg-muted/30 flex justify-end gap-3 rounded-b-xl border-t">
            <Button variant="ghost" onClick={() => setEditing(false)} disabled={updateCompany.isPending}>
              Cancel
            </Button>
            <Button onClick={handleSave} disabled={updateCompany.isPending} className="min-w-[120px]">
              {updateCompany.isPending ? (
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-primary-foreground mr-2" />
              ) : (
                <Check className="h-4 w-4 mr-2" />
              )}
              Save Changes
            </Button>
          </CardFooter>
        </Card>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Main Content Area */}
          <div className="lg:col-span-2 space-y-6">
            <Card className="shadow-sm">
              <CardHeader>
                <CardTitle className="text-xl">About Us</CardTitle>
              </CardHeader>
              <CardContent>
                {company?.description ? (
                  <div className="prose prose-sm dark:prose-invert max-w-none text-muted-foreground whitespace-pre-wrap leading-relaxed">
                    {company.description}
                  </div>
                ) : (
                  <p className="text-muted-foreground italic py-4">No description provided. Add a description to help candidates understand your company better.</p>
                )}
              </CardContent>
            </Card>
            
            {/* Associated Recruiter Account Card */}
            <Card className="shadow-sm bg-primary/5 border-primary/20">
              <CardHeader className="pb-3">
                <CardTitle className="text-lg flex items-center gap-2">
                  <Users className="h-5 w-5 text-primary" /> Recruiter Account
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex items-center gap-4 bg-background/50 p-4 rounded-lg border border-border/50">
                  <Avatar>
                    <AvatarFallback className="bg-primary/20 text-primary">{initials}</AvatarFallback>
                  </Avatar>
                  <div>
                    <p className="font-medium">{fullName}</p>
                    <p className="text-sm text-muted-foreground flex items-center gap-1 mt-0.5">
                      <Mail className="h-3 w-3" /> {user?.email}
                    </p>
                  </div>
                  <Badge variant="outline" className="ml-auto capitalize bg-background">{user?.role?.toLowerCase() || "recruiter"}</Badge>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Sidebar / Quick Info */}
          <div className="space-y-6">
            <Card className="shadow-sm">
              <CardHeader>
                <CardTitle className="text-lg">Contact Information</CardTitle>
              </CardHeader>
              <CardContent className="space-y-5">
                <div className="flex items-start gap-3">
                  <div className="p-2 bg-muted rounded-md text-muted-foreground shrink-0">
                    <Globe className="h-4 w-4" />
                  </div>
                  <div>
                    <p className="text-sm font-medium">Website</p>
                    {company?.website ? (
                      <a href={company.website} target="_blank" rel="noopener noreferrer" className="text-sm text-primary hover:underline mt-0.5 inline-block">
                        {company.website.replace(/^https?:\/\//, '')}
                      </a>
                    ) : (
                      <p className="text-sm text-muted-foreground mt-0.5">—</p>
                    )}
                  </div>
                </div>

                <div className="flex items-start gap-3">
                  <div className="p-2 bg-muted rounded-md text-muted-foreground shrink-0">
                    <Mail className="h-4 w-4" />
                  </div>
                  <div>
                    <p className="text-sm font-medium">Contact Email</p>
                    <p className="text-sm text-muted-foreground mt-0.5">{company?.contact_email || "—"}</p>
                  </div>
                </div>

                <div className="flex items-start gap-3">
                  <div className="p-2 bg-muted rounded-md text-muted-foreground shrink-0">
                    <Phone className="h-4 w-4" />
                  </div>
                  <div>
                    <p className="text-sm font-medium">Phone</p>
                    <p className="text-sm text-muted-foreground mt-0.5">{company?.contact_phone || "—"}</p>
                  </div>
                </div>
                
                <div className="flex items-start gap-3">
                  <div className="p-2 bg-muted rounded-md text-muted-foreground shrink-0">
                    <MapPin className="h-4 w-4" />
                  </div>
                  <div>
                    <p className="text-sm font-medium">Headquarters</p>
                    <p className="text-sm text-muted-foreground mt-0.5">{company?.location || "—"}</p>
                  </div>
                </div>
              </CardContent>
            </Card>
            
            {updateSuccess && (
              <div className="p-4 bg-success/15 border border-success/30 rounded-lg flex items-start gap-3 animate-in fade-in slide-in-from-bottom-2">
                <div className="p-1 bg-success rounded-full text-success-foreground shrink-0 mt-0.5">
                  <Check className="h-3 w-3" />
                </div>
                <div>
                  <p className="font-medium text-success-foreground text-sm">Success</p>
                  <p className="text-xs text-success-foreground/80 mt-0.5">Your profile has been updated successfully.</p>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
