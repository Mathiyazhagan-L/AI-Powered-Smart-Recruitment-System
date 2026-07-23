"use client";

import Link from "next/link";
import Image from "next/image";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import {
  LayoutDashboard,
  Users,
  Briefcase,
  FileText,
  UserCheck,
  Calendar,
  Gift,
  BarChart3,
  MessageSquare,
  Settings,
  User,
  Menu
} from "lucide-react";
import { useState } from "react";
import { Button } from "@/components/ui/button";

const navItems = [
  { name: "Dashboard", href: "/", icon: LayoutDashboard },
  { name: "Candidates", href: "/candidates", icon: Users },
  { name: "Jobs", href: "/jobs", icon: Briefcase },
  { name: "Applications", href: "/applications", icon: FileText },
  { name: "HR Queue", href: "/hr-queue", icon: UserCheck },
  { name: "Interviews", href: "/interviews", icon: Calendar },
  { name: "Offers", href: "/offers", icon: Gift },
  { name: "Analytics", href: "/analytics", icon: BarChart3 },
  { name: "Communication Center", href: "/communication", icon: MessageSquare },
];

const bottomNavItems = [
  { name: "Settings", href: "/settings", icon: Settings },
  { name: "Profile", href: "/profile", icon: User },
];

export function Sidebar() {
  const pathname = usePathname();
  const [collapsed, setCollapsed] = useState(false);

  return (
    <aside
      className={cn(
        "flex flex-col bg-primary text-primary-foreground transition-all duration-300",
        collapsed ? "w-[80px]" : "w-[280px]"
      )}
    >
      <div className="flex h-16 items-center justify-between px-4 border-b border-white/10">
        {!collapsed && (
          <Link href="/" className="flex items-center gap-2">
            <Image src="/logo.png" alt="AIHire Logo" width={32} height={32} className="w-auto h-8 object-contain" onError={() => {}} />
            <span className="font-bold text-xl text-secondary">AIHire</span>
          </Link>
        )}
        <Button
          variant="ghost"
          size="icon"
          onClick={() => setCollapsed(!collapsed)}
          className="text-primary-foreground hover:text-secondary hover:bg-white/10"
        >
          <Menu className="h-5 w-5" />
        </Button>
      </div>

      <nav className="flex-1 overflow-y-auto py-4 px-2">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = pathname === item.href || (item.href !== "/" && pathname.startsWith(item.href));
          return (
            <Link
              key={item.name}
              href={item.href}
              className={cn(
                "flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-all duration-200 mb-1",
                isActive
                  ? "bg-secondary text-black"
                  : "text-primary-foreground/70 hover:text-primary-foreground hover:bg-white/10"
              )}
            >
              <Icon className={cn("h-4 w-4 shrink-0", isActive ? "text-black" : "")} />
              {!collapsed && <span>{item.name}</span>}
            </Link>
          );
        })}
      </nav>

      <div className="border-t border-white/10 py-4 px-2">
        {bottomNavItems.map((item) => {
          const Icon = item.icon;
          const isActive = pathname === item.href;
          return (
            <Link
              key={item.name}
              href={item.href}
              className={cn(
                "flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-all duration-200 mb-1",
                isActive
                  ? "bg-secondary text-black"
                  : "text-primary-foreground/70 hover:text-primary-foreground hover:bg-white/10"
              )}
            >
              <Icon className={cn("h-4 w-4 shrink-0", isActive ? "text-black" : "")} />
              {!collapsed && <span>{item.name}</span>}
            </Link>
          );
        })}
      </div>
    </aside>
  );
}
