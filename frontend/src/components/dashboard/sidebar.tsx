"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const navItems = [
  { href: "/", label: "Dashboard", icon: "📊" },
  { href: "/studies", label: "Çalışmalar", icon: "🔬" },
  { href: "/viewer", label: "DICOM Viewer", icon: "🖥️" },
  { href: "/reports", label: "Raporlar", icon: "📋" },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="w-64 border-r bg-card flex flex-col">
      <div className="p-6 border-b">
        <h1 className="text-xl font-bold">AlpCAN</h1>
        <p className="text-xs text-muted-foreground mt-1">
          Cancer Analysis Network
        </p>
      </div>

      <nav className="flex-1 p-4 space-y-1">
        {navItems.map((item) => {
          const isActive = pathname === item.href;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex items-center gap-3 px-3 py-2 rounded-md text-sm transition-colors ${
                isActive
                  ? "bg-primary text-primary-foreground"
                  : "hover:bg-muted"
              }`}
            >
              <span>{item.icon}</span>
              {item.label}
            </Link>
          );
        })}
      </nav>

      <div className="p-4 border-t">
        <div className="text-xs text-muted-foreground">
          <p>ALPISS Suite v0.1.0</p>
          <p className="mt-1">Giresun Üniversitesi</p>
        </div>
      </div>
    </aside>
  );
}
