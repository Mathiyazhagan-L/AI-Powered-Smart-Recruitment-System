"use client";

import { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { useRecruiterDashboard, useHiringFunnel } from "@/lib/hooks/useDashboard";
import { useATSDistribution, useTopSkills, useOfferAnalytics } from "@/lib/hooks/useAnalytics";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, LineChart, Line, Legend
} from "recharts";
import { TrendingUp, TrendingDown, Users, Briefcase, Target, Award } from "lucide-react";

const COLORS = ["#22C55E", "#D4AF37", "#F59E0B", "#EF4444", "#6B7280", "#111827", "#3B82F6"];

export default function AnalyticsPage() {
  const { data: overview } = useRecruiterDashboard();
  const { data: funnelStats } = useHiringFunnel();
  const { data: atsDistribution, isLoading: atsLoading } = useATSDistribution();
  const { data: topSkills, isLoading: skillsLoading } = useTopSkills();
  const { data: offerAnalytics } = useOfferAnalytics();

  const funnelData = funnelStats ? [
    { name: "Applied", value: funnelStats.Applied || 0 },
    { name: "Screened", value: funnelStats.Screened || 0 },
    { name: "Shortlisted", value: funnelStats.Shortlisted || 0 },
    { name: "Interviewed", value: funnelStats.Interviewed || 0 },
    { name: "Selected", value: funnelStats.Selected || 0 },
  ] : [];

  const atsChartData = atsDistribution
    ? Object.entries(atsDistribution)
        .map(([range, count]) => ({ name: range, value: count as number }))
        .filter(item => item.value > 0)
    : [];

  const skillsData = (topSkills || []).slice(0, 10).map((s: { skill: string; count: number }) => ({
    name: s.skill,
    count: s.count,
  }));

  // Derived rates
  const applied = funnelStats?.Applied || 0;
  const interviewed = funnelStats?.Interviewed || 0;
  const selected = funnelStats?.Selected || 0;
  const interviewRate = applied > 0 ? ((interviewed / applied) * 100).toFixed(1) : "0";
  const offerRate = interviewed > 0 ? ((selected / interviewed) * 100).toFixed(1) : "0";
  const conversionRate = applied > 0 ? ((selected / applied) * 100).toFixed(1) : "0";

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-3xl font-bold tracking-tight text-foreground">Analytics</h2>
        <p className="text-muted-foreground mt-2">Real-time recruitment performance metrics.</p>
      </div>

      {/* KPI Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Total Candidates</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{overview?.total_candidates ?? 0}</div>
            <p className="text-xs text-muted-foreground mt-1">All registered</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Interview Rate</CardTitle>
            <Target className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-blue-500">{interviewRate}%</div>
            <p className="text-xs text-muted-foreground mt-1">Applied → Interviewed</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Offer Rate</CardTitle>
            <Award className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-success">{offerRate}%</div>
            <p className="text-xs text-muted-foreground mt-1">Interviewed → Selected</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Conversion Rate</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-warning">{conversionRate}%</div>
            <p className="text-xs text-muted-foreground mt-1">Applied → Hired</p>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        {/* Hiring Funnel */}
        <Card>
          <CardHeader>
            <CardTitle>Hiring Funnel</CardTitle>
            <CardDescription>Candidate progression stages</CardDescription>
          </CardHeader>
          <CardContent className="h-[300px]">
            {funnelData.every(d => d.value === 0) ? (
              <div className="flex items-center justify-center h-full text-muted-foreground text-sm">
                No pipeline data yet.
              </div>
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={funnelData}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} opacity={0.3} />
                  <XAxis dataKey="name" fontSize={11} tickLine={false} axisLine={false} />
                  <YAxis fontSize={11} tickLine={false} axisLine={false} />
                  <Tooltip contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }} />
                  <Bar dataKey="value" name="Candidates" fill="#111827" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            )}
          </CardContent>
        </Card>

        {/* ATS Distribution */}
        <Card>
          <CardHeader>
            <CardTitle>ATS Score Distribution</CardTitle>
            <CardDescription>Quality of candidate resumes</CardDescription>
          </CardHeader>
          <CardContent className="h-[300px]">
            {atsLoading ? (
              <div className="flex items-center justify-center h-full"><div className="animate-spin rounded-full h-6 w-6 border-b-2 border-primary" /></div>
            ) : atsChartData.length === 0 || atsChartData.every(d => d.value === 0) ? (
              <div className="flex items-center justify-center h-full text-muted-foreground text-sm">
                No ATS data yet.
              </div>
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie data={atsChartData} cx="50%" cy="50%" innerRadius={60} outerRadius={100} paddingAngle={3} dataKey="value">
                    {atsChartData.map((_, i) => (
                      <Cell key={i} fill={COLORS[i % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip contentStyle={{ borderRadius: '8px', border: 'none' }} />
                  <Legend />
                </PieChart>
              </ResponsiveContainer>
            )}
          </CardContent>
        </Card>

        {/* Top Skills */}
        <Card>
          <CardHeader>
            <CardTitle>Top Skills in Talent Pool</CardTitle>
            <CardDescription>Most common skills among candidates</CardDescription>
          </CardHeader>
          <CardContent className="h-[300px]">
            {skillsLoading ? (
              <div className="flex items-center justify-center h-full"><div className="animate-spin rounded-full h-6 w-6 border-b-2 border-primary" /></div>
            ) : skillsData.length === 0 ? (
              <div className="flex items-center justify-center h-full text-muted-foreground text-sm">
                No skills data yet.
              </div>
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={skillsData} layout="vertical" margin={{ left: 20 }}>
                  <CartesianGrid strokeDasharray="3 3" horizontal={false} opacity={0.3} />
                  <XAxis type="number" fontSize={11} tickLine={false} axisLine={false} />
                  <YAxis type="category" dataKey="name" fontSize={11} tickLine={false} axisLine={false} width={80} />
                  <Tooltip contentStyle={{ borderRadius: '8px', border: 'none' }} />
                  <Bar dataKey="count" name="Candidates" fill="#D4AF37" radius={[0, 4, 4, 0]} />
                </BarChart>
              </ResponsiveContainer>
            )}
          </CardContent>
        </Card>

        {/* Offer Analytics */}
        <Card>
          <CardHeader>
            <CardTitle>Offer Analytics</CardTitle>
            <CardDescription>Offer generation and acceptance overview</CardDescription>
          </CardHeader>
          <CardContent>
            {!offerAnalytics ? (
              <div className="flex items-center justify-center h-40 text-muted-foreground text-sm">No offer data yet.</div>
            ) : (
              <div className="space-y-4 pt-2">
                {Object.entries(offerAnalytics as Record<string, number>).map(([key, val]) => (
                  <div key={key} className="flex items-center justify-between border-b pb-2 last:border-0">
                    <span className="text-sm text-muted-foreground capitalize">{key.replace(/_/g, " ")}</span>
                    <span className="font-semibold text-foreground">{val ?? 0}</span>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
