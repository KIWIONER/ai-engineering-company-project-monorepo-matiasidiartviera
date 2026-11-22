import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import {TelemetryProvider} from "../components/TelemetryProvider";
import { BackofficeNavbar } from "../components/BackofficeNavbar";


const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Nexova Backoffice",
  description: "Internal Tools",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="en" className={`${geistSans.variable} ${geistMono.variable}`}>
      <body>
        <TelemetryProvider>
          <BackofficeNavbar />
          {children}
        </TelemetryProvider>
      </body>
    </html>
  );
}
