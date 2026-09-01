import type { Metadata } from "next";
import { Outfit } from "next/font/google";
import "./globals.css";

const outfit = Outfit({
  subsets: ["latin"],
  weight: ["400", "500", "700", "900"],
  variable: "--font-outfit",
  display: "swap",
});

export const metadata: Metadata = {
  title: "Voice Cursor — Multimodal Hands-Free Computer Interface",
  description:
    "Offline-first HCI prototype controlling macOS with voice commands, head tracking, eye-gaze estimation, and calibrated tongue & blink gestures. Runs entirely on-device with pretrained local AI models.",
  keywords: [
    "HCI",
    "assistive technology",
    "voice control",
    "head tracking",
    "eye gaze",
    "hands-free",
    "offline AI",
    "MediaPipe",
  ],
  authors: [{ name: "Utkarsh Khajuria" }],
  openGraph: {
    title: "Voice Cursor — Multimodal Hands-Free Interface",
    description:
      "Control macOS without a mouse: voice, head, eyes, and facial gestures — all offline.",
    type: "website",
  },
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" className={outfit.variable}>
      <body className="font-outfit antialiased">
        <a href="#main" className="skip-link">
          Skip to content
        </a>
        {children}
      </body>
    </html>
  );
}
