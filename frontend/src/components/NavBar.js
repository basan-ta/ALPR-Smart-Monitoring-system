"use client";
import Link from "next/link";
import { useMemo, useState, useEffect } from "react";
import { API_BASE } from "../lib/api";

export default function NavBar() {
  const [open, setOpen] = useState(false);

  const adminUrl = useMemo(() => {
    try {
      const base = API_BASE || '/api';
      if (/^https?:\/\//i.test(base)) {
        return base.replace(/\/$/, '').replace(/\/api\/?$/, '/admin/');
      }
      const origin = process.env.NEXT_PUBLIC_BACKEND_ORIGIN || 'http://127.0.0.1:8000';
      return `${origin.replace(/\/+$/, '')}/admin/`;
    } catch {
      return 'http://127.0.0.1:8000/admin/';
    }
  }, []);

  // Close menu on Escape for accessibility
  useEffect(() => {
    function onKey(e) {
      if (e.key === 'Escape') setOpen(false);
    }
    if (open) {
      window.addEventListener('keydown', onKey);
    }
    return () => window.removeEventListener('keydown', onKey);
  }, [open]);

  return (
    <nav className="container mx-auto px-4 py-3" role="navigation" aria-label="Primary navigation">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Logo />
          <div className="leading-tight">
            <div className="font-semibold tracking-wide" style={{ color: "var(--primary)" }}>
              सशस्त्र प्रहरी बल, नेपाल Armed Police Force, Nepal
            </div>
            <div className="text-xs text-gray-500">ALPR & Smart Monitoring Dashboard</div>
          </div>
        </div>

        <button
          className="md:hidden border border-muted rounded px-3 py-2"
          aria-label="Toggle menu"
          aria-expanded={open}
          aria-controls="primary-navigation"
          aria-haspopup="true"
          onClick={() => setOpen((v) => !v)}
        >
          Menu
        </button>

        <ul id="primary-navigation" className="hidden md:flex items-center gap-4 text-sm">
          <li>
            <Link className="px-3 py-2 rounded hover:opacity-80 focus-visible:outline-2 focus-visible:outline-offset-2" href="/">Dashboard</Link>
          </li>
          <li>
            <Link className="px-3 py-2 rounded hover:opacity-80 focus-visible:outline-2 focus-visible:outline-offset-2" href="/dataset">Dataset</Link>
          </li>
          <li>
            <a className="px-3 py-2 rounded hover:opacity-80 focus-visible:outline-2 focus-visible:outline-offset-2" href={adminUrl} target="_blank" rel="noopener noreferrer">Admin</a>
          </li>
          <li>
            <CTAButton href="/dataset">View Vehicles</CTAButton>
          </li>
        </ul>
      </div>

      {open && (
        <div className="md:hidden mt-3 animate-slide-up" aria-label="Mobile menu">
          <ul className="flex flex-col gap-2">
            <li>
              <Link className="block px-3 py-2 rounded border border-muted bg-surface" href="/" onClick={() => setOpen(false)}>Dashboard</Link>
            </li>
            <li>
              <Link className="block px-3 py-2 rounded border border-muted bg-surface" href="/dataset" onClick={() => setOpen(false)}>Dataset</Link>
            </li>
            <li>
              <a className="block px-3 py-2 rounded border border-muted bg-surface" href={adminUrl} target="_blank" rel="noopener noreferrer" onClick={() => setOpen(false)}>Admin</a>
            </li>
            <li>
              <CTAButton href="/dataset" onClick={() => setOpen(false)}>View Vehicles</CTAButton>
            </li>
          </ul>
        </div>
      )}
    </nav>
  );
}

function CTAButton({ href, children, onClick }) {
  return (
    <Link
      href={href}
      onClick={onClick}
      className="inline-flex items-center gap-2 px-3 py-2 rounded-md text-white"
      style={{ background: "var(--primary)" }}
      aria-label="Primary action"
    >
      {children}
      <span aria-hidden="true" className="inline-block w-2 h-2 rounded-full" style={{ background: "var(--accent)" }}></span>
    </Link>
  );
}

function Logo() {
  return (
    <svg width="32" height="32" viewBox="0 0 32 32" aria-hidden="true" className="rounded">
      <rect x="0" y="0" width="32" height="32" rx="6" style={{ fill: "var(--primary)" }}></rect>
      <path d="M6 20 L16 6 L26 20" fill="none" stroke="var(--accent)" strokeWidth="2" />
      <circle cx="16" cy="22" r="3" fill="var(--accent)" />
    </svg>
  );
}