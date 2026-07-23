"use client";

import { useState } from "react";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Search, Filter, MoreHorizontal, FileText, Send, Download, Plus } from "lucide-react";
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuLabel, DropdownMenuSeparator, DropdownMenuTrigger, DropdownMenuGroup } from "@/components/ui/dropdown-menu";
import { useOffers, useUpdateOfferStatus, useAutoGenerateOffer, Offer } from "@/lib/hooks/useOffers";
import { useInterviews } from "@/lib/hooks/useInterviews";

const getStatusColor = (status: string) => {
  switch (status) {
    case "Accepted": return "bg-success text-success-foreground border-transparent";
    case "Sent": return "bg-blue-100 text-blue-800 border-transparent dark:bg-blue-900 dark:text-blue-300";
    case "Negotiating": return "bg-warning text-warning-foreground border-transparent";
    case "Draft": return "bg-muted text-muted-foreground border-transparent";
    case "Declined": return "bg-destructive text-destructive-foreground border-transparent";
    default: return "bg-muted text-muted-foreground";
  }
};

export default function OffersPage() {
  const [searchTerm, setSearchTerm] = useState("");
  const { data: offers, isLoading } = useOffers();
  const { data: interviews } = useInterviews();
  const updateStatus = useUpdateOfferStatus();
  const autoGenerate = useAutoGenerateOffer();

  const activeOffers = offers || [];
  
  // Find candidates who are selected but don't have an offer yet
  const selectedInterviews = (interviews || []).filter((i: any) => i.status === "Selected");
  const pendingOfferCandidates = selectedInterviews.filter(
    (i: any) => !activeOffers.find((o: Offer) => o.candidate_id === i.candidate_id && o.job_id === i.job_id)
  );

  const filteredOffers = activeOffers.filter((o: Offer) => 
    (o.candidate_name || "").toLowerCase().includes(searchTerm.toLowerCase()) || 
    (o.position_title || "").toLowerCase().includes(searchTerm.toLowerCase()) ||
    o.id.toString().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="flex flex-col h-full space-y-4">
      {/* Sticky Header */}
      <div className="sticky top-0 z-10 bg-muted/20 backdrop-blur-md pb-4 border-b border-border/50 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h2 className="text-3xl font-bold tracking-tight text-foreground">Offer Management</h2>
          <p className="text-muted-foreground mt-1">Create, track, and manage candidate offers.</p>
        </div>
        <div className="flex space-x-2">
          <Button variant="outline" className="bg-background">
            <Download className="mr-2 h-4 w-4" /> Export
          </Button>
        </div>
      </div>

      {/* Filters & Search */}
      <div className="flex flex-col sm:flex-row justify-between gap-4 py-2">
        <div className="flex flex-1 items-center space-x-2 max-w-md relative">
          <Search className="absolute left-3 h-4 w-4 text-muted-foreground" />
          <Input 
            placeholder="Search offers..." 
            className="pl-9 bg-background"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>
        <div className="flex space-x-2">
          <Button variant="outline" className="bg-background">
            <Filter className="mr-2 h-4 w-4" /> Filters
          </Button>
        </div>
      </div>

      {/* Pending Offers Section */}
      {pendingOfferCandidates.length > 0 && (
        <div className="border rounded-lg bg-background p-4 shadow-sm mb-6">
          <h3 className="text-lg font-bold mb-4 text-warning">Pending Offers (Selected Candidates)</h3>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Candidate</TableHead>
                <TableHead>Position</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {pendingOfferCandidates.map((i: any) => (
                <TableRow key={`pending-${i.id}`}>
                  <TableCell className="font-semibold">{i.candidate_name || `Candidate #${i.candidate_id}`}</TableCell>
                  <TableCell>{i.job_title || `Job #${i.job_id}`}</TableCell>
                  <TableCell className="text-right">
                    <Button 
                      onClick={() => autoGenerate.mutate(i.id)} 
                      disabled={autoGenerate.isPending}
                      className="bg-primary hover:bg-primary/90"
                    >
                      {autoGenerate.isPending ? "Generating..." : "Generate & Send Offer"}
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      )}

      <h3 className="text-lg font-bold mb-2">Sent & Active Offers</h3>

      {/* Responsive Data Table */}
      <div className="border rounded-lg bg-background flex-1 overflow-auto shadow-sm">
        <Table>
          <TableHeader className="bg-muted/50 sticky top-0 z-10 backdrop-blur-sm">
            <TableRow>
              <TableHead className="w-[120px]">Offer ID</TableHead>
              <TableHead>Candidate</TableHead>
              <TableHead>Position</TableHead>
              <TableHead>Base Salary</TableHead>
              <TableHead>Equity</TableHead>
              <TableHead>Expiration</TableHead>
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
                    <p>Loading offers...</p>
                  </div>
                </TableCell>
              </TableRow>
            ) : filteredOffers.length === 0 ? (
              <TableRow>
                <TableCell colSpan={8} className="h-40 text-center text-muted-foreground">
                  <div className="flex flex-col items-center justify-center">
                    <FileText className="h-8 w-8 mb-2 opacity-20" />
                    <p>No offers found matching your criteria.</p>
                  </div>
                </TableCell>
              </TableRow>
            ) : (
              filteredOffers.map((offer: Offer) => (
                <TableRow key={offer.id} className="hover:bg-muted/30 transition-colors group">
                  <TableCell className="font-medium text-muted-foreground">#{offer.id}</TableCell>
                  <TableCell className="font-semibold text-foreground">{offer.candidate_name || `Candidate #${offer.candidate_id}`}</TableCell>
                  <TableCell>{offer.position_title || `Job #${offer.job_id}`}</TableCell>
                  <TableCell className="font-medium">{offer.package_amount ? `$${offer.package_amount}` : "$0"}</TableCell>
                  <TableCell>0%</TableCell>
                  <TableCell className="text-muted-foreground">{offer.offer_expiry_date || "-"}</TableCell>
                  <TableCell>
                    <Badge variant="secondary" className={`${getStatusColor(offer.offer_status)}`}>
                      {offer.offer_status}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-right">
                    <DropdownMenu>
                      <DropdownMenuTrigger className="inline-flex items-center justify-center rounded-md text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:pointer-events-none disabled:opacity-50 hover:bg-accent hover:text-accent-foreground h-8 w-8 p-0 opacity-0 group-hover:opacity-100 transition-opacity">
                        <span className="sr-only">Open menu</span>
                        <MoreHorizontal className="h-4 w-4" />
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end">
                        <DropdownMenuGroup>
                          <DropdownMenuLabel>Actions</DropdownMenuLabel>
                          <DropdownMenuItem 
                            disabled={!offer.offer_pdf_path}
                            onClick={() => offer.offer_pdf_path && window.open(`http://localhost:8000/offers/${offer.id}/download`, "_blank")}
                          >
                            View Document
                          </DropdownMenuItem>
                          <DropdownMenuItem>Edit Details</DropdownMenuItem>
                        </DropdownMenuGroup>
                        <DropdownMenuSeparator />
                        {offer.offer_status === "Draft" && <DropdownMenuItem onClick={() => updateStatus.mutate({ id: offer.id, action: "send" })}><Send className="mr-2 h-4 w-4" /> Send Offer</DropdownMenuItem>}
                        {offer.offer_status === "Sent" && <DropdownMenuItem>Resend Reminder</DropdownMenuItem>}
                        <DropdownMenuSeparator />
                        <DropdownMenuItem className="text-destructive" onClick={() => updateStatus.mutate({ id: offer.id, action: "revoke" })}>Revoke Offer</DropdownMenuItem>
                      </DropdownMenuContent>
                    </DropdownMenu>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}
