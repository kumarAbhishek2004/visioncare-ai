import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "VisionCare AI — Explainable Radiology Workstation & Decision Support",
  description:
    "Production-grade Clinical Decision Support platform for frontal chest radiographs with 14 NIH pathologies, Grad-CAM++ attribution, 5-zone anatomical localization, and ACR reporting.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body className={`${inter.className} bg-radDark-950 text-slate-100 min-h-screen antialiased`}>
        {children}
      </body>
    </html>
  );
}
