"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle, CardFooter } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Progress } from "@/components/ui/progress";
import { Separator } from "@/components/ui/separator";
import {
  ArrowLeft,
  Briefcase,
  Calendar,
  CheckCircle2,
  Clock,
  Download,
  Code,
  Mail,
  MapPin,
  MessageSquare,
  MoreHorizontal,
  Phone,
  Star,
  BrainCircuit,
  FileCode2,
  GraduationCap
} from "lucide-react";
import Link from "next/link";
import { use } from "react";
import { useCandidate } from "@/lib/hooks/useCandidates";
import RecruiterNotes from "@/components/RecruiterNotes";
import CandidateTimeline from "@/components/CandidateTimeline";
import ResumeViewer from "@/components/ResumeViewer";
import ScheduleInterviewModal from "@/components/ScheduleInterviewModal";

export default function CandidateProfile({ params }: { params: Promise<{ id: string }> }) {
  const resolvedParams = use(params);
  const { id } = resolvedParams;
  const { data: candidate, isLoading } = useCandidate(id);

  if (isLoading) {
    return <div className="flex items-center justify-center h-full min-h-[50vh]"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div></div>;
  }

  if (!candidate) {
    return <div className="flex items-center justify-center h-full min-h-[50vh] text-muted-foreground">Candidate not found</div>;
  }

  return (
    <div className="flex flex-col h-full space-y-6 max-w-7xl mx-auto">
      {/* Sticky Header Workspace */}
      <div className="sticky top-0 z-10 bg-muted/20 backdrop-blur-md pb-4 border-b border-border/50 flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div className="flex items-center space-x-4">
          <Link href="/candidates">
            <Button variant="ghost" size="icon" className="shrink-0 text-muted-foreground hover:text-foreground hover:bg-background">
              <ArrowLeft className="h-5 w-5" />
            </Button>
          </Link>
          <div>
            <div className="flex items-center space-x-3">
              <h2 className="text-3xl font-bold tracking-tight text-foreground">{candidate.full_name}</h2>
              <Badge variant="outline" className="text-xs bg-background">
                #{candidate.id}
              </Badge>
              <Badge className="bg-blue-500 hover:bg-blue-600 text-white shadow-sm border-none">
                {candidate.status || "Applied"}
              </Badge>
            </div>
            <p className="text-muted-foreground mt-1 flex items-center space-x-4">
              <span className="flex items-center"><Briefcase className="mr-1.5 h-4 w-4" /> {candidate.headline || "Candidate"}</span>
              {candidate.location && <span className="flex items-center"><MapPin className="mr-1.5 h-4 w-4" /> {candidate.location}</span>}
            </p>
          </div>
        </div>
        <div className="flex items-center space-x-2">
          <Button variant="outline" className="bg-background">
            <Mail className="mr-2 h-4 w-4" /> Email
          </Button>
          <ScheduleInterviewModal
            candidateId={parseInt(id)}
            candidateName={candidate.full_name || "Candidate"}
            jobId={1} // Temporary fallback until application linkage
            triggerElement={
              <Button variant="outline" className="bg-background">
                <Calendar className="mr-2 h-4 w-4" /> Schedule
              </Button>
            }
          />
          <Button className="bg-secondary text-secondary-foreground hover:bg-secondary/90 shadow-md">
            Move to Offer
          </Button>
          <Button variant="ghost" size="icon">
            <MoreHorizontal className="h-5 w-5" />
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Intelligence & Deep Dive */}
        <div className="lg:col-span-2 space-y-6">
          
          <Tabs defaultValue="insights" className="w-full">
            <TabsList className="grid w-full grid-cols-2">
              <TabsTrigger value="insights">AI Insights & Assessment</TabsTrigger>
              <TabsTrigger value="resume">Extracted Resume</TabsTrigger>
            </TabsList>
            
            <TabsContent value="insights" className="space-y-6 mt-4">
              {/* ATS Intelligence Summary */}
              <Card className="border-secondary/20 shadow-md bg-gradient-to-br from-background to-secondary/5 relative overflow-hidden">
                <div className="absolute top-0 right-0 p-4 opacity-10">
                  <BrainCircuit className="h-24 w-24" />
                </div>
                <CardHeader className="pb-3">
                  <CardTitle className="flex items-center text-xl">
                    <BrainCircuit className="mr-2 h-5 w-5 text-secondary" /> 
                    AI Resume Summary
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-muted-foreground leading-relaxed">
                    {candidate.summary || "No AI summary available for this candidate."}
                  </p>
                </CardContent>
              </Card>

              {/* GitHub Intelligence */}
              <Card className="shadow-sm">
                <CardHeader className="pb-3">
                  <CardTitle className="flex items-center text-lg">
                    <Code className="mr-2 h-5 w-5" /> 
                    GitHub Intelligence
                  </CardTitle>
                  <CardDescription>Automated analysis of public repositories</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid grid-cols-3 gap-4">
                    <div className="bg-muted/30 p-4 rounded-lg border text-center">
                      <div className="text-2xl font-bold text-foreground">{candidate.github_score || "-"}</div>
                      <div className="text-xs text-muted-foreground mt-1 uppercase tracking-wider">Code Quality</div>
                    </div>
                    <div className="bg-muted/30 p-4 rounded-lg border text-center">
                      <div className="text-2xl font-bold text-foreground">{candidate.github_repositories || "-"}</div>
                      <div className="text-xs text-muted-foreground mt-1 uppercase tracking-wider">Active Repos</div>
                    </div>
                    <div className="bg-muted/30 p-4 rounded-lg border text-center">
                      <div className="text-2xl font-bold text-foreground">{candidate.github_stars || "-"}</div>
                      <div className="text-xs text-muted-foreground mt-1 uppercase tracking-wider">Total Stars</div>
                    </div>
                  </div>
                  <Separator />
                  <div>
                    <h4 className="text-sm font-semibold mb-2">Top Languages</h4>
                    {candidate.github_languages && candidate.github_languages.length > 0 ? (
                      <div className="flex flex-wrap gap-2">
                        {candidate.github_languages.map((lang: any, index: number) => (
                          <Badge key={index} variant="secondary" className="bg-muted">{typeof lang === 'string' ? lang : (lang.name || JSON.stringify(lang))}</Badge>
                        ))}
                      </div>
                    ) : (
                      <p className="text-sm text-muted-foreground">No public languages analyzed.</p>
                    )}
                  </div>
                </CardContent>
              </Card>

              {/* Assessment & Tech Scores */}
              <Card className="shadow-sm">
                <CardHeader>
                  <CardTitle className="flex items-center text-lg">
                    <FileCode2 className="mr-2 h-5 w-5" />
                    Assessment Performance
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-6">
                    {/* Aptitude Results */}
                    <div className="flex items-center justify-between border-b pb-4">
                      <div className="flex items-center space-x-4">
                        <div className="h-12 w-12 rounded-full bg-blue-500/20 flex items-center justify-center border border-blue-500/30">
                          <span className="text-blue-500 font-bold text-lg">{candidate.aptitude_score || "-"}</span>
                        </div>
                        <div>
                          <h4 className="font-semibold">Aptitude Assessment</h4>
                          <p className="text-sm text-muted-foreground">Logical and quantitative reasoning</p>
                        </div>
                      </div>
                      <Button variant="outline" size="sm">View Detailed Report</Button>
                    </div>
                    {/* Coding Results */}
                    <div className="flex items-center justify-between border-b pb-4">
                      <div className="flex items-center space-x-4">
                        <div className="h-12 w-12 rounded-full bg-success/20 flex items-center justify-center border border-success/30">
                          <span className="text-success font-bold text-lg">{candidate.coding_score || "-"}</span>
                        </div>
                        <div>
                          <h4 className="font-semibold">Coding Assessment</h4>
                          <p className="text-sm text-muted-foreground">Technical implementation and problem solving</p>
                        </div>
                      </div>
                      <Button variant="outline" size="sm">Watch IDE Playback</Button>
                    </div>
                    {/* Interview Results */}
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-4">
                        <div className="h-12 w-12 rounded-full bg-amber-500/20 flex items-center justify-center border border-amber-500/30">
                          <span className="text-amber-500 font-bold text-lg">{candidate.interview_score || "-"}</span>
                        </div>
                        <div>
                          <h4 className="font-semibold">AI Video Interview</h4>
                          <p className="text-sm text-muted-foreground">Communication and behavioral traits</p>
                        </div>
                      </div>
                      <Button variant="outline" size="sm">Play Interview Audio</Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </TabsContent>
            
            <TabsContent value="resume" className="h-[800px] mt-4">
              <ResumeViewer candidateId={id} />
            </TabsContent>
          </Tabs>
        </div>

        {/* Right Column: Timeline & Profile Info */}
        <div className="space-y-6">
          
          {/* Overall Score */}
          <Card className="border-t-4 border-t-primary shadow-md">
            <CardContent className="pt-6">
              <div className="flex flex-col items-center text-center">
                <div className="relative flex items-center justify-center">
                  <svg className="w-32 h-32 transform -rotate-90">
                    <circle className="text-muted stroke-current" strokeWidth="8" cx="64" cy="64" r="56" fill="transparent"></circle>
                    <circle className="text-primary stroke-current" strokeWidth="8" strokeLinecap="round" cx="64" cy="64" r="56" fill="transparent" strokeDasharray="351.858" strokeDashoffset={351.858 - (351.858 * (candidate.ats_score || 0) / 100)}></circle>
                  </svg>
                  <div className="absolute text-3xl font-bold text-foreground">{candidate.ats_score || "-"}</div>
                </div>
                <h3 className="mt-4 font-semibold text-lg">Overall Match Score</h3>
                <p className="text-sm text-muted-foreground mt-1">Top 5% of all applicants for this role.</p>
              </div>
            </CardContent>
          </Card>

          {/* Contact Info */}
          <Card className="shadow-sm">
            <CardHeader className="pb-3">
              <CardTitle className="text-md">Contact Information</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3 text-sm">
              <div className="flex items-center text-muted-foreground">
                <Mail className="mr-3 h-4 w-4" />
                <span className="text-foreground">{candidate.email}</span>
              </div>
              {candidate.phone && (
                <div className="flex items-center text-muted-foreground">
                  <Phone className="mr-3 h-4 w-4" />
                  <span className="text-foreground">{candidate.phone}</span>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Notes */}
          <div className="h-[400px]">
            <RecruiterNotes candidateId={id} />
          </div>

          {/* Hiring Timeline */}
          <div className="h-[400px]">
            <CandidateTimeline candidateId={id} />
          </div>

        </div>
      </div>
    </div>
  );
}
