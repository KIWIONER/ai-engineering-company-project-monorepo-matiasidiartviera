"use client";

import React, { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Menu, X } from "lucide-react";
import styles from "./BackofficeNavbar.module.css";

const NAV_LINKS = [
  { label: "Conocimiento RAG", href: "/knowledge" },
  { label: "Portal RFPs", href: "/rfps" },
  { label: "Reporting Ejecutivo", href: "/reporting" },
  { label: "Chat Soporte", href: "/support-chat" },
  { label: "Inventario", href: "/inventory/products" },
];

export function BackofficeNavbar() {
  const pathname = usePathname();
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  if (pathname === "/login") {
    return null;
  }

  const websiteUrl =
    process.env.NEXT_PUBLIC_WEBSITE_URL || "http://localhost:3000";

  return (
    <header className={styles.header}>
      <div className={styles.inner}>
        <Link href="/reporting" className={styles.brand}>
          <span className={styles.logoBox}>N</span>
          <span>Nexova Backoffice</span>
        </Link>

        {/* Navegación Desktop (>= 1280px) */}
        <nav
          aria-label="Navegación global del Backoffice"
          className={styles.desktopNav}
        >
          {NAV_LINKS.map((item) => {
            const active = pathname.startsWith(item.href);
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`${styles.navLink} ${active ? styles.navLinkActive : ""}`}
              >
                {item.label}
              </Link>
            );
          })}
        </nav>

        {/* CTAs Derecha Desktop (>= 1280px) */}
        <div className={styles.desktopCtas}>
          <a href={`${websiteUrl}/admin/panel`} className={styles.ctaAdmin}>
            Panel Admin ↗
          </a>
          <a href={websiteUrl} className={styles.ctaWebsite}>
            Website Oficial ↗
          </a>
        </div>

        {/* Botón Móvil / Tablet (< 1280px) */}
        <button
          type="button"
          className={styles.menuButton}
          aria-expanded={isMobileMenuOpen}
          aria-label="Abrir menú del Backoffice"
          onClick={() => setIsMobileMenuOpen((prev) => !prev)}
        >
          {isMobileMenuOpen ? <X size={20} /> : <Menu size={20} />}
        </button>
      </div>

      {/* Menú Desplegable Móvil / Tablet */}
      {isMobileMenuOpen && (
        <div
          className={styles.mobileDropdown}
          aria-label="Menú móvil del Backoffice"
        >
          <ul className={styles.mobileList}>
            {NAV_LINKS.map((item) => {
              const active = pathname.startsWith(item.href);
              return (
                <li key={item.href}>
                  <Link
                    href={item.href}
                    onClick={() => setIsMobileMenuOpen(false)}
                    className={`${styles.mobileLink} ${active ? styles.mobileLinkActive : ""}`}
                  >
                    {item.label}
                  </Link>
                </li>
              );
            })}
            <li className={styles.mobileCtas}>
              <a
                href={`${websiteUrl}/admin/panel`}
                onClick={() => setIsMobileMenuOpen(false)}
                className={`${styles.mobileCtaLink} ${styles.ctaAdmin}`}
              >
                Panel Admin ↗
              </a>
              <a
                href={websiteUrl}
                onClick={() => setIsMobileMenuOpen(false)}
                className={`${styles.mobileCtaLink} ${styles.ctaWebsite}`}
              >
                Website Oficial ↗
              </a>
            </li>
          </ul>
        </div>
      )}
    </header>
  );
}
