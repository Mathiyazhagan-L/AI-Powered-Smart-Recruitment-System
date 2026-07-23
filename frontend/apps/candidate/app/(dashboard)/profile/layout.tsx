"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useUser } from "@/lib/hooks/useAuth";
import { useProfileCompletion } from "@/lib/hooks/useProfile";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import {
  User,
  GraduationCap,
  Briefcase,
  Code,
  FolderOpen,
  FileText,
} from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";

const profileNavItems = [
  { name: "Basic Details", href: "/profile", icon: User },
  { name: "Resume Parsing", href: "/profile/resume", icon: FileText },
  { name: "Education", href: "/profile/education", icon: GraduationCap },
  { name: "Experience", href: "/profile/experience", icon: Briefcase },
  { name: "Skills", href: "/profile/skills", icon: Code },
  { name: "Projects", href: "/profile/projects", icon: FolderOpen },
];

export default function ProfileLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const pathname = usePathname();
  const { data: user } = useUser();
  const { completionPercentage, isLoading } = useProfileCompletion(user?.id);

  return (
    <div className="flex flex-col md:flex-row gap-8 max-w-6xl mx-auto w-full">
      {/* Sidebar Navigation */}
      <aside className="w-full md:w-64 shrink-0 flex flex-col gap-6">
        <Card className="border-none shadow-sm bg-card/50 backdrop-blur-sm">
          <CardContent className="p-4 flex flex-col gap-2">
            <h3 className="text-sm font-semibold text-muted-foreground mb-2 px-2 uppercase tracking-wider">
              Profile Completion
            </h3>
            <div className="px-2 mb-4">
              <div className="flex justify-between items-center mb-2">
                <span className="text-2xl font-bold text-primary">
                  {isLoading ? "..." : completionPercentage}%
                </span>
              </div>
              <Progress value={completionPercentage} className="h-2" />
              <p className="text-xs text-muted-foreground mt-2">
                Complete your profile to unlock all platform features.
              </p>
            </div>
          </CardContent>
        </Card>

        <nav className="flex flex-row md:flex-col gap-1 overflow-x-auto pb-4 md:pb-0 hide-scrollbar">
          {profileNavItems.map((item) => {
            const isActive = pathname === item.href;
            return (
              <Link key={item.name} href={item.href}>
                <Button
                  variant={isActive ? "secondary" : "ghost"}
                  className={cn(
                    "w-full justify-start gap-3 rounded-lg transition-all",
                    isActive 
                      ? "bg-secondary text-secondary-foreground font-semibold shadow-sm" 
                      : "text-muted-foreground hover:bg-muted hover:text-foreground"
                  )}
                >
                  <item.icon className={cn("h-4 w-4", isActive ? "text-primary" : "")} />
                  <span className="whitespace-nowrap">{item.name}</span>
                </Button>
              </Link>
            );
          })}
        </nav>
      </aside>

      {/* Main Content Area */}
      <div className="flex-1 min-w-0">
        <div className="bg-card/50 backdrop-blur-sm rounded-xl p-6 shadow-sm border border-border/50 min-h-[500px]">
          {children}
        </div>
      </div>
    </div>
  );
}
