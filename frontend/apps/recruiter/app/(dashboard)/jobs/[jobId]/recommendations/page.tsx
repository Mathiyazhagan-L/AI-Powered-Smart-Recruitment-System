"use client";

import { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { ArrowLeft, Users, BrainCircuit, Activity, FileText, CheckCircle2 } from "lucide-react";
import RecommendationCard from "@/components/RecommendationCard";

import { apiClient } from "@/lib/apiClient";

export default function JobRecommendationsPage() {
  const params = useParams();
  const router = useRouter();
  const jobId = params.jobId as string;
  
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchRecommendations = async () => {
      try {
        const res = await apiClient.get(`/ranking/job/${jobId}`);
        setData(res.data);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    
    fetchRecommendations();
  }, [jobId]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>
    );
  }

  if (!data || data.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-full space-y-4">
        <BrainCircuit className="h-16 w-16 text-muted-foreground opacity-20" />
        <h2 className="text-xl font-semibold">No Recommendations Yet</h2>
        <p className="text-muted-foreground">AI recommendations will appear here once candidates apply and complete assessments.</p>
        <Button variant="outline" onClick={() => router.push("/jobs")}>Back to Jobs</Button>
      </div>
    );
  }

  // Summary stats
  const totalCandidates = data.length;
  const avgAts = Math.round(data.reduce((acc: number, curr: any) => acc + (curr.ats_score || 0), 0) / totalCandidates);
  const avgAssessment = Math.round(data.reduce((acc: number, curr: any) => acc + ((curr.aptitude_score || 0) + (curr.coding_score || 0) + (curr.interview_score || 0)) / 3, 0) / totalCandidates);
  const topCandidates = data.filter((c: any) => c.overall_score >= 80).length;

  return (
    <div className="flex flex-col space-y-6 pb-10">
      {/* Header */}
      <div className="flex items-center justify-between border-b pb-4">
        <div className="flex items-center space-x-4">
          <Button variant="ghost" size="icon" onClick={() => router.push("/jobs")}>
            <ArrowLeft className="h-5 w-5" />
          </Button>
          <div>
            <h1 className="text-2xl font-bold">AI Recommendations</h1>
            <p className="text-muted-foreground text-sm">Intelligent candidate ranking and matching for Job #{jobId}</p>
          </div>
        </div>
        <Button onClick={() => router.push(`/jobs/${jobId}/pipeline`)}>
          View Hiring Pipeline
        </Button>
      </div>

      {/* Summary Dashboard */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="bg-primary/5 border-primary/20">
          <CardContent className="p-6 flex flex-col items-center justify-center text-center space-y-2">
            <Users className="h-8 w-8 text-primary mb-2" />
            <p className="text-sm font-medium text-muted-foreground">Total Applicants</p>
            <h3 className="text-3xl font-bold">{totalCandidates}</h3>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-6 flex flex-col items-center justify-center text-center space-y-2">
            <CheckCircle2 className="h-8 w-8 text-success mb-2" />
            <p className="text-sm font-medium text-muted-foreground">Recommended</p>
            <h3 className="text-3xl font-bold">{topCandidates}</h3>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-6 flex flex-col items-center justify-center text-center space-y-2">
            <FileText className="h-8 w-8 text-blue-500 mb-2" />
            <p className="text-sm font-medium text-muted-foreground">Avg ATS Score</p>
            <h3 className="text-3xl font-bold">{avgAts}%</h3>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-6 flex flex-col items-center justify-center text-center space-y-2">
            <Activity className="h-8 w-8 text-amber-500 mb-2" />
            <p className="text-sm font-medium text-muted-foreground">Avg Assessment</p>
            <h3 className="text-3xl font-bold">{avgAssessment}%</h3>
          </CardContent>
        </Card>
      </div>

      {/* Recommendations List */}
      <div className="space-y-4">
        <h3 className="text-xl font-semibold flex items-center gap-2">
          <BrainCircuit className="h-5 w-5 text-primary" /> Top Matches
        </h3>
        <div className="grid grid-cols-1 gap-6">
          {data.map((candidate: any, index: number) => (
            <RecommendationCard 
              key={candidate.candidate_id} 
              candidate={candidate} 
              rank={index + 1}
              jobId={jobId}
            />
          ))}
        </div>
      </div>
    </div>
  );
}
