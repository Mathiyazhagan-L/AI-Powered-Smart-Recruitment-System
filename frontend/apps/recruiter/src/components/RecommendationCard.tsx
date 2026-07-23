import React from "react";
import { apiClient } from "@/lib/apiClient";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { CheckCircle2, XCircle, BrainCircuit, ShieldAlert, ArrowRight, Star } from "lucide-react";
import Link from "next/link";

interface RecommendationCardProps {
  candidate: any;
  rank: number;
  jobId: string;
}

const ScoreDisplay = ({ label, score, suffix = "%" }: { label: string; score: number | null | undefined; suffix?: string }) => {
  const isAvailable = score !== null && score !== undefined && score > 0;
  
  return (
    <div className="flex flex-col items-center justify-center p-3 bg-muted/30 rounded-xl border">
      <span className="text-xs text-muted-foreground font-medium mb-1">{label}</span>
      {isAvailable ? (
        <span className="text-xl font-bold">{score}{suffix}</span>
      ) : (
        <span className="text-sm font-medium text-muted-foreground italic">Not Available</span>
      )}
    </div>
  );
};

export default function RecommendationCard({ candidate, rank, jobId }: RecommendationCardProps) {
  // Fetch detailed AI explanation
  const [explanation, setExplanation] = React.useState<any>(null);
  const [loadingExp, setLoadingExp] = React.useState(true);

  React.useEffect(() => {
    apiClient.get(`/recommendation/job/${jobId}/candidate/${candidate.candidate_id}`)
      .then(res => {
        setExplanation(res.data);
        setLoadingExp(false);
      })
      .catch(() => setLoadingExp(false));
  }, [jobId, candidate.candidate_id]);

  // Use data from backend ranking endpoint
  const overallScore = candidate.overall_score ? Math.min(Math.round(candidate.overall_score), 100) : null;
  const isTopMatch = rank <= 3 && overallScore && overallScore >= 80;
  
  // Explanation data (comes from recommendation engine)
  const expData = explanation || {};
  const matchingSkills = expData.matching_skills || [];
  const missingSkills = expData.missing_skills || [];
  const strengths = expData.strengths || [];
  const weaknesses = expData.weaknesses || [];
  const experienceMatch = expData.experience_match || "Unknown";
  const educationMatch = expData.education_match || "Unknown";

  return (
    <Card className={`relative overflow-hidden transition-all ${isTopMatch ? 'border-primary shadow-md' : 'border-border'}`}>
      {/* Top Match Banner */}
      {isTopMatch && (
        <div className="absolute top-0 right-0 bg-primary text-primary-foreground px-4 py-1 rounded-bl-xl text-xs font-bold flex items-center gap-1 shadow-sm">
          <Star className="w-3 h-3 fill-current" /> Top Candidate
        </div>
      )}

      <CardContent className="p-0">
        <div className="flex flex-col md:flex-row">
          
          {/* Left Panel: Identity & Scores */}
          <div className="flex-1 p-6 md:border-r border-border/50 bg-background/50">
            <div className="flex justify-between items-start mb-6">
              <div className="flex items-center gap-4">
                <div className={`w-12 h-12 rounded-full flex items-center justify-center text-lg font-bold text-white shadow-sm ${isTopMatch ? 'bg-gradient-to-br from-primary to-blue-600' : 'bg-muted-foreground'}`}>
                  #{rank}
                </div>
                <div>
                  <h3 className="text-xl font-bold">{candidate.candidate_name || `Candidate #${candidate.candidate_id}`}</h3>
                  <div className="flex items-center gap-2 mt-1">
                    <Badge variant="outline" className="text-xs font-normal">
                      Stage: {candidate.current_stage || "Applied"}
                    </Badge>
                    {candidate.integrity_score && candidate.integrity_score < 70 && (
                      <Badge variant="destructive" className="text-[10px] gap-1 h-5">
                        <ShieldAlert className="w-3 h-3" /> Review Required
                      </Badge>
                    )}
                  </div>
                </div>
              </div>
              
              <div className="text-right">
                <div className="text-xs text-muted-foreground font-medium mb-1 uppercase tracking-wider">AI Match Score</div>
                <div className={`text-3xl font-extrabold ${overallScore && overallScore >= 80 ? 'text-primary' : 'text-foreground'}`}>
                  {overallScore ? `${Math.round(overallScore)}%` : <span className="text-lg italic text-muted-foreground">Not Available</span>}
                </div>
              </div>
            </div>

            <div className="grid grid-cols-3 gap-3 mb-6">
              <ScoreDisplay label="ATS Score" score={candidate.ats_score ? Math.min(candidate.ats_score, 100) : null} />
              <ScoreDisplay label="Aptitude" score={candidate.aptitude_score ? Math.min(candidate.aptitude_score, 100) : null} />
              <ScoreDisplay label="Coding" score={candidate.coding_score ? Math.min(candidate.coding_score, 100) : null} />
              <ScoreDisplay label="Interview" score={candidate.interview_score ? Math.min(candidate.interview_score, 100) : null} />
              <ScoreDisplay label="GitHub" score={candidate.github_score ? Math.min(candidate.github_score, 100) : null} />
              <ScoreDisplay label="Resume Match" score={candidate.resume_match ? Math.min(candidate.resume_match, 100) : null} />
            </div>

            <Link href={`/candidates/${candidate.candidate_id}?job=${jobId}`}>
              <Button className="w-full gap-2 group">
                Review Profile <ArrowRight className="w-4 h-4 transition-transform group-hover:translate-x-1" />
              </Button>
            </Link>
          </div>

          {/* Right Panel: AI Explanation */}
          <div className="flex-1 p-6 bg-muted/10">
            <h4 className="text-sm font-bold flex items-center gap-2 mb-4 text-primary">
              <BrainCircuit className="w-4 h-4" /> AI Explanation
            </h4>

            <div className="space-y-4">
              {loadingExp ? (
                <div className="flex items-center justify-center py-6">
                  <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-primary"></div>
                </div>
              ) : (
                <>
                  {/* Skills */}
                  <div>
                    <p className="text-xs font-semibold text-muted-foreground mb-2">Skill Analysis</p>
                    <div className="flex flex-wrap gap-1.5 mb-2">
                      {matchingSkills.length > 0 ? matchingSkills.map((s: string, i: number) => (
                        <Badge key={i} variant="secondary" className="bg-success/10 text-success border-success/20 text-[10px] py-0">
                          <CheckCircle2 className="w-3 h-3 mr-1" /> {s}
                        </Badge>
                      )) : <span className="text-xs italic text-muted-foreground">Not Available</span>}
                    </div>
                    <div className="flex flex-wrap gap-1.5">
                      {missingSkills.length > 0 && missingSkills.map((s: string, i: number) => (
                        <Badge key={i} variant="outline" className="text-destructive border-destructive/20 bg-destructive/5 text-[10px] py-0">
                          <XCircle className="w-3 h-3 mr-1" /> Missing: {s}
                        </Badge>
                      ))}
                    </div>
                  </div>

                  {/* Match Details */}
                  <div className="grid grid-cols-2 gap-4">
                    <div className="bg-background border rounded-lg p-3">
                      <p className="text-[10px] uppercase tracking-wider text-muted-foreground mb-1">Experience Match</p>
                      <p className="text-sm font-medium">{experienceMatch}</p>
                    </div>
                    <div className="bg-background border rounded-lg p-3">
                      <p className="text-[10px] uppercase tracking-wider text-muted-foreground mb-1">Education Match</p>
                      <p className="text-sm font-medium">{educationMatch}</p>
                    </div>
                  </div>

                  {/* AI Notes */}
                  {(strengths.length > 0 || weaknesses.length > 0 || expData.recommendation) && (
                    <div className="bg-background border rounded-lg p-3 text-sm space-y-2">
                      {expData.recommendation && (
                        <div className="mb-2 pb-2 border-b">
                          <span className="font-semibold text-primary">Recommendation:</span> {expData.recommendation}
                        </div>
                      )}
                      {strengths.length > 0 && (
                        <div>
                          <span className="font-semibold text-success">Strengths:</span> {strengths.join(", ")}
                        </div>
                      )}
                      {weaknesses.length > 0 && (
                        <div>
                          <span className="font-semibold text-destructive">Weaknesses:</span> {weaknesses.join(", ")}
                        </div>
                      )}
                    </div>
                  )}
                </>
              )}
            </div>
          </div>

        </div>
      </CardContent>
    </Card>
  );
}
