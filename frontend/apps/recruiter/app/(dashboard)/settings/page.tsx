"use client";

import { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Separator } from "@/components/ui/separator";
import { Switch } from "@/components/ui/switch";
import { Badge } from "@/components/ui/badge";
import { useUser, useLogout } from "@/lib/hooks/useAuth";
import { useRouter } from "next/navigation";
import { User, Lock, Bell, Shield, LogOut, Check } from "lucide-react";
import { apiClient } from "@/lib/apiClient";

export default function SettingsPage() {
  const router = useRouter();
  const { data: user } = useUser();
  const logout = useLogout();
  const [emailNotifs, setEmailNotifs] = useState(true);
  const [candidateAlerts, setCandidateAlerts] = useState(true);
  const [assessmentAlerts, setAssessmentAlerts] = useState(true);
  const [passwordData, setPasswordData] = useState({ current: "", newPass: "", confirm: "" });
  const [passwordStatus, setPasswordStatus] = useState<"idle" | "loading" | "success" | "error">("idle");
  const [passwordError, setPasswordError] = useState("");

  const handleLogout = () => {
    logout();
    router.push("/login");
  };

  const handleChangePassword = async () => {
    if (!passwordData.newPass || !passwordData.confirm) {
      setPasswordError("All fields are required.");
      return;
    }
    if (passwordData.newPass !== passwordData.confirm) {
      setPasswordError("Passwords do not match.");
      return;
    }
    if (passwordData.newPass.length < 8) {
      setPasswordError("Password must be at least 8 characters.");
      return;
    }
    setPasswordError("");
    setPasswordStatus("loading");
    try {
      await apiClient.post("/auth/change-password", {
        current_password: passwordData.current,
        new_password: passwordData.newPass,
      });
      setPasswordStatus("success");
      setPasswordData({ current: "", newPass: "", confirm: "" });
    } catch (err: any) {
      setPasswordStatus("error");
      setPasswordError(err?.response?.data?.detail || "Failed to change password. Check your current password.");
    }
  };

  return (
    <div className="space-y-6 max-w-3xl">
      <div>
        <h2 className="text-3xl font-bold tracking-tight text-foreground">Settings</h2>
        <p className="text-muted-foreground mt-2">Manage your account and preferences.</p>
      </div>

      {/* Account Info */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2"><User className="h-5 w-5" /> Account Information</CardTitle>
          <CardDescription>Your account details (read-only)</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label className="text-xs text-muted-foreground">Full Name</Label>
              <p className="font-medium mt-1">{user?.full_name || "—"}</p>
            </div>
            <div>
              <Label className="text-xs text-muted-foreground">Email</Label>
              <p className="font-medium mt-1">{user?.email || "—"}</p>
            </div>
            <div>
              <Label className="text-xs text-muted-foreground">Role</Label>
              <Badge variant="outline" className="mt-1 capitalize">{user?.role?.toLowerCase() || "recruiter"}</Badge>
            </div>
            <div>
              <Label className="text-xs text-muted-foreground">Account Status</Label>
              <Badge className="mt-1 bg-success text-success-foreground">Active</Badge>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Change Password */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2"><Lock className="h-5 w-5" /> Change Password</CardTitle>
          <CardDescription>Update your account password</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <Label htmlFor="current-pass">Current Password</Label>
            <Input
              id="current-pass"
              type="password"
              value={passwordData.current}
              onChange={e => setPasswordData(p => ({ ...p, current: e.target.value }))}
              className="mt-1"
            />
          </div>
          <div>
            <Label htmlFor="new-pass">New Password</Label>
            <Input
              id="new-pass"
              type="password"
              value={passwordData.newPass}
              onChange={e => setPasswordData(p => ({ ...p, newPass: e.target.value }))}
              className="mt-1"
            />
          </div>
          <div>
            <Label htmlFor="confirm-pass">Confirm New Password</Label>
            <Input
              id="confirm-pass"
              type="password"
              value={passwordData.confirm}
              onChange={e => setPasswordData(p => ({ ...p, confirm: e.target.value }))}
              className="mt-1"
            />
          </div>
          {passwordError && <p className="text-destructive text-sm">{passwordError}</p>}
          {passwordStatus === "success" && (
            <p className="text-success text-sm flex items-center gap-1"><Check className="h-4 w-4" /> Password changed successfully!</p>
          )}
          <Button
            onClick={handleChangePassword}
            disabled={passwordStatus === "loading"}
            className="bg-primary text-primary-foreground"
          >
            {passwordStatus === "loading" ? "Updating..." : "Update Password"}
          </Button>
        </CardContent>
      </Card>

      {/* Notification Preferences */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2"><Bell className="h-5 w-5" /> Notifications</CardTitle>
          <CardDescription>Control what alerts you receive</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="font-medium text-sm">Email Notifications</p>
              <p className="text-xs text-muted-foreground">Receive recruitment updates via email</p>
            </div>
            <Switch checked={emailNotifs} onCheckedChange={setEmailNotifs} />
          </div>
          <Separator />
          <div className="flex items-center justify-between">
            <div>
              <p className="font-medium text-sm">New Candidate Alerts</p>
              <p className="text-xs text-muted-foreground">Notify when a new candidate applies</p>
            </div>
            <Switch checked={candidateAlerts} onCheckedChange={setCandidateAlerts} />
          </div>
          <Separator />
          <div className="flex items-center justify-between">
            <div>
              <p className="font-medium text-sm">Assessment Completion Alerts</p>
              <p className="text-xs text-muted-foreground">Notify when a candidate completes an assessment</p>
            </div>
            <Switch checked={assessmentAlerts} onCheckedChange={setAssessmentAlerts} />
          </div>
        </CardContent>
      </Card>

      {/* Danger Zone */}
      <Card className="border-destructive/30">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-destructive"><Shield className="h-5 w-5" /> Danger Zone</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-between">
            <div>
              <p className="font-medium text-sm">Sign out of your account</p>
              <p className="text-xs text-muted-foreground">This will end your current session</p>
            </div>
            <Button variant="destructive" onClick={handleLogout} className="gap-2">
              <LogOut className="h-4 w-4" /> Logout
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
