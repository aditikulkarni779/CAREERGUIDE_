import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "AI Career Copilot",
  description: "Your personal AI career mentor",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
