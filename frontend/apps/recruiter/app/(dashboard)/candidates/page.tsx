"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { 
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow 
} from "@/components/ui/table";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { useCandidates, CandidateProfile } from "@/lib/hooks/useCandidates";
import { 
  DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuLabel, 
  DropdownMenuSeparator, DropdownMenuTrigger 
} from "@/components/ui/dropdown-menu";
import { Search, Filter, MoreHorizontal, ChevronLeft, ChevronRight, Download } from "lucide-react";

const getStatusColor = (status: string) => {
  switch (status) {
    case "Applied": return "bg-neutral text-white";
    case "Assessment": return "bg-primary text-primary-foreground";
    case "HR Review": return "bg-warning text-warning-foreground";
    case "Interview": return "bg-blue-500 text-white";
    case "Offer": return "bg-secondary text-secondary-foreground";
    case "Hired": return "bg-success text-success-foreground";
    case "Rejected": return "bg-destructive text-destructive-foreground";
    default: return "bg-neutral text-white";
  }
};

const triggerButtonClass =
  "inline-flex items-center justify-center rounded-md text-sm font-medium transition-colors " +
  "focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring " +
  "disabled:pointer-events-none disabled:opacity-50 hover:bg-accent hover:text-accent-foreground " +
  "h-8 w-8 p-0 opacity-0 group-hover:opacity-100 transition-opacity";

