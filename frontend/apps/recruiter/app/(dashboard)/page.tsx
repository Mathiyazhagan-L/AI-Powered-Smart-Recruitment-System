"use client";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Users, Briefcase, Calendar, Gift, TrendingUp } from "lucide-react";
import { useRecruiterDashboard, useHiringFunnel } from "@/lib/hooks/useDashboard";
import { useATSDistribution } from "@/lib/hooks/useAnalytics";
import Link from "next/link";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell
} from "recharts";

const COLORS = ["#22C55E", "#D4AF37", "#F59E0B", "#EF4444", "#6B7280", "#111827"];

export default function Dashboard() {
  const { data: overview, isLoading: overviewLoading } = useRecruiterDashboard();
  const { data: funnelStats, isLoading: funnelLoading } = useHiringFunnel();
  const { data: atsDistribution, isLoading: atsLoading } = useATSDistribution();

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

  if (overviewLoading || funnelLoading) {
    return (
      <div className="flex items-center justify-center h-full min-h-[50vh]">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-3xl font-bold tracking-tight text-foreground">Executive Dashboard</h2>
        <p className="text-muted-foreground mt-2">Overview of your recruitment pipeline and team performance.</p>
      </div>

      {/* KPI Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Link href="/candidates" className="block">
          <Card className="hover:shadow-lg transition-all duration-300 cursor-pointer h-full">
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium">Total Candidates</CardTitle>
              <Users className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{overview?.total_candidates ?? 0}</div>
              <p className="text-xs mt-1 text-success flex items-center">
                <TrendingUp className="h-3 w-3 mr-1" /> Active
              </p>
            </CardContent>
          </Card>
        </Link>
        <Link href="/jobs" className="block">
          <Card className="hover:shadow-lg transition-all duration-300 cursor-pointer h-full">
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium">Active Jobs</CardTitle>
              <Briefcase className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{overview?.total_jobs ?? 0}</div>
              <p className="text-xs text-muted-foreground mt-1">Total open requisitions</p>
            </CardContent>
          </Card>
        </Link>
        <Link href="/applications" className="block">
          <Card className="hover:shadow-lg transition-all duration-300 cursor-pointer h-full">
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium">Total Applications</CardTitle>
              <Calendar className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{overview?.total_applications ?? 0}</div>
              <p className="text-xs text-muted-foreground mt-1">All time</p>
            </CardContent>
          </Card>
        </Link>
        <Link href="/offers" className="block">
          <Card className="hover:shadow-lg transition-all duration-300 cursor-pointer h-full">
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium">Selected Candidates</CardTitle>
              <Gift className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{overview?.selected_candidates ?? 0}</div>
              <p className="text-xs mt-1 text-success flex items-center">
                <TrendingUp className="h-3 w-3 mr-1" /> Accepted Offers
              </p>
            </CardContent>
          </Card>
        </Link>
      </div>

      {/* Charts */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-7">
        <Card className="col-span-4 hover:shadow-lg transition-all duration-300">
          <CardHeader>
            <CardTitle>Hiring Funnel</CardTitle>
            <CardDescription>Candidate progression across all active pipelines</CardDescription>
          </CardHeader>
          <CardContent className="h-[350px]">
            {funnelData.every(d => d.value === 0) ? (
              <div className="flex items-center justify-center h-full text-muted-foreground text-sm">
                No pipeline data yet. Add candidates to jobs to see the funnel.
              </div>
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={funnelData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} opacity={0.3} />
                  <XAxis dataKey="name" stroke="#888888" fontSize={12} tickLine={false} axisLine={false} />
                  <YAxis stroke="#888888" fontSize={12} tickLine={false} axisLine={false} />
                  <Tooltip cursor={{ fill: 'rgba(0,0,0,0.05)' }} contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }} />
                  <Bar dataKey="value" fill="#111827" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            )}
          </CardContent>
        </Card>

        <Card className="col-span-3 hover:shadow-lg transition-all duration-300">
          <CardHeader>
            <CardTitle>ATS Score Distribution</CardTitle>
            <CardDescription>Breakdown of candidate ATS scores</CardDescription>
          </CardHeader>
          <CardContent className="h-[350px] flex items-center justify-center">
            {atsLoading ? (
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary" />
            ) : atsChartData.length === 0 || atsChartData.every(d => d.value === 0) ? (
              <div className="text-muted-foreground text-sm text-center">
                No ATS data yet. Candidates need resumes parsed to appear here.
              </div>
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={atsChartData}
                    cx="50%"
                    cy="50%"
                    innerRadius={70}
                    outerRadius={110}
                    paddingAngle={3}
                    dataKey="value"
                    label={({ name, percent }) => `${name} ${((percent || 0) * 100).toFixed(0)}%`}
                    labelLine={false}
                  >
                    {atsChartData.map((_, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }} />
                </PieChart>
              </ResponsiveContainer>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
