"use client";

import { useState, useEffect } from "react";
import { useUser } from "@/lib/hooks/useAuth";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Loader2, UploadCloud, FileText, CheckCircle2, AlertCircle, Plus, Trash2, ShieldCheck } from "lucide-react";
import { toast } from "sonner";
import { apiClient } from "@/lib/apiClient";
import { 
  useGetProfile, useUpdateProfile, 
  useCreateEducation, useCreateExperience, 
  useCreateSkill, useCreateProject 
} from "@/lib/hooks/useProfile";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";

export default function ProfileResumePage() {
  const { data: user } = useUser();
  const { data: profile } = useGetProfile(user?.id);
  
  const [file, setFile] = useState<File | null>(null);
  const [isParsing, setIsParsing] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  
  const [parsedData, setParsedData] = useState<any>(null);
  const [isReviewModalOpen, setIsReviewModalOpen] = useState(false);

  // Editable State
  const [personalMerge, setPersonalMerge] = useState<any>({});
  const [editableArrays, setEditableArrays] = useState({
    education: [] as any[],
    experience: [] as any[],
    skills: [] as any[],
    projects: [] as any[],
  });

  const updateProfile = useUpdateProfile();
  const createEducation = useCreateEducation();
  const createExperience = useCreateExperience();
  const createSkill = useCreateSkill();
  const createProject = useCreateProject();

  useEffect(() => {
    if (parsedData && profile) {
      const initialMerge: any = {};
      const fields = ["full_name", "email", "phone", "location", "linkedin_url", "github_url", "portfolio_url"];
      
      fields.forEach(f => {
        const existingVal = (profile as any)[f];
        const resumeVal = parsedData.personal?.[f];
        
        if (!existingVal && resumeVal) {
          initialMerge[f] = resumeVal; // Auto fill
        } else if (existingVal && resumeVal && existingVal !== resumeVal) {
          initialMerge[f] = existingVal; // Default to existing if collision
        } else {
          initialMerge[f] = existingVal || ""; // Keep existing or empty
        }
      });

      setPersonalMerge(initialMerge);
      setEditableArrays({
        education: (parsedData.education || []).map((edu: any) => ({
          institution: edu.institution || edu.college || edu.university || "",
          degree: edu.degree || "",
          field_of_study: edu.field_of_study || edu.branch || "",
          start_year: edu.start_year || "",
          end_year: edu.end_year || edu.graduation_year || "",
        })),
        experience: (parsedData.experience || []).map((exp: any) => ({
          company: exp.company || exp.company_name || "",
          job_title: exp.job_title || exp.role || exp.title || "",
          start_date: exp.start_date || "",
          end_date: exp.end_date || "",
          description: exp.description || (Array.isArray(exp.responsibilities) ? exp.responsibilities.join("\n") : (exp.responsibilities || "")),
        })),
        skills: parsedData.skills?.map((s: any) => typeof s === 'string' ? { name: s } : s) || [],
        projects: (parsedData.projects || []).map((proj: any) => ({
          project_name: proj.name || proj.project_name || proj.project_title || "",
          technologies: proj.technologies || (Array.isArray(proj.technologies_used) ? proj.technologies_used.join(', ') : proj.technologies_used) || "",
          description: proj.description || "",
          github_url: proj.github_url || proj.github_link || "",
          live_url: proj.live_url || proj.live_demo_link || "",
        }))
      });
    }
  }, [parsedData, profile]);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      setFile(e.target.files[0]);
    }
  };

  const handleParse = async () => {
    if (!file) {
      toast.error("Please select a file first.");
      return;
    }
    if (!user) {
      toast.error("User session not fully loaded. Please wait or refresh the page.");
      return;
    }
    
    setIsParsing(true);
    const formData = new FormData();
    formData.append("file", file);

    try {
      const token = localStorage.getItem('access_token');
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      
      const response = await fetch(`${apiUrl}/resume-parser/parse`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
        },
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `Request failed with status ${response.status}`);
      }

      const data = await response.json();
      const result = data.parsed_json;
      if (result) {
        setParsedData(result);
        setIsReviewModalOpen(true);
      } else {
        toast.error("Failed to extract data from resume.");
      }
    } catch (error: any) {
      console.error(error);
      toast.error(error.message || "Error parsing resume");
    } finally {
      setIsParsing(false);
    }
  };

  const formatDate = (dateStr: any): string => {
    if (!dateStr) return new Date().toISOString().split('T')[0];
    const parsed = new Date(dateStr);
    if (isNaN(parsed.getTime())) {
      const match = String(dateStr).match(/\b(19|20)\d{2}\b/);
      if (match) return `${match[0]}-01-01`;
      return new Date().toISOString().split('T')[0];
    }
    return parsed.toISOString().split('T')[0];
  };

  const parseSafeYear = (val: any, fallback: number): number => {
    if (!val) return fallback;
    const numStr = String(val).match(/\b(19|20)\d{2}\b/);
    if (numStr) return parseInt(numStr[0], 10);
    const parsed = parseInt(String(val), 10);
    if (isNaN(parsed) || parsed < 1900 || parsed > 2100) return fallback;
    return parsed;
  };

  const handleApproveAndSave = async () => {
    if (!parsedData || !user || !profile) return;
    setIsSaving(true);
    
    try {
      // 1. Save Merged Basic Details
      const updatePayload: any = {};
      Object.keys(personalMerge).forEach(k => {
        if (personalMerge[k]) updatePayload[k] = personalMerge[k];
      });
      if (Object.keys(updatePayload).length > 0) {
        try {
          await updateProfile.mutateAsync({ userId: user.id, payload: updatePayload });
        } catch (e: any) {
          console.error("Profile update failed", e.response?.data || e.message);
          toast.error("Some basic details could not be saved due to validation rules.");
        }
      }

      // 2. Save Education
      for (const edu of editableArrays.education) {
        try {
          const sy = parseSafeYear(edu.start_year, new Date().getFullYear());
          let ey = edu.end_year ? parseSafeYear(edu.end_year, sy) : null;
          if (ey !== null && ey < sy) ey = sy;
          
          await createEducation.mutateAsync({
            user_id: user.id,
            institution: edu.institution || "Unknown Institution",
            degree: edu.degree || "Unknown Degree",
            department: edu.field_of_study || null,
            start_year: sy,
            end_year: ey,
          });
        } catch (e: any) { console.error("Education save failed", JSON.stringify(e.response?.data || e.message)); }
      }

      // 3. Save Experience
      for (const exp of editableArrays.experience) {
        try {
          await createExperience.mutateAsync({
            user_id: user.id,
            company_name: exp.company || "Unknown Company",
            job_title: exp.job_title || "Unknown Title",
            employment_type: "Full-time",
            start_date: formatDate(exp.start_date),
            end_date: exp.end_date ? formatDate(exp.end_date) : null,
            currently_working: !exp.end_date,
            description: exp.description || null,
          });
        } catch (e: any) { console.error("Experience save failed", e.response?.data || e); }
      }

      // 4. Save Skills
      for (const skill of editableArrays.skills) {
        try {
          await createSkill.mutateAsync({
            user_id: user.id,
            skill_name: skill.name || "Unknown Skill",
            proficiency_level: "intermediate",
            years_of_experience: 1,
          });
        } catch (e: any) { console.error("Skill save failed", e.response?.data || e); }
      }

      // 5. Save Projects
      for (const proj of editableArrays.projects) {
        try {
          const techArray = Array.isArray(proj.technologies) 
              ? proj.technologies 
              : (typeof proj.technologies === 'string' ? proj.technologies.split(',').map((t:string)=>t.trim()) : []);
          await createProject.mutateAsync({
            user_id: user.id,
            project_name: proj.name || proj.project_name || "Unknown Project",
            technologies: techArray,
            description: proj.description || null,
            github_url: proj.github_url || null,
            live_url: proj.live_url || null,
            start_date: formatDate(proj.start_date || proj.date || new Date().toISOString()),
          });
        } catch (e: any) { console.error("Project save failed", e.response?.data || e); }
      }

      toast.success("Resume data successfully merged and saved to your profile!");
      setIsReviewModalOpen(false);
      setParsedData(null);
      setFile(null);
    } catch (error) {
      toast.error("An error occurred while saving extracted data.");
    } finally {
      setIsSaving(false);
    }
  };

  const renderMergeField = (field: string, label: string) => {
    const existingVal = profile ? (profile as any)[field] : null;
    const resumeVal = parsedData?.personal?.[field];

    if (!existingVal && !resumeVal) return null;

    if (!existingVal && resumeVal) {
      return (
        <div className="mb-4 p-3 bg-green-50/50 border border-green-100 rounded-md">
          <Label className="text-xs text-muted-foreground uppercase">{label}</Label>
          <div className="text-sm font-medium flex items-center gap-2 mt-1">
            <CheckCircle2 className="h-4 w-4 text-green-500" />
            Auto-filled: {resumeVal}
          </div>
        </div>
      );
    }

    if (existingVal && resumeVal && existingVal !== resumeVal) {
      return (
        <div className="mb-4 p-4 border rounded-md bg-muted/20">
          <Label className="text-xs text-muted-foreground uppercase mb-3 block">{label} Conflict</Label>
          <RadioGroup 
            value={personalMerge[field]} 
            onValueChange={(val) => setPersonalMerge({...personalMerge, [field]: val})}
            className="space-y-3"
          >
            <div className="flex items-center space-x-3 bg-background p-2 rounded border">
              <RadioGroupItem value={existingVal} id={`ext-${field}`} />
              <Label htmlFor={`ext-${field}`} className="cursor-pointer flex-1">
                <span className="text-xs text-muted-foreground block">Keep Existing</span>
                <span className="font-medium">{existingVal}</span>
              </Label>
            </div>
            <div className="flex items-center space-x-3 bg-primary/5 p-2 rounded border border-primary/20">
              <RadioGroupItem value={resumeVal} id={`res-${field}`} />
              <Label htmlFor={`res-${field}`} className="cursor-pointer flex-1">
                <span className="text-xs text-primary block">Use Resume Value</span>
                <span className="font-medium">{resumeVal}</span>
              </Label>
            </div>
          </RadioGroup>
        </div>
      );
    }

    return (
      <div className="mb-4 p-3 border rounded-md opacity-70">
        <Label className="text-xs text-muted-foreground uppercase">{label}</Label>
        <div className="text-sm font-medium mt-1">{existingVal}</div>
      </div>
    );
  };

  const handleArrayChange = (type: keyof typeof editableArrays, index: number, field: string, value: string) => {
    const newArray = [...editableArrays[type]];
    newArray[index] = { ...newArray[index], [field]: value };
    setEditableArrays({ ...editableArrays, [type]: newArray });
  };

  const handleArrayDelete = (type: keyof typeof editableArrays, index: number) => {
    const newArray = [...editableArrays[type]];
    newArray.splice(index, 1);
    setEditableArrays({ ...editableArrays, [type]: newArray });
  };

  const handleArrayAdd = (type: keyof typeof editableArrays, emptyItem: any) => {
    setEditableArrays({ ...editableArrays, [type]: [...editableArrays[type], emptyItem] });
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold tracking-tight">Resume Parser</h2>
        <p className="text-muted-foreground">Upload your resume to automatically fill out your profile.</p>
      </div>

      <Card className="border-dashed shadow-sm">
        <CardContent className="p-12 flex flex-col items-center justify-center text-center">
          <div className="bg-primary/10 p-4 rounded-full mb-4">
            <UploadCloud className="h-8 w-8 text-primary" />
          </div>
          <h3 className="text-lg font-semibold mb-2">Upload Resume</h3>
          <p className="text-muted-foreground mb-6 max-w-md">
            Drag and drop your PDF or DOCX file here. We will intelligently extract your details.
          </p>
          
          <input 
            type="file" 
            id="resume-upload" 
            className="hidden" 
            accept=".pdf,.doc,.docx"
            onChange={handleFileChange}
          />
          
          {file ? (
            <div className="flex flex-col items-center gap-4">
              <div className="flex items-center gap-2 text-sm font-medium bg-muted px-4 py-2 rounded-md">
                <FileText className="h-4 w-4" />
                {file.name}
              </div>
              <Button onClick={handleParse} disabled={isParsing} className="min-w-[150px]">
                {isParsing ? (
                  <><Loader2 className="mr-2 h-4 w-4 animate-spin" /> Parsing...</>
                ) : (
                  "Parse Resume"
                )}
              </Button>
            </div>
          ) : (
            <Button variant="outline" onClick={() => document.getElementById("resume-upload")?.click()}>
              Select File
            </Button>
          )}
        </CardContent>
      </Card>

      <Dialog open={isReviewModalOpen} onOpenChange={setIsReviewModalOpen}>
        <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <div className="flex justify-between items-center pr-8">
              <DialogTitle className="text-xl">Review & Merge Data</DialogTitle>
              {parsedData?.confidence_score !== undefined && (
                <div className="flex items-center gap-2 bg-green-500/10 text-green-600 px-3 py-1 rounded-full text-sm font-semibold border border-green-500/20">
                  <ShieldCheck className="h-4 w-4" />
                  AI Confidence: {parsedData.confidence_score}%
                </div>
              )}
            </div>
            <p className="text-sm text-muted-foreground">Select which existing fields to keep, and edit any extracted array data before saving.</p>
          </DialogHeader>
          
          {parsedData && (
            <div className="space-y-8 mt-4">
              
              {/* Personal Details Merge */}
              <section>
                <h4 className="font-bold flex items-center gap-2 mb-4 pb-2 border-b text-lg">
                  Basic Details
                </h4>
                <div className="grid md:grid-cols-2 gap-x-6">
                  {renderMergeField("full_name", "Full Name")}
                  {renderMergeField("email", "Email")}
                  {renderMergeField("phone", "Phone")}
                  {renderMergeField("location", "Location")}
                  {renderMergeField("linkedin_url", "LinkedIn")}
                  {renderMergeField("github_url", "GitHub")}
                  {renderMergeField("portfolio_url", "Portfolio")}
                </div>
              </section>

              {/* Education */}
              <section>
                <div className="flex justify-between items-center mb-4 pb-2 border-b">
                  <h4 className="font-bold flex items-center gap-2 text-lg">
                    Education ({editableArrays.education.length})
                  </h4>
                  <Button size="sm" variant="outline" onClick={() => handleArrayAdd('education', { degree: "", institution: "", start_year: "", end_year: "" })}>
                    <Plus className="h-4 w-4 mr-1" /> Add
                  </Button>
                </div>
                <div className="space-y-4">
                  {editableArrays.education.map((edu, i) => (
                    <div key={i} className="flex gap-4 items-start p-4 bg-muted/30 rounded-lg border">
                      <div className="flex-1 grid grid-cols-2 gap-3">
                        <div>
                          <Label className="text-xs">Degree</Label>
                          <Input value={edu.degree || ""} onChange={(e) => handleArrayChange('education', i, 'degree', e.target.value)} />
                        </div>
                        <div>
                          <Label className="text-xs">Institution</Label>
                          <Input value={edu.institution || ""} onChange={(e) => handleArrayChange('education', i, 'institution', e.target.value)} />
                        </div>
                        <div>
                          <Label className="text-xs">Start Year</Label>
                          <Input value={edu.start_year || ""} onChange={(e) => handleArrayChange('education', i, 'start_year', e.target.value)} />
                        </div>
                        <div>
                          <Label className="text-xs">End Year</Label>
                          <Input value={edu.end_year || ""} onChange={(e) => handleArrayChange('education', i, 'end_year', e.target.value)} />
                        </div>
                      </div>
                      <Button variant="ghost" size="icon" className="text-destructive hover:bg-destructive/10" onClick={() => handleArrayDelete('education', i)}>
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  ))}
                  {editableArrays.education.length === 0 && (
                    <p className="text-sm text-muted-foreground flex items-center gap-2"><AlertCircle className="h-4 w-4"/> No education extracted.</p>
                  )}
                </div>
              </section>

              {/* Experience */}
              <section>
                <div className="flex justify-between items-center mb-4 pb-2 border-b">
                  <h4 className="font-bold flex items-center gap-2 text-lg">
                    Experience ({editableArrays.experience.length})
                  </h4>
                  <Button size="sm" variant="outline" onClick={() => handleArrayAdd('experience', { job_title: "", company: "", start_date: "", end_date: "", description: "" })}>
                    <Plus className="h-4 w-4 mr-1" /> Add
                  </Button>
                </div>
                <div className="space-y-4">
                  {editableArrays.experience.map((exp, i) => (
                    <div key={i} className="flex gap-4 items-start p-4 bg-muted/30 rounded-lg border">
                      <div className="flex-1 space-y-3">
                        <div className="grid grid-cols-2 gap-3">
                          <div>
                            <Label className="text-xs">Job Title</Label>
                            <Input value={exp.job_title || ""} onChange={(e) => handleArrayChange('experience', i, 'job_title', e.target.value)} />
                          </div>
                          <div>
                            <Label className="text-xs">Company</Label>
                            <Input value={exp.company || ""} onChange={(e) => handleArrayChange('experience', i, 'company', e.target.value)} />
                          </div>
                          <div>
                            <Label className="text-xs">Start Date</Label>
                            <Input value={exp.start_date || ""} onChange={(e) => handleArrayChange('experience', i, 'start_date', e.target.value)} />
                          </div>
                          <div>
                            <Label className="text-xs">End Date</Label>
                            <Input value={exp.end_date || ""} onChange={(e) => handleArrayChange('experience', i, 'end_date', e.target.value)} />
                          </div>
                        </div>
                        <div>
                          <Label className="text-xs">Description</Label>
                          <Textarea value={exp.description || ""} onChange={(e) => handleArrayChange('experience', i, 'description', e.target.value)} rows={2} />
                        </div>
                      </div>
                      <Button variant="ghost" size="icon" className="text-destructive hover:bg-destructive/10" onClick={() => handleArrayDelete('experience', i)}>
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  ))}
                  {editableArrays.experience.length === 0 && (
                    <p className="text-sm text-muted-foreground flex items-center gap-2"><AlertCircle className="h-4 w-4"/> No experience extracted.</p>
                  )}
                </div>
              </section>

              {/* Skills */}
              <section>
                <div className="flex justify-between items-center mb-4 pb-2 border-b">
                  <h4 className="font-bold flex items-center gap-2 text-lg">
                    Skills ({editableArrays.skills.length})
                  </h4>
                  <Button size="sm" variant="outline" onClick={() => handleArrayAdd('skills', { name: "" })}>
                    <Plus className="h-4 w-4 mr-1" /> Add
                  </Button>
                </div>
                <div className="flex flex-wrap gap-2">
                  {editableArrays.skills.map((skill, i) => (
                    <div key={i} className="flex items-center gap-1 bg-secondary/30 border border-secondary p-1 pl-2 rounded-md">
                      <input 
                        className="bg-transparent border-none text-sm w-24 focus:outline-none" 
                        value={skill.name || ""} 
                        onChange={(e) => handleArrayChange('skills', i, 'name', e.target.value)}
                        placeholder="Skill name"
                      />
                      <button className="text-muted-foreground hover:text-destructive p-1 rounded-full hover:bg-background" onClick={() => handleArrayDelete('skills', i)}>
                        <Trash2 className="h-3 w-3" />
                      </button>
                    </div>
                  ))}
                  {editableArrays.skills.length === 0 && (
                    <p className="text-sm text-muted-foreground flex items-center gap-2"><AlertCircle className="h-4 w-4"/> No skills extracted.</p>
                  )}
                </div>
              </section>

              {/* Projects */}
              <section>
                <div className="flex justify-between items-center mb-4 pb-2 border-b">
                  <h4 className="font-bold flex items-center gap-2 text-lg">
                    Projects ({editableArrays.projects.length})
                  </h4>
                  <Button size="sm" variant="outline" onClick={() => handleArrayAdd('projects', { project_name: "", technologies: "", description: "" })}>
                    <Plus className="h-4 w-4 mr-1" /> Add
                  </Button>
                </div>
                <div className="space-y-4">
                  {editableArrays.projects.map((proj, i) => (
                    <div key={i} className="flex gap-4 items-start p-4 bg-muted/30 rounded-lg border">
                      <div className="flex-1 space-y-3">
                        <div className="grid grid-cols-2 gap-3">
                          <div>
                            <Label className="text-xs">Project Name</Label>
                            <Input value={proj.name || proj.project_name || ""} onChange={(e) => handleArrayChange('projects', i, 'project_name', e.target.value)} />
                          </div>
                          <div>
                            <Label className="text-xs">Technologies (comma separated)</Label>
                            <Input value={Array.isArray(proj.technologies) ? proj.technologies.join(', ') : (proj.technologies || "")} onChange={(e) => handleArrayChange('projects', i, 'technologies', e.target.value)} />
                          </div>
                          <div className="col-span-2">
                            <Label className="text-xs">Description</Label>
                            <Textarea value={proj.description || ""} onChange={(e) => handleArrayChange('projects', i, 'description', e.target.value)} rows={2} />
                          </div>
                        </div>
                      </div>
                      <Button variant="ghost" size="icon" className="text-destructive hover:bg-destructive/10" onClick={() => handleArrayDelete('projects', i)}>
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  ))}
                  {editableArrays.projects.length === 0 && (
                    <p className="text-sm text-muted-foreground flex items-center gap-2"><AlertCircle className="h-4 w-4"/> No projects extracted.</p>
                  )}
                </div>
              </section>

              <div className="flex justify-end gap-3 pt-6 border-t sticky bottom-0 bg-background/95 backdrop-blur py-4">
                <Button variant="outline" onClick={() => setIsReviewModalOpen(false)}>Cancel</Button>
                <Button onClick={handleApproveAndSave} disabled={isSaving} size="lg">
                  {isSaving ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : null}
                  Approve & Save to Profile
                </Button>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