export default function CandidatesPage() {
  const router = useRouter();
  const [searchTerm, setSearchTerm] = useState("");
  const [statusFilter, setStatusFilter] = useState<string | null>(null);
  const { data: candidates, isLoading } = useCandidates();

  const allCandidates = candidates || [];

  const filteredCandidates = allCandidates.filter((c: CandidateProfile) => {
    const matchSearch =
      (c.full_name || "").toLowerCase().includes(searchTerm.toLowerCase()) ||
      (c.headline || "").toLowerCase().includes(searchTerm.toLowerCase()) ||
      c.id.toString().includes(searchTerm.toLowerCase());
    const matchStatus = !statusFilter || c.status === statusFilter;
    return matchSearch && matchStatus;
  });

  const exportCSV = () => {
    const headers = ["ID", "Name", "Position", "ATS Score", "GitHub Score", "Technical Score", "Status", "Email", "Phone"];
    const rows = filteredCandidates.map((c: CandidateProfile) => [
      c.id,
      `"${c.full_name || ""}"`,
      `"${c.headline || ""}"`,
      c.ats_score || "",
      c.github_score || "",
      c.technical_score || "",
      c.status || "Applied",
      c.email || "",
      c.phone || "",
    ]);
    const csvContent = [headers.join(","), ...rows.map(r => r.join(","))].join("\n");
    const blob = new Blob([csvContent], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `candidates_${new Date().toISOString().split("T")[0]}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const statuses = ["Applied", "Screening", "Assessment", "Interview", "HR Review", "Offer", "Hired", "Rejected"];

  return (
    <div className="flex flex-col h-full space-y-4">
      {/* Header */}
      <div className="sticky top-0 z-10 bg-muted/20 backdrop-blur-md pb-4 border-b border-border/50 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h2 className="text-3xl font-bold tracking-tight text-foreground">Candidate Management</h2>
          <p className="text-muted-foreground mt-1">Manage and track all applicants across your organization.</p>
        </div>
        <div className="flex space-x-2">
          <Button variant="outline" className="hidden sm:flex" onClick={exportCSV}>
            <Download className="mr-2 h-4 w-4" />
            Export CSV
          </Button>
        </div>
      </div>

      {/* Filters & Search */}
      <div className="flex flex-col sm:flex-row justify-between gap-4 py-2">
        <div className="flex flex-1 items-center space-x-2 max-w-md relative">
          <Search className="absolute left-3 h-4 w-4 text-muted-foreground" />
          <Input 
            placeholder="Search by name, role, or ID..." 
            className="pl-9 bg-background"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>
        <div className="flex space-x-2 flex-wrap gap-2">
          <Button 
            variant="outline" 
            className={`bg-background ${!statusFilter ? 'border-primary' : ''}`}
            onClick={() => setStatusFilter(null)}
          >
            <Filter className="mr-2 h-4 w-4" />
            All
          </Button>
          <DropdownMenu>
            <DropdownMenuTrigger className="inline-flex items-center justify-center gap-2 rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 border border-input bg-background hover:bg-accent hover:text-accent-foreground h-10 px-4 py-2">
              Status{statusFilter ? `: ${statusFilter}` : ""}
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuLabel>Filter by Status</DropdownMenuLabel>
              <DropdownMenuSeparator />
              <DropdownMenuItem onClick={() => setStatusFilter(null)}>All Candidates</DropdownMenuItem>
              {statuses.map(s => (
                <DropdownMenuItem key={s} onClick={() => setStatusFilter(s)}>{s}</DropdownMenuItem>
              ))}
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </div>

      {/* Data Table */}
      <div className="border rounded-lg bg-background flex-1 overflow-auto shadow-sm">
        <Table>
          <TableHeader className="bg-muted/50 sticky top-0 z-10 backdrop-blur-sm">
            <TableRow>
              <TableHead className="w-[100px]">ID</TableHead>
              <TableHead>Name</TableHead>
              <TableHead>Position</TableHead>
              <TableHead className="text-center">ATS Score</TableHead>
              <TableHead className="text-center">GitHub</TableHead>
              <TableHead className="text-center">Technical</TableHead>
              <TableHead>Status</TableHead>
              <TableHead className="text-right">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {isLoading ? (
              <TableRow>
                <TableCell colSpan={8} className="h-40 text-center text-muted-foreground">
                  <div className="flex flex-col items-center justify-center">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mb-2"></div>
                    <p>Loading candidates...</p>
                  </div>
                </TableCell>
              </TableRow>
            ) : filteredCandidates.length === 0 ? (
              <TableRow>
                <TableCell colSpan={8} className="h-40 text-center text-muted-foreground">
                  <div className="flex flex-col items-center justify-center">
                    <Search className="h-8 w-8 mb-2 opacity-20" />
                    <p>No candidates found.</p>
                  </div>
                </TableCell>
              </TableRow>
            ) : (
              filteredCandidates.map((candidate: CandidateProfile) => (
                <TableRow key={candidate.id} className="hover:bg-muted/30 transition-colors group">
                  <TableCell className="font-medium text-muted-foreground">#{candidate.id}</TableCell>
                  <TableCell>
                    <button
                      onClick={() => router.push(`/candidates/${candidate.id}`)}
                      className="font-semibold text-primary hover:text-secondary transition-colors text-left"
                    >
                      {candidate.full_name}
                    </button>
                  </TableCell>
                  <TableCell>{candidate.headline || "—"}</TableCell>
                  <TableCell className="text-center">
                    <span className={`font-semibold ${candidate.ats_score && candidate.ats_score >= 90 ? 'text-success' : candidate.ats_score && candidate.ats_score >= 80 ? 'text-warning' : ''}`}>
                      {candidate.ats_score ?? "—"}
                    </span>
                  </TableCell>
                  <TableCell className="text-center">
                    {candidate.github_score ? (
                      <Badge variant="outline" className="bg-primary/5 border-primary/20">{candidate.github_score}</Badge>
                    ) : (
                      <span className="text-muted-foreground/50">—</span>
                    )}
                  </TableCell>
                  <TableCell className="text-center">
                    {candidate.technical_score ? (
                      <span className="font-medium">{candidate.technical_score}</span>
                    ) : (
                      <span className="text-muted-foreground/50">—</span>
                    )}
                  </TableCell>
                  <TableCell>
                    <Badge className={`${getStatusColor(candidate.status || 'Applied')} border-none shadow-none`}>
                      {candidate.status || 'Applied'}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-right">
                    <DropdownMenu>
                      <DropdownMenuTrigger className={triggerButtonClass}>
                        <span className="sr-only">Open menu</span>
                        <MoreHorizontal className="h-4 w-4" />
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end" className="w-[160px]">
                        <DropdownMenuLabel>Actions</DropdownMenuLabel>
                        <DropdownMenuItem onClick={() => router.push(`/candidates/${candidate.id}`)}>
                          View Profile
                        </DropdownMenuItem>
                        <DropdownMenuSeparator />
                        <DropdownMenuItem className="text-destructive focus:bg-destructive/10">
                          Reject Candidate
                        </DropdownMenuItem>
                      </DropdownMenuContent>
                    </DropdownMenu>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </div>

      {/* Pagination */}
      <div className="flex items-center justify-between px-2 py-4 border-t">
        <div className="text-sm text-muted-foreground">
          Showing <strong>{filteredCandidates.length}</strong> of <strong>{allCandidates.length}</strong> candidates
        </div>
        <div className="flex space-x-2">
          <Button variant="outline" size="sm" disabled>
            <ChevronLeft className="h-4 w-4 mr-1" />Previous
          </Button>
          <Button variant="outline" size="sm" disabled>
            Next<ChevronRight className="h-4 w-4 ml-1" />
          </Button>
        </div>
      </div>
    </div>
  );
}
