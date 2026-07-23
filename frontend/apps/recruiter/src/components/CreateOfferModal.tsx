"use client";

import React, { useState } from "react";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogTrigger } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { useCreateOffer } from "@/lib/hooks/useOffers";
import { useInterviews } from "@/lib/hooks/useInterviews";

interface CreateOfferModalProps {
  triggerElement?: React.ReactNode;
}

export default function CreateOfferModal({ triggerElement }: CreateOfferModalProps) {
  const [open, setOpen] = useState(false);
  const [jobId, setJobId] = useState("");
  const [candidateId, setCandidateId] = useState("");
  const [baseSalary, setBaseSalary] = useState("");
  const [equity, setEquity] = useState("0");
  const [bonus, setBonus] = useState("0");
  const [selectedCandidate, setSelectedCandidate] = useState<any>(null);

  const createMutation = useCreateOffer();
  const { data: interviews } = useInterviews();
  const selectedInterviews = (interviews || []).filter((i: any) => i.status === "Selected");

  const handleCreate = () => {
    if (!selectedCandidate || !baseSalary) return;

    createMutation.mutate({
      job_id: selectedCandidate.job_id,
      candidate_id: selectedCandidate.candidate_id,
      base_salary: parseFloat(baseSalary),
      equity_percentage: parseFloat(equity),
      signing_bonus: parseFloat(bonus),
      validity_days: 7
    }, {
      onSuccess: () => {
        setOpen(false);
      }
    });
  };

  const handleCandidateChange = (val: string | null) => {
    if (!val) return;
    const inter = selectedInterviews.find((i: any) => i.id.toString() === val);
    if (inter) {
      setSelectedCandidate(inter);
      setCandidateId(inter.candidate_id.toString());
      setJobId(inter.job_id.toString());
    }
  };

  return (
    <>
      <div onClick={() => setOpen(true)} className="inline-block cursor-pointer">
        {triggerElement || <Button>Create Offer</Button>}
      </div>
      <Dialog open={open} onOpenChange={setOpen}>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle>Generate New Offer</DialogTitle>
        </DialogHeader>
        <div className="grid gap-4 py-4">
          <div className="grid grid-cols-4 items-center gap-4">
            <Label className="text-right">Candidate</Label>
            <Select onValueChange={handleCandidateChange}>
              <SelectTrigger className="col-span-3">
                <SelectValue placeholder="Select a candidate" />
              </SelectTrigger>
              <SelectContent>
                {selectedInterviews.map((i: any) => (
                  <SelectItem key={i.id} value={i.id.toString()}>
                    {i.candidate_name || `Candidate #${i.candidate_id}`} - {i.job_title || `Job #${i.job_id}`}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="grid grid-cols-4 items-center gap-4">
            <Label className="text-right">Base Salary ($)</Label>
            <Input type="number" value={baseSalary} onChange={e => setBaseSalary(e.target.value)} className="col-span-3" />
          </div>
          <div className="grid grid-cols-4 items-center gap-4">
            <Label className="text-right">Equity (%)</Label>
            <Input type="number" step="0.01" value={equity} onChange={e => setEquity(e.target.value)} className="col-span-3" />
          </div>
          <div className="grid grid-cols-4 items-center gap-4">
            <Label className="text-right">Bonus ($)</Label>
            <Input type="number" value={bonus} onChange={e => setBonus(e.target.value)} className="col-span-3" />
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => setOpen(false)}>Cancel</Button>
          <Button onClick={handleCreate} disabled={createMutation.isPending || !selectedCandidate}>
            {createMutation.isPending ? "Generating..." : "Proceed to Generate Offer Letter"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
    </>
  );
}
