import { Header } from "@/components/layout/Header";

export default function DashboardLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <div className="min-h-screen bg-muted/20 flex flex-col font-sans antialiased">
      <Header />
      <main className="flex-1 container mx-auto p-4 md:p-8 lg:p-12">
        {children}
      </main>
    </div>
  );
}
