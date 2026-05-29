import type { Metadata } from "next";
import { Inter } from "next/font/google";

import { ToastProvider } from "@/components/ui/toast";

import "./globals.css";

const inter = Inter({
  subsets: ["latin"],
  display: "swap",
  variable: "--font-sans",
});

export const metadata: Metadata = {
  title: "Talenscan — Inteligencia de talento",
  description: "Plataforma B2B para inteligencia de talento, evaluación 360 y pipeline de búsqueda ejecutiva.",
  icons: {
    icon: [
      { url: "/favicon.png", type: "image/png" },
    ],
    apple: [{ url: "/favicon.png" }],
  },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="es" className={inter.variable}>
      <body className="font-sans">
        <ToastProvider>{children}</ToastProvider>
      </body>
    </html>
  );
}
