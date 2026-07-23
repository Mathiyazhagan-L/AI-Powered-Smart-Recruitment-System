"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Briefcase, Building2, ArrowRight, User } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { cn } from "@/lib/utils";

type Role = "candidate" | "recruiter";

export default function UnifiedSignup() {
  const router = useRouter();
  const [isLoading, setIsLoading] = useState(false);
  const [role, setRole] = useState<Role>("candidate");

  const handleSignup = (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    
    // Simulate signup process
    setTimeout(() => {
      setIsLoading(false);
      // After signup, we route them to the login page so they can experience the flow!
      router.push("/login");
    }, 1500);
  };

  return (
    <div className="min-h-screen w-full flex relative overflow-hidden bg-background">
      {/* Dynamic Background Mesh based on role */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none transition-colors duration-700">
        <div className={cn(
          "absolute top-[-10%] right-[-10%] w-[50%] h-[50%] rounded-full blur-[120px] mix-blend-screen transition-all duration-700",
          role === "candidate" ? "bg-blue-500/20" : "bg-primary/20 left-[-10%] right-auto"
        )} />
        <div className={cn(
          "absolute bottom-[-10%] left-[-10%] w-[50%] h-[50%] rounded-full blur-[120px] mix-blend-screen transition-all duration-700",
          role === "candidate" ? "bg-primary/20" : "bg-blue-500/20 right-[-10%] left-auto"
        )} />
      </div>

      <div className="flex-1 flex flex-col justify-center items-center p-6 relative z-10 w-full max-w-2xl mx-auto">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="w-full"
        >
          <div className="flex items-center justify-center gap-2 mb-8">
            <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-primary shadow-lg shadow-primary/20">
              <Briefcase className="h-6 w-6 text-primary-foreground" />
            </div>
            <span className="text-3xl font-bold tracking-tight">AIHire</span>
          </div>

          <Card className="border-muted/50 bg-background/60 backdrop-blur-xl shadow-2xl overflow-hidden">
            <CardHeader className="space-y-1 text-center pb-6">
              <CardTitle className="text-2xl font-semibold tracking-tight">Create your account</CardTitle>
              <CardDescription className="text-muted-foreground">
                Join the platform that connects top talent with elite companies.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              
              {/* Role Selection Toggle */}
              <div className="space-y-3">
                <Label>I am a...</Label>
                <div className="grid grid-cols-2 gap-4">
                  <button
                    type="button"
                    onClick={() => setRole("candidate")}
                    className={cn(
                      "relative flex flex-col items-center justify-center p-4 border rounded-xl transition-all duration-200 outline-none",
                      role === "candidate" 
                        ? "border-primary bg-primary/5 text-primary shadow-sm shadow-primary/10" 
                        : "border-muted-foreground/20 hover:border-muted-foreground/40 text-muted-foreground hover:bg-muted/30"
                    )}
                  >
                    <User className="h-6 w-6 mb-2" />
                    <span className="font-semibold">Candidate</span>
                    <span className="text-xs mt-1 opacity-70">Looking for jobs</span>
                  </button>

                  <button
                    type="button"
                    onClick={() => setRole("recruiter")}
                    className={cn(
                      "relative flex flex-col items-center justify-center p-4 border rounded-xl transition-all duration-200 outline-none",
                      role === "recruiter" 
                        ? "border-primary bg-primary/5 text-primary shadow-sm shadow-primary/10" 
                        : "border-muted-foreground/20 hover:border-muted-foreground/40 text-muted-foreground hover:bg-muted/30"
                    )}
                  >
                    <Building2 className="h-6 w-6 mb-2" />
                    <span className="font-semibold">Recruiter</span>
                    <span className="text-xs mt-1 opacity-70">Hiring talent</span>
                  </button>
                </div>
              </div>

              <AnimatePresence mode="wait">
                <motion.form 
                  key={role}
                  initial={{ opacity: 0, x: 20 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: -20 }}
                  transition={{ duration: 0.2 }}
                  onSubmit={handleSignup} 
                  className="space-y-4"
                >
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label htmlFor="firstName">First Name</Label>
                      <Input id="firstName" placeholder="John" required className="bg-background/50" />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="lastName">Last Name</Label>
                      <Input id="lastName" placeholder="Doe" required className="bg-background/50" />
                    </div>
                  </div>
                  
                  <div className="space-y-2">
                    <Label htmlFor="email">Email Address</Label>
                    <Input 
                      id="email" 
                      type="email" 
                      placeholder={role === "recruiter" ? "name@company.com" : "name@example.com"} 
                      required 
                      className="bg-background/50"
                    />
                  </div>
                  
                  {role === "recruiter" && (
                    <div className="space-y-2">
                      <Label htmlFor="company">Company Name</Label>
                      <Input id="company" placeholder="Acme Inc." required className="bg-background/50" />
                    </div>
                  )}

                  <div className="space-y-2">
                    <Label htmlFor="password">Password</Label>
                    <Input id="password" type="password" required className="bg-background/50" />
                  </div>

                  <Button 
                    type="submit" 
                    className="w-full h-11 mt-2 text-base font-medium transition-all" 
                    disabled={isLoading}
                  >
                    {isLoading ? "Creating account..." : `Join as a ${role === "recruiter" ? "Recruiter" : "Candidate"}`}
                    {!isLoading && <ArrowRight className="ml-2 h-4 w-4" />}
                  </Button>
                </motion.form>
              </AnimatePresence>

            </CardContent>
            <CardFooter className="flex justify-center border-t border-muted/50 p-4 bg-muted/10">
              <p className="text-sm text-muted-foreground">
                Already have an account?{" "}
                <button 
                  onClick={() => router.push('/login')} 
                  className="font-medium text-primary hover:underline outline-none"
                >
                  Sign in here
                </button>
              </p>
            </CardFooter>
          </Card>
        </motion.div>
      </div>
    </div>
  );
}
