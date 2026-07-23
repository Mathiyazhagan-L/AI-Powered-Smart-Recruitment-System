"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import Image from "next/image";
import Link from "next/link";
import { useLogin, useGoogleAuth } from "@/lib/hooks/useAuth";
import { useGoogleLogin } from "@react-oauth/google";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from "@/components/ui/dialog";
import { Briefcase, ArrowRight, Eye, EyeOff } from "lucide-react";
import { motion } from "framer-motion";

export default function CandidateLogin() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");
  
  const [needsCompletion, setNeedsCompletion] = useState(false);
  const [googlePayload, setGooglePayload] = useState<any>(null);
  
  const [mobileNumber, setMobileNumber] = useState("");
  const [role, setRole] = useState("candidate"); // Default to candidate since we're in candidate app
  
  const handleCompleteGoogle = async () => {
    try {
      const response = await fetch("http://localhost:8000/auth/google/complete", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          google_id: googlePayload.google_id,
          email: googlePayload.email,
          full_name: googlePayload.full_name,
          mobile_number: mobileNumber,
          role: role,
        }),
      });
      
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || "Registration failed");
      
      localStorage.setItem("access_token", data.access_token);
      localStorage.setItem("user_role", data.user.role);
      
      if (data.user.role === "company" || data.user.role === "recruiter") {
        const recruiterUrl = process.env.NEXT_PUBLIC_RECRUITER_URL || "http://localhost:3000";
        window.location.href = `${recruiterUrl}/login?token=${data.access_token}&role=${data.user.role}`;
      } else {
        router.push("/");
      }
    } catch (error: any) {
      setErrorMessage(error.message || "Failed to complete registration");
    }
  };

  const loginMutation = useLogin();
  const googleAuthMutation = useGoogleAuth();

  const handleGoogleLogin = useGoogleLogin({
    flow: 'auth-code',
    select_account: true,
    onSuccess: async (tokenResponse) => {
      try {
        const data = await googleAuthMutation.mutateAsync(tokenResponse.code);
        if (data.needs_completion) {
          setGooglePayload(data);
          setNeedsCompletion(true);
        } else {
          const userRole = data.user?.role?.toLowerCase() || "";
          if (userRole === "company" || userRole === "recruiter") {
            const recruiterUrl = process.env.NEXT_PUBLIC_RECRUITER_URL || "http://localhost:3000";
            window.location.href = `${recruiterUrl}/login?token=${data.access_token}&role=${userRole}`;
          } else {
            router.push("/");
          }
        }
      } catch (error: any) {
        setErrorMessage(error.response?.data?.detail || error.message || "Google login failed. Please try again.");
      }
    },
    onError: () => setErrorMessage("Google login failed."),
  });
  useEffect(() => {
    if (typeof window !== "undefined") {
      const urlParams = new URLSearchParams(window.location.search);
      const token = urlParams.get("token");
      const role = urlParams.get("role");
      if (token) {
        localStorage.setItem("access_token", token);
        if (role) localStorage.setItem("user_role", role);
        router.push("/");
      }
    }
  }, [router]);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage("");
    
    try {
      const data = await loginMutation.mutateAsync({ email, password });
      
      // Redirect based on role
      const userRole = data.user.role?.toLowerCase() || "";
      if (userRole === "company" || userRole === "recruiter") {
        const recruiterUrl = process.env.NEXT_PUBLIC_RECRUITER_URL || "http://localhost:3000";
        window.location.href = `${recruiterUrl}/login?token=${data.access_token}&role=${userRole}`;
      } else {
        router.push("/");
      }
    } catch (error: any) {
      setErrorMessage(error.response?.data?.detail || "Invalid credentials. Please try again.");
    }
  };

  return (
    <div className="min-h-screen w-full flex relative overflow-hidden bg-background">
      {/* Dynamic Background Mesh */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-[-10%] right-[-10%] w-[50%] h-[50%] rounded-full bg-blue-500/20 blur-[120px] mix-blend-screen" />
        <div className="absolute bottom-[-10%] left-[-10%] w-[50%] h-[50%] rounded-full bg-primary/20 blur-[120px] mix-blend-screen" />
      </div>

      {/* Decorative Side Panel for Candidate */}
      <div className="hidden lg:flex flex-1 bg-muted/10 items-center justify-center p-12 relative overflow-hidden border-r border-muted/20">
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,_var(--tw-gradient-stops))] from-primary/10 via-background to-background" />
        
        {/* Animated Background Orbs */}
        <motion.div 
          className="absolute top-1/4 left-1/4 w-64 h-64 bg-primary/20 rounded-full blur-[100px] pointer-events-none"
          animate={{ 
            x: [0, 50, 0], 
            y: [0, 30, 0],
            scale: [1, 1.2, 1]
          }}
          transition={{ duration: 8, repeat: Infinity, ease: "easeInOut" }}
        />
        <motion.div 
          className="absolute bottom-1/4 right-1/4 w-80 h-80 bg-blue-500/20 rounded-full blur-[120px] pointer-events-none"
          animate={{ 
            x: [0, -40, 0], 
            y: [0, -50, 0],
            scale: [1, 1.5, 1]
          }}
          transition={{ duration: 10, repeat: Infinity, ease: "easeInOut", delay: 1 }}
        />
        
        <div className="relative z-10 flex flex-col items-center text-center space-y-6 max-w-md">
          {/* Centered Brand Logo and Name */}
          <div className="flex flex-col items-center space-y-4">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6 }}
            >
              <motion.div
                animate={{ y: [0, -10, 0] }}
                transition={{ duration: 4, repeat: Infinity, ease: "easeInOut" }}
              >
                <Image src="/logo.png" alt="AIHire Logo" width={120} height={120} className="w-auto h-28 object-contain drop-shadow-xl" />
              </motion.div>
            </motion.div>
            
            <motion.h1 
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.2 }}
              className="text-5xl font-extrabold tracking-tight text-foreground uppercase"
            >
              AI HIRE
            </motion.h1>
            
            <motion.p 
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.4 }}
              className="text-xl text-muted-foreground font-medium tracking-wide"
            >
              Connecting talent to tomorrow
            </motion.p>
          </div>
        </div>
      </div>

      <div className="flex-1 flex flex-col justify-center items-center p-6 relative z-10">
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.5 }}
          className="w-full max-w-md"
        >
          <div className="flex items-center justify-center gap-2 mb-8 lg:hidden">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-primary shadow-lg shadow-primary/20">
              <Briefcase className="h-5 w-5 text-primary-foreground" />
            </div>
            <span className="text-2xl font-bold tracking-tight">AIHire</span>
          </div>

          <Dialog open={needsCompletion} onOpenChange={(open) => !open && setNeedsCompletion(false)}>
            <DialogContent className="sm:max-w-md">
              <DialogHeader>
                <DialogTitle>Complete Your Profile</DialogTitle>
                <DialogDescription>
                  Welcome {googlePayload?.full_name}! You haven't registered yet. Please complete the registration below to sign up and log in.
                </DialogDescription>
              </DialogHeader>
              <div className="space-y-4 py-4">
                <div className="space-y-2">
                  <Label>I am a</Label>
                  <select
                    value={role}
                    onChange={(e) => setRole(e.target.value)}
                    className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                  >
                    <option value="candidate">Candidate</option>
                    <option value="recruiter">Recruiter</option>
                  </select>
                </div>
                <div className="space-y-2">
                  <Label>Mobile Number</Label>
                  <Input 
                    value={mobileNumber} 
                    onChange={(e) => setMobileNumber(e.target.value)} 
                    placeholder="+1 234 567 8900" 
                    required 
                  />
                </div>
                <Button onClick={handleCompleteGoogle} className="w-full">
                  Complete Registration
                </Button>
              </div>
            </DialogContent>
          </Dialog>

          <Card className="border-muted/50 bg-background/60 backdrop-blur-xl shadow-2xl">
            <CardHeader className="space-y-1 text-center pb-6">
              <div className="hidden lg:flex justify-center mb-4">
                <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-primary shadow-lg shadow-primary/20">
                  <Briefcase className="h-6 w-6 text-primary-foreground" />
                </div>
              </div>
              <CardTitle className="text-2xl font-semibold tracking-tight">Welcome back</CardTitle>
              <CardDescription className="text-muted-foreground">
                Sign in to view your applications and offers
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex flex-col gap-3">
                <Button suppressHydrationWarning variant="outline" className="w-full h-11 bg-background/50 border-muted-foreground/20 hover:bg-muted/50" onClick={() => handleGoogleLogin()}>
                  <svg className="mr-2 h-5 w-5" viewBox="0 0 24 24">
                    <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4"/>
                    <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/>
                    <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05"/>
                    <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/>
                  </svg>
                  Continue with Google
                </Button>
              </div>

              <div className="relative my-6">
                <div className="absolute inset-0 flex items-center">
                  <div className="w-full border-t border-muted-foreground/20" />
                </div>
                <div className="relative flex justify-center text-xs uppercase">
                  <span className="bg-background/60 px-2 text-muted-foreground backdrop-blur-xl">Or continue with email</span>
                </div>
              </div>

              <form suppressHydrationWarning onSubmit={handleLogin} className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="email">Email</Label>
                  <Input 
                    suppressHydrationWarning
                    id="email" 
                    type="email" 
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="name@example.com" 
                    required 
                    className="bg-background/50 border-muted-foreground/20 focus-visible:ring-primary h-11"
                  />
                </div>
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <Label htmlFor="password">Password</Label>
                    <Link href="/forgot-password" className="text-xs font-medium text-primary hover:underline">Forgot password?</Link>
                  </div>
                  <div className="relative">
                    <Input 
                      suppressHydrationWarning
                      id="password" 
                      type={showPassword ? "text" : "password"} 
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      required 
                      className="bg-background/50 border-muted-foreground/20 focus-visible:ring-primary h-11 pr-10"
                    />
                    <button
                      suppressHydrationWarning
                      type="button"
                      onClick={() => setShowPassword(!showPassword)}
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground focus:outline-none transition-colors"
                      aria-label={showPassword ? "Hide password" : "Show password"}
                    >
                      {showPassword ? (
                        <EyeOff className="h-4 w-4" />
                      ) : (
                        <Eye className="h-4 w-4" />
                      )}
                    </button>
                  </div>
                </div>
                
                {errorMessage && (
                  <div className="text-sm text-red-500 font-medium">{errorMessage}</div>
                )}
                
                <Button 
                  suppressHydrationWarning
                  type="submit" 
                  className="w-full h-11 text-base font-medium transition-all" 
                  disabled={loginMutation.isPending}
                >
                  {loginMutation.isPending ? "Signing in..." : "Sign in to AIHire"}
                  {!loginMutation.isPending && <ArrowRight className="ml-2 h-4 w-4" />}
                </Button>
              </form>
            </CardContent>
            <CardFooter className="flex justify-center border-t border-muted/50 p-4">
              <p className="text-sm text-muted-foreground">
                Don't have an account? <Link href="/register" className="font-medium text-primary hover:underline">Sign up for free</Link>
              </p>
            </CardFooter>
          </Card>
        </motion.div>
      </div>
    </div>
  );
}
