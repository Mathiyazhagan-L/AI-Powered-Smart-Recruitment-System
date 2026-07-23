"use client";

import React, { useState, useEffect } from "react";
import { apiClient } from "@/lib/apiClient";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { FileText, Download, AlertCircle, FileCheck2 } from "lucide-react";
import { Button } from "@/components/ui/button";

export default function ResumeViewer({ candidateId }: { candidateId: string | number }) {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchResumeData = async () => {
      try {
        const res = await apiClient.get(`/recruiter-workspace/resume/${candidateId}`);
        setData(res.data);
      } catch (e) {
        console.error("Failed to fetch resume data", e);
      } finally {
        setLoading(false);
      }
    };
    fetchResumeData();
  }, [candidateId]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64 border rounded-xl bg-card">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>
    );
  }

  if (!data) {
    return (
      <Card className="h-full border-dashed bg-muted/10">
        <CardContent className="flex flex-col items-center justify-center h-64 text-center">
          <AlertCircle className="w-12 h-12 text-muted-foreground mb-4 opacity-50" />
          <h3 className="text-lg font-semibold mb-1">No Resume Data Found</h3>
          <p className="text-sm text-muted-foreground mb-4">This candidate hasn't uploaded a resume or it failed to parse.</p>
        </CardContent>
      </Card>
    );
  }

  const { parsed_data } = data;
  const skills = parsed_data?.skills || [];
  const education = parsed_data?.education || [];
  const experience = parsed_data?.experience || [];

  return (
    <Card className="h-full flex flex-col">
      <CardHeader className="flex flex-row items-center justify-between border-b pb-4 bg-muted/10">
        <CardTitle className="flex items-center text-lg">
          <FileCheck2 className="w-5 h-5 mr-2 text-primary" /> AI Extracted Resume
        </CardTitle>
        <Button variant="outline" size="sm">
          <Download className="w-4 h-4 mr-2" /> Download Original
        </Button>
      </CardHeader>
      <CardContent className="flex-1 overflow-y-auto p-6 space-y-8">
        {/* Skills */}
        <div>
          <h4 className="text-sm font-semibold uppercase tracking-wider text-muted-foreground mb-3">Extracted Skills</h4>
          <div className="flex flex-wrap gap-2">
            {skills.map((s: string, i: number) => (
              <Badge key={i} variant="secondary" className="font-medium">{s}</Badge>
            ))}
            {skills.length === 0 && <span className="text-sm text-muted-foreground italic">No skills extracted</span>}
          </div>
        </div>

        {/* Experience */}
        <div>
          <h4 className="text-sm font-semibold uppercase tracking-wider text-muted-foreground mb-3">Work Experience</h4>
          <div className="space-y-4">
            {experience.map((exp: any, i: number) => (
              <div key={i} className="border-l-2 border-primary/30 pl-4 py-1">
                <div className="flex justify-between items-start">
                  <div>
                    <h5 className="font-semibold">{exp.job_title || "Unknown Role"}</h5>
                    <p className="text-sm text-muted-foreground">{exp.company || "Unknown Company"}</p>
                  </div>
                  {exp.dates && <Badge variant="outline" className="text-xs">{exp.dates}</Badge>}
                </div>
                {exp.description && <p className="text-sm mt-2 whitespace-pre-wrap text-foreground/80">{exp.description}</p>}
              </div>
            ))}
            {experience.length === 0 && <span className="text-sm text-muted-foreground italic">No experience extracted</span>}
          </div>
        </div>

        {/* Education */}
        <div>
          <h4 className="text-sm font-semibold uppercase tracking-wider text-muted-foreground mb-3">Education</h4>
          <div className="space-y-4">
            {education.map((edu: any, i: number) => (
              <div key={i} className="border-l-2 border-secondary/30 pl-4 py-1">
                <h5 className="font-semibold">{edu.degree || "Unknown Degree"}</h5>
                <p className="text-sm text-muted-foreground">{edu.institution || "Unknown Institution"}</p>
                {edu.graduation_year && <p className="text-xs text-muted-foreground mt-1">Class of {edu.graduation_year}</p>}
              </div>
            ))}
            {education.length === 0 && <span className="text-sm text-muted-foreground italic">No education extracted</span>}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
