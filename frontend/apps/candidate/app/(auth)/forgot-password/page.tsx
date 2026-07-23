"use client";

import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Mail, Lock, CheckCircle2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useForgotPassword, useResetPassword } from "@/lib/hooks/useRegister";

const forgotSchema = z.object({
  email: z.string().email("Invalid email address"),
  otp_code: z.string().optional(),
  new_password: z.string().optional(),
  confirm_password: z.string().optional(),
});

type ForgotFormValues = z.infer<typeof forgotSchema>;

export default function ForgotPasswordPage() {
  const router = useRouter();
  const [step, setStep] = useState<1 | 2>(1);
  const [serverError, setServerError] = useState("");
  const [successMessage, setSuccessMessage] = useState("");
  
  const forgotMutation = useForgotPassword();
  const resetMutation = useResetPassword();

  const { register, handleSubmit, formState: { errors }, watch } = useForm<ForgotFormValues>({
    resolver: zodResolver(forgotSchema as any),
    defaultValues: {
      email: "",
      otp_code: "",
      new_password: "",
      confirm_password: "",
    }
  });

  const email = watch("email");

  const handleSendOTP = async (data: ForgotFormValues) => {
    setServerError("");
    try {
      await forgotMutation.mutateAsync({ email: data.email });
      setStep(2);
    } catch (error: any) {
      setServerError(error.response?.data?.detail || "Failed to send reset code. Please try again.");
    }
  };

  const handleResetPassword = async (data: ForgotFormValues) => {
    setServerError("");
    if (!data.otp_code || !data.new_password || !data.confirm_password) {
      setServerError("Please fill in all fields.");
      return;
    }
    if (data.new_password !== data.confirm_password) {
      setServerError("Passwords do not match.");
      return;
    }
    
    try {
      const response = await resetMutation.mutateAsync({
        email: data.email,
        otp_code: data.otp_code,
        new_password: data.new_password,
        confirm_password: data.confirm_password,
      });
      setSuccessMessage("Password reset successfully. You can now sign in.");
      setTimeout(() => router.push("/login"), 2000);
    } catch (error: any) {
      setServerError(error.response?.data?.detail || "Failed to reset password. Please try again.");
    }
  };

  const onSubmit = (data: ForgotFormValues) => {
    if (step === 1) {
      handleSendOTP(data);
    } else {
      handleResetPassword(data);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-background/50 relative overflow-hidden">
      <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] bg-primary/20 blur-[120px] rounded-full animate-pulse pointer-events-none" />
      
      <div className="w-full max-w-[440px] px-6 py-8 relative z-10">
        <div className="text-center mb-8">
          <h1 className="text-2xl font-semibold tracking-tight">Forgot Password</h1>
          <p className="text-sm text-muted-foreground mt-2">
            Enter your email to receive a password reset code
          </p>
        </div>

        <div className="bg-card border border-border/50 rounded-2xl shadow-xl shadow-black/5 p-8 backdrop-blur-sm">
          {serverError && (
            <div className="mb-6 p-3 rounded-lg bg-destructive/10 border border-destructive/20 text-destructive text-sm flex items-start gap-2">
              <span>{serverError}</span>
            </div>
          )}
          {successMessage && (
            <div className="mb-6 p-3 rounded-lg bg-green-500/10 border border-green-500/20 text-green-500 text-sm flex items-start gap-2">
              <span>{successMessage}</span>
            </div>
          )}

          <form suppressHydrationWarning onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            
            <div className="space-y-4" style={{ display: step === 1 ? "block" : "none" }}>
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

              <Button 
                type="submit"
                disabled={forgotMutation.isPending}
                className="w-full h-11 text-base font-medium transition-all shadow-lg hover:shadow-primary/25"
              >
                {forgotMutation.isPending ? "Sending code..." : "Send Reset Code"}
              </Button>
            </div>

            <div className="space-y-4" style={{ display: step === 2 ? "block" : "none" }}>
              <div className="text-center mb-4">
                <div className="inline-flex items-center justify-center w-12 h-12 rounded-full bg-primary/10 mb-2">
                  <CheckCircle2 className="w-6 h-6 text-primary" />
                </div>
                <p className="text-sm text-muted-foreground mt-1">
                  Code sent to <span className="font-medium text-foreground">{email}</span>
                </p>
              </div>

              <div className="space-y-1">
                <Input 
                  {...register("otp_code")}
                  placeholder="Enter 6-digit OTP" 
                  className="bg-background/50 h-11 text-center tracking-widest font-medium"
                  maxLength={6}
                />
              </div>

              <div className="space-y-1">
                <div className="relative">
                  <Lock className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                  <Input 
                    {...register("new_password")}
                    type="password" 
                    placeholder="New Password" 
                    className="bg-background/50 h-11 pl-10"
                  />
                </div>
              </div>

              <div className="space-y-1">
                <div className="relative">
                  <Lock className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                  <Input 
                    {...register("confirm_password")}
                    type="password" 
                    placeholder="Confirm New Password" 
                    className="bg-background/50 h-11 pl-10"
                  />
                </div>
              </div>

              <Button 
                type="submit"
                disabled={resetMutation.isPending}
                className="w-full h-11 text-base font-medium transition-all shadow-lg hover:shadow-primary/25"
              >
                {resetMutation.isPending ? "Resetting..." : "Reset Password"}
              </Button>

              <div className="text-center">
                <button 
                  type="button" 
                  onClick={() => setStep(1)} 
                  className="text-sm text-muted-foreground hover:text-primary transition-colors"
                >
                  Back to enter email
                </button>
              </div>
            </div>

          </form>

          <div className="mt-6 text-center text-sm text-muted-foreground">
            Remember your password?{" "}
            <Link href="/login" className="font-medium text-primary hover:underline">
              Sign in
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
