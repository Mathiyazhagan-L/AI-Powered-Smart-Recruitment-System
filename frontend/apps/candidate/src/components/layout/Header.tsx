"use client";

import Link from "next/link";
import Image from "next/image";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Bell, Briefcase, FileText, CheckSquare, Calendar, Gift, User, LayoutDashboard } from "lucide-react";
import { useUser } from "@/lib/hooks/useAuth";
import { useGetProfile } from "@/lib/hooks/useProfile";

import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

const navItems = [
  { name: "Dashboard", href: "/", icon: LayoutDashboard },
  { name: "Jobs", href: "/jobs", icon: Briefcase },
  { name: "My Applications", href: "/applications", icon: FileText },
  { name: "Assessments", href: "/assessments", icon: CheckSquare },
  { name: "Interviews", href: "/interviews", icon: Calendar },
  { name: "Offers", href: "/offers", icon: Gift },
];

export function Header() {
  const pathname = usePathname();
  const { data: user } = useUser();
  const { data: profile } = useGetProfile(user?.id);

  return (
    <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 shadow-sm">
      <div className="container mx-auto flex h-16 items-center px-4 md:px-6">
        <Link href="/" className="flex items-center space-x-2 mr-8">
          <Image src="/logo.png" alt="AIHire Logo" width={32} height={32} className="w-auto h-8 object-contain" />
          <span className="font-bold text-xl text-secondary">AIHire</span>
          <span className="text-muted-foreground text-sm font-medium hidden md:inline-block border-l border-border pl-2 ml-2">
            {profile?.candidate_code ? `Candidate ID: ${profile.candidate_code}` : "Candidate Portal"}
          </span>
        </Link>
        <nav className="flex items-center space-x-6 text-sm font-medium flex-1 overflow-x-auto no-scrollbar">
          {navItems.map((item) => (
            <Link
              key={item.name}
              href={item.href}
              className={cn(
                "transition-colors hover:text-foreground/80 flex items-center whitespace-nowrap py-1 border-b-2",
                pathname === item.href ? "text-foreground font-semibold border-secondary" : "text-foreground/60 border-transparent hover:border-border"
              )}
            >
              <item.icon className="mr-2 h-4 w-4" />
              {item.name}
            </Link>
          ))}
        </nav>
        <div className="flex items-center space-x-4 ml-auto pl-4">
          <Button variant="ghost" size="icon" className="relative text-muted-foreground hover:text-foreground">
            <Bell className="h-5 w-5" />
            <span className="absolute top-1 right-1 h-2 w-2 bg-secondary rounded-full" />
          </Button>
          
          <DropdownMenu>
            <DropdownMenuTrigger className="p-0 border-none bg-transparent outline-none cursor-pointer">
              <Avatar className="h-8 w-8 cursor-pointer border-2 border-transparent hover:border-secondary transition-colors">
                <AvatarFallback className="bg-primary text-primary-foreground text-xs">Me</AvatarFallback>
              </Avatar>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-56">
              <DropdownMenuLabel>My Account</DropdownMenuLabel>
              <DropdownMenuSeparator />
              <DropdownMenuItem className="cursor-pointer" onClick={() => window.location.href = "/profile"}>
                <User className="mr-2 h-4 w-4" /> Basic Details
              </DropdownMenuItem>
              <DropdownMenuItem className="cursor-pointer" onClick={() => window.location.href = "/profile/resume"}>
                <FileText className="mr-2 h-4 w-4" /> Resume Parser
              </DropdownMenuItem>
              <DropdownMenuItem className="cursor-pointer" onClick={() => window.location.href = "/jobs/saved"}>
                <Briefcase className="mr-2 h-4 w-4" /> Saved Jobs
              </DropdownMenuItem>
              <DropdownMenuItem className="cursor-pointer" onClick={() => window.location.href = "/profile/education"}>
                <Briefcase className="mr-2 h-4 w-4" /> Education
              </DropdownMenuItem>
              <DropdownMenuItem className="cursor-pointer" onClick={() => window.location.href = "/profile/experience"}>
                <Briefcase className="mr-2 h-4 w-4" /> Experience
              </DropdownMenuItem>
              <DropdownMenuItem className="cursor-pointer" onClick={() => window.location.href = "/profile/skills"}>
                <CheckSquare className="mr-2 h-4 w-4" /> Skills
              </DropdownMenuItem>
              <DropdownMenuItem className="cursor-pointer" onClick={() => window.location.href = "/profile/projects"}>
                <CheckSquare className="mr-2 h-4 w-4" /> Projects
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem className="cursor-pointer" onClick={() => window.location.href = "/profile"}>
                Settings
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem className="text-destructive w-full cursor-pointer" onClick={() => window.location.href = "/login"}>
                Log out
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>

        </div>
      </div>
    </header>
  );
}
