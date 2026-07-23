"use client";

import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Mail, Lock, User, Phone, CheckCircle2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useSendOTP, useRegister } from "@/lib/hooks/useRegister";
import { useGoogleAuth } from "@/lib/hooks/useAuth";
import { useGoogleLogin } from "@react-oauth/google";

const registerSchema = z.object({
  full_name: z.string().min(2, "Full name is required"),
  email: z.string().email("Invalid email address"),
  mobile_number: z.string().min(10, "Invalid mobile number"),
  password: z.string().min(8, "Password must be at least 8 characters"),
  confirm_password: z.string(),
  otp_code: z.string().optional(),
  role: z.enum(["candidate", "recruiter"]),
}).refine((data) => data.password === data.confirm_password, {
  message: "Passwords do not match",
  path: ["confirm_password"],
});

type RegisterFormValues = z.infer<typeof registerSchema>;

export default function RegisterPage() {
  const router = useRouter();
  const [step, setStep] = useState<1 | 2>(1);
  const [serverError, setServerError] = useState("");
  
  const sendOTP = useSendOTP();
  const registerMutation = useRegister();

  const { register, handleSubmit, formState: { errors, isSubmitting }, watch } = useForm<RegisterFormValues>({
    resolver: zodResolver(registerSchema),
    defaultValues: {
      full_name: "",
      email: "",
      mobile_number: "",
      password: "",
      confirm_password: "",
      otp_code: "",
      role: "candidate",
    }
  });

  const email = watch("email");
  const role = watch("role");

  const googleAuthMutation = useGoogleAuth();
  
  const handleGoogleLogin = useGoogleLogin({
    flow: 'auth-code',
    onSuccess: async (tokenResponse) => {
      try {
        const data = await googleAuthMutation.mutateAsync(tokenResponse.code);
        if (data.needs_completion) {
          // Just redirect to login page where the modal will appear
          router.push("/login?complete_profile=true");
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
        setServerError(error.response?.data?.detail || error.message || "Google login failed.");
      }
    },
    onError: () => setServerError("Google login failed."),
  });

  const handleSendOTP = async (e: React.MouseEvent) => {
    e.preventDefault();
    setServerError("");
    // Basic validation before sending OTP
    if (!email) {
      setServerError("Please enter your email first.");
      return;
    }
    try {
      await sendOTP.mutateAsync({ target: email, role: role, method: "email", intent: "register" });
      setStep(2);
    } catch (error: any) {
      setServerError(error.response?.data?.detail || "Failed to send OTP. Please try again.");
    }
  };

  const onSubmit = async (data: RegisterFormValues) => {
    setServerError("");
    if (step === 1) {
      return; // We need to send OTP first
    }
    if (!data.otp_code) {
      setServerError("OTP Code is required");
      return;
    }
    try {
      const response = await registerMutation.mutateAsync({
        full_name: data.full_name,
        email: data.email,
        mobile_number: data.mobile_number,
        password: data.password,
        confirm_password: data.confirm_password,
        otp_code: data.otp_code,
        role: data.role,
      });
      
      // Store tokens
      if (typeof window !== "undefined") {
        localStorage.setItem("access_token", response.access_token);
        localStorage.setItem("user_role", response.user.role);
      }
      
      // Redirect to dashboard
      if (response.user.role === "recruiter") {
        const recruiterUrl = process.env.NEXT_PUBLIC_RECRUITER_URL || "http://localhost:3000";
        window.location.href = `${recruiterUrl}/login?token=${response.access_token}&role=recruiter`;
      } else {
        router.push("/");
      }
    } catch (error: any) {
      setServerError(error.response?.data?.detail || "Registration failed. Please try again.");
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-background/50 relative overflow-hidden">
      {/* Dynamic Background Elements */}
      <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] bg-primary/20 blur-[120px] rounded-full animate-pulse pointer-events-none" />
      <div className="absolute bottom-[-10%] right-[-10%] w-[30%] h-[30%] bg-blue-500/20 blur-[100px] rounded-full animate-pulse delay-1000 pointer-events-none" />

      <div className="w-full max-w-[440px] px-6 py-8 relative z-10">
        <div className="text-center mb-8">
          <div className="flex items-center justify-center gap-2 mb-2">
            <div className="w-8 h-8 rounded-lg bg-primary flex items-center justify-center">
              <span className="text-primary-foreground font-bold text-xl">A</span>
            </div>
            <span className="text-2xl font-bold tracking-tight">AIHire</span>
          </div>
          <h1 className="text-2xl font-semibold tracking-tight">Create an account</h1>
          <p className="text-sm text-muted-foreground mt-2">
            Join thousands of candidates finding their dream jobs
          </p>
        </div>

        <div className="bg-card border border-border/50 rounded-2xl shadow-xl shadow-black/5 p-8 backdrop-blur-sm">
          {serverError && (
            <div className="mb-6 p-3 rounded-lg bg-destructive/10 border border-destructive/20 text-destructive text-sm flex items-start gap-2">
              <span>{serverError}</span>
            </div>
          )}

          <form suppressHydrationWarning onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            
            <div className="space-y-4" style={{ display: step === 1 ? "block" : "none" }}>
              <div className="flex flex-col gap-3">
                <Button 
                  suppressHydrationWarning 
                  type="button" 
                  variant="outline" 
                  className="w-full h-11 bg-background/50 border-muted-foreground/20 hover:bg-muted/50"
                  onClick={(e) => { e.preventDefault(); handleGoogleLogin(); }}
                >
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

              <div className="flex gap-4 p-1 bg-muted/50 rounded-lg">
                <label className={`flex-1 flex items-center justify-center py-2 rounded-md cursor-pointer transition-colors ${role === "candidate" ? "bg-primary text-primary-foreground shadow-sm" : "hover:bg-muted"}`}>
                  <input type="radio" value="candidate" {...register("role")} className="hidden" />
                  <span className="text-sm font-medium">Candidate</span>
                </label>
                <label className={`flex-1 flex items-center justify-center py-2 rounded-md cursor-pointer transition-colors ${role === "recruiter" ? "bg-primary text-primary-foreground shadow-sm" : "hover:bg-muted"}`}>
                  <input type="radio" value="recruiter" {...register("role")} className="hidden" />
                  <span className="text-sm font-medium">Recruiter</span>
                </label>
              </div>

              <div className="space-y-1">
                <div className="relative">
                  <User className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                  <Input 
                    {...register("full_name")}
                    placeholder="Full Name" 
                    className="bg-background/50 h-11 pl-10"
                  />
                </div>
                {errors.full_name && <p className="text-xs text-destructive">{errors.full_name.message}</p>}
              </div>

              <div className="space-y-1">
                <div className="relative">
                  <Mail className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                  <Input 
                    {...register("email")}
                    type="email" 
                    placeholder="Email Address" 
                    className="bg-background/50 h-11 pl-10"
                  />
                </div>
                {errors.email && <p className="text-xs text-destructive">{errors.email.message}</p>}
              </div>

              <div className="space-y-1">
                <div className="relative">
                  <Phone className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                  <Input 
                    {...register("mobile_number")}
                    placeholder="Mobile Number" 
                    className="bg-background/50 h-11 pl-10"
                  />
                </div>
                {errors.mobile_number && <p className="text-xs text-destructive">{errors.mobile_number.message}</p>}
              </div>

              <div className="space-y-1">
                <div className="relative">
                  <Lock className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                  <Input 
                    {...register("password")}
                    type="password" 
                    placeholder="Password" 
                    className="bg-background/50 h-11 pl-10"
                  />
                </div>
                {errors.password && <p className="text-xs text-destructive">{errors.password.message}</p>}
              </div>

              <div className="space-y-1">
                <div className="relative">
                  <Lock className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                  <Input 
                    {...register("confirm_password")}
                    type="password" 
                    placeholder="Confirm Password" 
                    className="bg-background/50 h-11 pl-10"
                  />
                </div>
                {errors.confirm_password && <p className="text-xs text-destructive">{errors.confirm_password.message}</p>}
              </div>

              <Button 
                onClick={handleSendOTP}
                disabled={sendOTP.isPending}
                className="w-full h-11 text-base font-medium transition-all shadow-lg hover:shadow-primary/25"
              >
                {sendOTP.isPending ? "Sending OTP..." : "Continue"}
              </Button>
            </div>

            <div className="space-y-4" style={{ display: step === 2 ? "block" : "none" }}>
              <div className="text-center mb-4">
                <div className="inline-flex items-center justify-center w-12 h-12 rounded-full bg-primary/10 mb-2">
                  <CheckCircle2 className="w-6 h-6 text-primary" />
                </div>
                <h3 className="font-medium text-lg">Verify your email</h3>
                <p className="text-sm text-muted-foreground mt-1">
                  We've sent a code to <span className="font-medium text-foreground">{email}</span>
                </p>
              </div>

              <div className="space-y-1">
                <Input 
                  {...register("otp_code")}
                  placeholder="Enter 6-digit OTP" 
                  className="bg-background/50 h-11 text-center text-lg tracking-widest font-medium"
                  maxLength={6}
                />
                {errors.otp_code && <p className="text-xs text-destructive text-center">{errors.otp_code.message}</p>}
              </div>

              <Button 
                type="submit"
                disabled={registerMutation.isPending}
                className="w-full h-11 text-base font-medium transition-all shadow-lg hover:shadow-primary/25"
              >
                {registerMutation.isPending ? "Creating Account..." : "Create Account"}
              </Button>

              <div className="text-center">
                <button 
                  type="button" 
                  onClick={() => setStep(1)} 
                  className="text-sm text-muted-foreground hover:text-primary transition-colors"
                >
                  Back to edit details
                </button>
              </div>
            </div>

          </form>

          <div className="mt-6 text-center text-sm text-muted-foreground">
            Already have an account?{" "}
            <Link href="/login" className="font-medium text-primary hover:underline">
              Sign in
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
