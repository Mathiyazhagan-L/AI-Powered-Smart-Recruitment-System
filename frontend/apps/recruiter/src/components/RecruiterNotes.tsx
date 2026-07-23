"use client";

import React, { useState, useEffect } from "react";
import { apiClient } from "@/lib/apiClient";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { MessageSquare, Plus, Save, X, Star } from "lucide-react";

interface Note {
  id: number;
  candidate_id: number;
  recruiter_id: number;
  title: string | null;
  note_type: string;
  content: string;
  visibility: string;
  rating: number | null;
  created_at: string;
}

export default function RecruiterNotes({ candidateId }: { candidateId: string | number }) {
  const [notes, setNotes] = useState<Note[]>([]);
  const [loading, setLoading] = useState(true);
  const [isAdding, setIsAdding] = useState(false);
  
  const [newNote, setNewNote] = useState({
    title: "",
    note_type: "General",
    content: "",
    visibility: "Team",
    rating: 0
  });

  const fetchNotes = async () => {
    try {
      const res = await apiClient.get(`/recruiter-workspace/notes/candidate/${candidateId}`);
      setNotes(res.data);
    } catch (e) {
      console.error("Failed to fetch notes", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchNotes();
  }, [candidateId]);

  const handleSave = async () => {
    if (!newNote.content.trim()) return;
    try {
      const payload = {
        ...newNote,
        candidate_id: Number(candidateId),
        rating: newNote.rating > 0 ? newNote.rating : null,
      };
      await apiClient.post(`/recruiter-workspace/notes`, payload);
      setIsAdding(false);
      setNewNote({ title: "", note_type: "General", content: "", visibility: "Team", rating: 0 });
      fetchNotes();
    } catch (e) {
      console.error("Failed to save note", e);
    }
  };

  return (
    <Card className="flex flex-col h-full border-border/50">
      <CardHeader className="pb-3 border-b bg-muted/20">
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center text-lg">
            <MessageSquare className="mr-2 h-5 w-5 text-primary" /> Recruiter Notes
          </CardTitle>
          <Button variant="outline" size="sm" onClick={() => setIsAdding(!isAdding)}>
            {isAdding ? <X className="h-4 w-4 mr-1" /> : <Plus className="h-4 w-4 mr-1" />}
            {isAdding ? "Cancel" : "Add Note"}
          </Button>
        </div>
      </CardHeader>
      <CardContent className="flex-1 p-4 overflow-y-auto space-y-4">
        {isAdding && (
          <div className="bg-muted/30 p-3 rounded-lg border border-primary/20 space-y-3 mb-4">
            <div className="flex gap-2">
              <Input 
                placeholder="Title (Optional)" 
                value={newNote.title} 
                onChange={e => setNewNote({...newNote, title: e.target.value})} 
                className="flex-1 h-8 text-sm"
              />
              <Select value={newNote.note_type} onValueChange={(v: string | null) => setNewNote({...newNote, note_type: v || "General"})}>
                <SelectTrigger className="w-[130px] h-8 text-sm">
                  <SelectValue placeholder="Type" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="General">General</SelectItem>
                  <SelectItem value="Interview Feedback">Interview Feedback</SelectItem>
                  <SelectItem value="HR Feedback">HR Feedback</SelectItem>
                  <SelectItem value="Recommendation">Recommendation</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <Textarea 
              placeholder="Write your evaluation or notes here..." 
              value={newNote.content} 
              onChange={e => setNewNote({...newNote, content: e.target.value})}
              className="min-h-[80px] text-sm resize-none"
            />
            <div className="flex justify-between items-center">
              <div className="flex items-center gap-1">
                <span className="text-xs text-muted-foreground mr-1">Rating:</span>
                {[1,2,3,4,5].map(r => (
                  <Star 
                    key={r} 
                    className={`w-4 h-4 cursor-pointer ${newNote.rating >= r ? 'fill-amber-400 text-amber-400' : 'text-muted-foreground/30'}`}
                    onClick={() => setNewNote({...newNote, rating: r})}
                  />
                ))}
              </div>
              <Button size="sm" onClick={handleSave} className="h-8">
                <Save className="h-4 w-4 mr-1" /> Save
              </Button>
            </div>
          </div>
        )}

        {loading ? (
          <div className="flex justify-center p-4"><div className="animate-spin rounded-full h-5 w-5 border-b-2 border-primary"></div></div>
        ) : notes.length === 0 && !isAdding ? (
          <div className="text-center py-8 text-muted-foreground text-sm italic">
            No notes yet. Add your first evaluation note.
          </div>
        ) : (
          <div className="space-y-3">
            {notes.map(note => (
              <div key={note.id} className="bg-background border rounded-lg p-3 shadow-sm hover:border-primary/30 transition-colors">
                <div className="flex justify-between items-start mb-2">
                  <div>
                    <h4 className="font-semibold text-sm">{note.title || `${note.note_type} Note`}</h4>
                    <p className="text-[10px] text-muted-foreground">{new Date(note.created_at).toLocaleString()}</p>
                  </div>
                  <Badge variant="secondary" className="text-[10px]">{note.note_type}</Badge>
                </div>
                <p className="text-sm whitespace-pre-wrap">{note.content}</p>
                {note.rating && (
                  <div className="flex items-center gap-1 mt-2">
                    {[1,2,3,4,5].map(r => (
                      <Star key={r} className={`w-3 h-3 ${note.rating! >= r ? 'fill-amber-400 text-amber-400' : 'text-muted-foreground/20'}`} />
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
