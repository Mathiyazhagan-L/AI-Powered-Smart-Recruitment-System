"use client";

import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Building, MapPin, DollarSign, Download, CheckCircle2, XCircle, FileText, Calendar } from "lucide-react";
import { useCandidateOffers, useAcceptOffer, useRejectOffer, CandidateOffer } from "@/lib/hooks/useOffers";

export default function OffersPage() {
  const { data: offers, isLoading } = useCandidateOffers();
  const acceptOffer = useAcceptOffer();
  const rejectOffer = useRejectOffer();

  const activeOffers = offers || [];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight text-foreground">Offers</h1>
        <p className="text-muted-foreground mt-2">Review your pending job offers and past acceptances.</p>
      </div>

      <div className="mt-8 space-y-6">
        {isLoading ? (
          <Card className="flex flex-col items-center justify-center p-12 text-center border-dashed">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mb-2"></div>
            <p className="text-muted-foreground">Loading your offers...</p>
          </Card>
        ) : activeOffers.length === 0 ? (
          <Card className="flex flex-col items-center justify-center p-12 text-center border-dashed">
            <div className="h-16 w-16 rounded-full bg-muted flex items-center justify-center mb-4">
              <CheckCircle2 className="h-8 w-8 text-muted-foreground" />
            </div>
            <CardTitle className="text-xl mb-2">No Offers Yet</CardTitle>
            <CardDescription className="text-base max-w-md">
              You don't have any pending or past job offers at the moment. Keep applying and interviewing!
            </CardDescription>
          </Card>
        ) : (
          activeOffers.map((offer: CandidateOffer) => (
            <Card key={offer.id} className="overflow-hidden border-l-4 border-l-primary shadow-sm hover:shadow-md transition-shadow">
              <CardContent className="p-0">
                <div className="flex flex-col md:flex-row">
                  <div className="p-6 flex-1 flex flex-col justify-between">
                    <div>
                      <div className="flex justify-between items-start mb-4">
                        <div>
                          <h3 className="text-2xl font-bold">{offer.position_title}</h3>
                          <p className="text-lg text-muted-foreground flex items-center mt-1">
                            <Building className="mr-2 h-5 w-5" /> {offer.company_name}
                          </p>
                        </div>
                        <Badge 
                          variant="outline" 
                          className={`text-sm px-3 py-1 ${
                            offer.offer_status === "Accepted" ? "bg-success/10 text-success border-success/30" :
                            offer.offer_status === "Rejected" ? "bg-destructive/10 text-destructive border-destructive/30" :
                            "bg-blue-50 text-blue-700 border-blue-200"
                          }`}
                        >
                          {offer.offer_status}
                        </Badge>
                      </div>
                      
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-6">
                        <div className="bg-muted/50 p-3 rounded-lg">
                          <p className="text-xs text-muted-foreground mb-1 uppercase tracking-wider font-semibold">Package</p>
                          <p className="font-semibold text-lg flex items-center"><DollarSign className="h-4 w-4 mr-0.5 text-muted-foreground" />{Number(offer.package_amount || 0).toLocaleString()}</p>
                        </div>
                        <div className="bg-muted/50 p-3 rounded-lg">
                          <p className="text-xs text-muted-foreground mb-1 uppercase tracking-wider font-semibold">Location</p>
                          <p className="font-semibold text-sm flex items-center mt-1"><MapPin className="h-4 w-4 mr-1 text-muted-foreground" />{offer.location}</p>
                        </div>
                        <div className="bg-muted/50 p-3 rounded-lg">
                          <p className="text-xs text-muted-foreground mb-1 uppercase tracking-wider font-semibold">Expires</p>
                          <p className="font-semibold text-sm flex items-center mt-1"><Calendar className="h-4 w-4 mr-1 text-muted-foreground" />{offer.offer_expiry_date?.substring(0, 10)}</p>
                        </div>
                        <div className="bg-muted/50 p-3 rounded-lg">
                          <p className="text-xs text-muted-foreground mb-1 uppercase tracking-wider font-semibold">Equity</p>
                          <p className="font-semibold text-sm flex items-center mt-1">{offer.equity_percentage}%</p>
                        </div>
                      </div>
                    </div>
                  </div>
                  
                  <div className="bg-muted/30 p-6 md:w-64 border-t md:border-t-0 md:border-l flex flex-col justify-center space-y-3">
                    {offer.offer_pdf_path && (
                      <Button variant="outline" className="w-full justify-start" onClick={() => window.open(`http://localhost:8000/offers/${offer.id}/download`, "_blank")}>
                        <FileText className="mr-2 h-4 w-4" /> View Offer Letter
                      </Button>
                    )}
                    
                    {(offer.offer_status === "Sent" || offer.offer_status === "Generated") && (
                      <>
                        <Button 
                          className="w-full justify-start bg-success hover:bg-success/90 text-success-foreground"
                          onClick={() => acceptOffer.mutate(offer.id)}
                          disabled={acceptOffer.isPending}
                        >
                          <CheckCircle2 className="mr-2 h-4 w-4" /> Accept Offer
                        </Button>
                        <Button 
                          variant="outline"
                          className="w-full justify-start text-destructive hover:bg-destructive/10 hover:text-destructive"
                          onClick={() => rejectOffer.mutate(offer.id)}
                          disabled={rejectOffer.isPending}
                        >
                          <XCircle className="mr-2 h-4 w-4" /> Decline
                        </Button>
                      </>
                    )}
                  </div>
                </div>
              </CardContent>
            </Card>
          ))
        )}
      </div>
    </div>
  );
}
