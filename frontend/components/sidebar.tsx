"use client";

import React, { useState } from "react";
import { usePathname } from "next/navigation";
import { Button } from "@heroui/button";
import { Link } from "@heroui/link";
import { Card, CardBody } from "@heroui/card";
import NextLink from "next/link";
import clsx from "clsx";
import {
  Home,
  Settings,
  Package,
  Menu,
  X,
  Bot,
} from "lucide-react";

interface SidebarItem {
  title: string;
  icon: React.ComponentType<{ className?: string }>;
  href: string;
}

const menuItems: SidebarItem[] = [
  {
    title: "Dashboard",
    icon: Home,
    href: "/dashboard",
  },
  {
    title: "Import",
    icon: Package,
    href: "/dashboard/import",
  },
  {
    title: "AI Bot",
    icon: Bot,
    href: "/dashboard/ai-bot",
  }
];

const bottomMenuItems: SidebarItem[] = [
  {
    title: "Настройки",
    icon: Settings,
    href: "/dashboard/settings",
  },
];

interface SidebarProps {
  isOpen?: boolean;
  onToggle?: () => void;
}

export function Sidebar({ isOpen = true, onToggle }: SidebarProps) {
  const [isMobileOpen, setIsMobileOpen] = useState(false);
  const pathname = usePathname();

  const handleToggle = () => {
    setIsMobileOpen(!isMobileOpen);
    onToggle?.();
  };

  const isActive = (href: string) => {
    if (href === "/dashboard") {
      return pathname === "/dashboard";
    }
    return pathname.startsWith(href);
  };

  return (
    <>
      {/* Mobile menu button */}
      <Button
        isIconOnly
        variant="light"
        className="lg:hidden fixed top-4 left-4 z-50"
        onPress={handleToggle}
        aria-label="Toggle sidebar"
      >
        {isMobileOpen ? <X size={24} /> : <Menu size={24} />}
      </Button>

      {/* Mobile overlay */}
      {isMobileOpen && (
        <div
          className="lg:hidden fixed inset-0 bg-black/50 z-40"
          onClick={handleToggle}
        />
      )}

      {/* Sidebar */}
      <Card
        className={clsx(
          "fixed lg:sticky top-0 left-0 h-screen w-64 z-40 transition-transform duration-300",
          "lg:translate-x-0",
          isMobileOpen ? "translate-x-0" : "-translate-x-full"
        )}
        radius="none"
      >
        <CardBody className="p-0 flex flex-col h-full">
          {/* Header */}
          <div className="p-4 border-b border-divider">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary text-primary-foreground">
                <Package className="h-5 w-5" />
              </div>
              <div className="flex flex-col">
                <span className="text-sm font-bold">Dashboard</span>
                <span className="text-xs text-default-500">v1.0.0</span>
              </div>
            </div>
          </div>

          {/* Menu Items */}
          <div className="flex-1 overflow-y-auto py-4">
            <div className="px-2">
              <div className="text-xs font-semibold text-default-500 uppercase px-3 mb-2">
                Меню
              </div>
              <div className="flex flex-col gap-1">
                {menuItems.map((item) => {
                  const active = isActive(item.href);
                  return (
                    <Link
                      key={item.title}
                      as={NextLink}
                      href={item.href}
                      className={clsx(
                        "flex items-center gap-3 px-3 py-2 rounded-lg transition-colors",
                        "hover:bg-default-100",
                        active && "bg-primary text-primary-foreground"
                      )}
                      onClick={() => setIsMobileOpen(false)}
                    >
                      <item.icon className="h-5 w-5" />
                      <span className="text-sm font-medium">{item.title}</span>
                    </Link>
                  );
                })}
              </div>
            </div>
          </div>

          {/* Footer */}
          <div className="p-4 border-t border-divider">
            <div className="flex flex-col gap-1">
              {bottomMenuItems.map((item) => {
                const active = isActive(item.href);
                return (
                  <Link
                    key={item.title}
                    as={NextLink}
                    href={item.href}
                    className={clsx(
                      "flex items-center gap-3 px-3 py-2 rounded-lg transition-colors",
                      "hover:bg-default-100",
                      active && "bg-primary text-primary-foreground"
                    )}
                    onClick={() => setIsMobileOpen(false)}
                  >
                    <item.icon className="h-5 w-5" />
                    <span className="text-sm font-medium">{item.title}</span>
                  </Link>
                );
              })}
            </div>
          </div>
          <div className="flex justify-center p-4 border-t border-divider">
            <Link
              className="flex items-center gap-1 text-current"
              href="https://terricon.kz"
              title="terricon homepage"
            >
              <span className="text-default-600">Made for</span>
              <p className="text-primary">Terricon Valley</p>
            </Link>
          </div>
        </CardBody>
      </Card>
    </>
  );
}

