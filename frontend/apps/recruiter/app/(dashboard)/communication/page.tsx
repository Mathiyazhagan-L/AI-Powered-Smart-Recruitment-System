"use client";

import { useState } from "react";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Search, Filter, MoreHorizontal, Mail, Send, AlertCircle, RefreshCw } from "lucide-react";
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuLabel, DropdownMenuSeparator, DropdownMenuTrigger } from "@/components/ui/dropdown-menu";
import { useEmailLogs, useResendEmail, EmailLog } from "@/lib/hooks/useEmailLogs";

const getStatusColor = (status: string) => {
  switch (status) {
    case "sent": return "bg-success/20 text-success border-success/30";
    case "pending": return "bg-warning/20 text-warning border-warning/30";
    case "failed": return "bg-destructive/20 text-destructive border-destructive/30";
    default: return "bg-muted text-muted-foreground";
  }
};

export default function CommunicationPage() {
  const [searchTerm, setSearchTerm] = useState("");
  const { data: logs, isLoading } = useEmailLogs();
  const resendEmail = useResendEmail();

  const activeLogs = logs || [];

  const filteredLogs = activeLogs.filter((l: EmailLog) => 
    (l.recipient_email || "").toLowerCase().includes(searchTerm.toLowerCase()) || 
    (l.subject || "").toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="flex flex-col h-full space-y-4">
      {/* Sticky Header */}
      <div className="sticky top-0 z-10 bg-muted/20 backdrop-blur-md pb-4 border-b border-border/50 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h2 className="text-3xl font-bold tracking-tight text-foreground">Communication Center</h2>
          <p className="text-muted-foreground mt-1">Track automated and manual candidate email communications.</p>
        </div>
        <div className="flex space-x-2">
          <Button variant="outline" className="bg-background">
            <Filter className="mr-2 h-4 w-4" /> Filters
          </Button>
        </div>
      </div>

      {/* Analytics Summary */}
      <div className="grid grid-cols-3 gap-4">
        <div className="border rounded-lg p-4 shadow-sm bg-background flex flex-col justify-center items-center">
          <div className="text-3xl font-bold text-foreground">{activeLogs.filter(l => l.status === 'sent').length}</div>
          <div className="text-sm text-muted-foreground mt-1 flex items-center"><Send className="w-3 h-3 mr-1 text-success"/> Sent Emails</div>
        </div>
        <div className="border rounded-lg p-4 shadow-sm bg-background flex flex-col justify-center items-center">
          <div className="text-3xl font-bold text-foreground">{activeLogs.filter(l => l.status === 'pending').length}</div>
          <div className="text-sm text-muted-foreground mt-1 flex items-center"><RefreshCw className="w-3 h-3 mr-1 text-warning"/> Pending Delivery</div>
        </div>
        <div className="border rounded-lg p-4 shadow-sm bg-background flex flex-col justify-center items-center">
          <div className="text-3xl font-bold text-foreground">{activeLogs.filter(l => l.status === 'failed').length}</div>
          <div className="text-sm text-muted-foreground mt-1 flex items-center"><AlertCircle className="w-3 h-3 mr-1 text-destructive"/> Delivery Failed</div>
        </div>
      </div>

      {/* Filters & Search */}
      <div className="flex flex-col sm:flex-row justify-between gap-4 py-2">
        <div className="flex flex-1 items-center space-x-2 max-w-md relative">
          <Search className="absolute left-3 h-4 w-4 text-muted-foreground" />
          <Input 
            placeholder="Search emails by recipient or subject..." 
            className="pl-9 bg-background"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>
      </div>

      {/* Responsive Data Table */}
      <div className="border rounded-lg bg-background flex-1 overflow-auto shadow-sm">
        <Table>
          <TableHeader className="bg-muted/50 sticky top-0 z-10 backdrop-blur-sm">
            <TableRow>
              <TableHead className="w-[80px]">ID</TableHead>
              <TableHead>Recipient</TableHead>
              <TableHead>Subject</TableHead>
              <TableHead>Trigger Event</TableHead>
              <TableHead>Timestamp</TableHead>
              <TableHead>Status</TableHead>
              <TableHead className="text-right">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {isLoading ? (
              <TableRow>
                <TableCell colSpan={7} className="h-40 text-center text-muted-foreground">
                  <div className="flex flex-col items-center justify-center">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mb-2"></div>
                    <p>Loading email logs...</p>
                  </div>
                </TableCell>
              </TableRow>
            ) : filteredLogs.length === 0 ? (
              <TableRow>
                <TableCell colSpan={7} className="h-40 text-center text-muted-foreground">
                  <div className="flex flex-col items-center justify-center">
                    <Mail className="h-8 w-8 mb-2 opacity-20" />
                    <p>No email logs found matching your criteria.</p>
                  </div>
                </TableCell>
              </TableRow>
            ) : (
              filteredLogs.map((log: EmailLog) => (
                <TableRow key={log.id} className="hover:bg-muted/30 transition-colors group">
                  <TableCell className="font-medium text-muted-foreground">#{log.id}</TableCell>
                  <TableCell className="font-semibold text-foreground">{log.recipient_email}</TableCell>
                  <TableCell className="max-w-[300px] truncate">{log.subject}</TableCell>
                  <TableCell><Badge variant="outline" className="font-normal">{log.event_type}</Badge></TableCell>
                  <TableCell className="text-muted-foreground">{new Date(log.created_at).toLocaleString()}</TableCell>
                  <TableCell>
                    <Badge variant="outline" className={`${getStatusColor(log.status)} uppercase text-[10px]`}>
                      {log.status}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-right">
                    <DropdownMenu>
                      <DropdownMenuTrigger className="inline-flex items-center justify-center rounded-md text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:pointer-events-none disabled:opacity-50 hover:bg-accent hover:text-accent-foreground h-8 w-8 p-0 opacity-0 group-hover:opacity-100 transition-opacity">
                        <span className="sr-only">Open menu</span>
                        <MoreHorizontal className="h-4 w-4" />
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end">
                        <DropdownMenuLabel>Actions</DropdownMenuLabel>
                        <DropdownMenuItem>View Email Preview</DropdownMenuItem>
                        <DropdownMenuSeparator />
                        {log.status === "failed" && (
                          <DropdownMenuItem onClick={() => resendEmail.mutate(log.id)}>
                            <RefreshCw className="mr-2 h-4 w-4 text-warning" /> Retry Send
                          </DropdownMenuItem>
                        )}
                        {log.status === "sent" && (
                          <DropdownMenuItem onClick={() => resendEmail.mutate(log.id)}>
                            <Send className="mr-2 h-4 w-4" /> Send Again
                          </DropdownMenuItem>
                        )}
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
