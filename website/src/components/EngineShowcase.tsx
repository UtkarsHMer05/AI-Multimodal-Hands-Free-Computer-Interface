"use client";

/**
 * Landing-page engine showcase — deliberately NON-interactive.
 *
 * Real pointer control needs the local Python engine, so the landing page
 * shows the interface as a static composition and routes visitors to the
 * /dashboard, where the page connects to the engine over WebSocket and
 * becomes the full control surface (voice, head/gaze camera, tongue/blink
 * clicks — the real thing, driving the real Mac).
 */

import Link from "next/link";
import {
  IconVoice, IconGaze, IconGestureClick, IconArrowRight,
  IconMonitor, IconShield, IconPlay, IconWifi,
} from "./icons";

const PIPELINE = [
  { icon: IconVoice, color: "bg-red", label: "Voice", note: "Parakeet / Vosk · continuous" },
  { icon: IconGaze, color: "bg-blue", label: "Head & gaze", note: "MediaPipe · calibrated" },
  { icon: IconGestureClick, color: "bg-yellow", label: "Tongue & blink", note: "1·2·3 gestures, 2·4 blinks" },
];

export default function EngineShowcase() {
  return (
    <section id="demo" className="py-12 md:py-24 px-4 md:px-8 border-b-4 border-ink">
      <div className="max-w-7xl mx-auto">
        <header className="mb-8 md:mb-12">
          <p className="font-bold uppercase tracking-widest text-sm mb-2 text-red">
            Live control
          </p>
          <h2 className="text-4xl md:text-6xl font-black uppercase tracking-tighter">
            The real engine, on your Mac
          </h2>
          <p className="mt-4 max-w-2xl text-base md:text-lg leading-relaxed">
            Voice Cursor moves your actual pointer — that needs the local engine,
            so live control lives in the dashboard, connected to the Python
            application that drives macOS through Accessibility and native events.
          </p>
        </header>

        {/* Static mock — visual only, pointer-events none */}
        <div className="relative">
          <div
            aria-hidden
            className="relative overflow-hidden bg-[#a9c4e8] border-4 border-ink shadow-hard-lg select-none pointer-events-none"
            style={{ aspectRatio: "800 / 500" }}
          >
            <div className="absolute top-0 inset-x-0 h-9 bg-white/95 border-b-2 border-ink flex items-center px-3 gap-1 text-xs font-bold">
              <span className="flex items-center gap-1.5 mr-1">
                <span className="w-3 h-3 rounded-full bg-red" />
                <span className="w-3 h-3 bg-blue" />
                <span className="w-3 h-3 triangle-up bg-yellow" />
              </span>
              {["Finder", "File", "Edit", "View", "Window", "Help"].map((m) => (
                <span key={m} className="px-2 py-0.5">{m}</span>
              ))}
              <span className="ml-auto inline-flex items-center gap-1 bg-[#30c030] text-white px-2 py-0.5">
                <IconPlay size={10} /> ENABLED
              </span>
            </div>

            {/* desktop icons */}
            {[
              { label: "HCI Project", x: 66, y: 12 },
              { label: "src", x: 58, y: 26 },
              { label: "docs", x: 57, y: 39 },
              { label: "voice_cursor", x: 58, y: 52 },
              { label: "Downloads", x: 86, y: 26 },
            ].map((t) => (
              <div
                key={t.label}
                className="absolute flex flex-col items-center gap-1"
                style={{ left: `${t.x}%`, top: `${t.y}%`, transform: "translate(-50%, -50%)" }}
              >
                <div className="w-9 h-7 bg-[#f5d060] border-2 border-ink relative">
                  <div className="absolute -top-1.5 left-0 w-4 h-1.5 bg-[#f5d060] border-2 border-ink border-b-0" />
                </div>
                <span className="text-[10px] font-bold text-white" style={{ textShadow: "0 1px 2px rgba(0,0,0,0.8)" }}>
                  {t.label}
                </span>
              </div>
            ))}

            {/* window */}
            <div className="absolute left-[8%] top-[42%] w-[62%] demo-window">
              <div className="h-7 bg-ink flex items-center px-3 gap-2">
                <span className="w-2.5 h-2.5 rounded-full bg-red" />
                <span className="w-2.5 h-2.5 rounded-full bg-yellow" />
                <span className="w-2.5 h-2.5 rounded-full bg-[#30c030]" />
                <span className="ml-2 text-[10px] text-white uppercase tracking-widest font-bold">
                  Voice Cursor — Live Dashboard
                </span>
              </div>
              <div className="p-4 text-sm bg-white">
                <p className="font-bold mb-1">Transcript</p>
                <p className="font-mono">&ldquo;click Sign In&rdquo;</p>
                <p className="font-bold mt-3 mb-1">Feedback</p>
                <p>Clicked &ldquo;Sign In&rdquo; at (690, 300)</p>
                <div className="mt-3 flex gap-3 text-[10px] font-bold uppercase">
                  <span className="inline-flex items-center gap-1 bg-blue text-white px-2 py-0.5">
                    <IconWifi size={10} /> ENGINE CONNECTED
                  </span>
                  <span className="inline-flex items-center gap-1 bg-[#30c030] text-white px-2 py-0.5">
                    <IconPlay size={10} /> LISTENING
                  </span>
                </div>
              </div>
            </div>

            {/* form buttons */}
            <div className="absolute right-4 top-[24%] w-32 space-y-3">
              {["Sign In", "Submit", "Cancel", "Enable"].map((label) => (
                <div key={label} className="text-center text-xs font-bold uppercase bg-white border-2 border-ink px-2 py-2 shadow-hard-sm">
                  {label}
                </div>
              ))}
            </div>

            {/* click rings */}
            <div className="absolute" style={{ left: "86%", top: "60%" }}>
              <div className="w-14 h-14 -translate-x-1/2 -translate-y-1/2 rounded-full border-4 border-blue flex items-center justify-center font-black text-xl text-blue bg-white/60">
                1
              </div>
            </div>

            {/* cursor */}
            <svg className="absolute" style={{ left: "86%", top: "60%", width: 20, height: 20 }} viewBox="0 0 24 24" fill="none" stroke="#121212" strokeWidth="2.5">
              <path d="M4 4 L4 20 L8 16 L11 22 L14 20 L11 15 L16 15 Z" fill="#121212" />
            </svg>
          </div>

          {/* "Open the dashboard" overlay card */}
          <div className="mt-6 flex flex-col sm:flex-row sm:items-center gap-4 justify-between border-4 border-ink bg-yellow shadow-hard-lg p-5">
            <div className="flex items-start gap-3">
              <IconMonitor size={32} className="shrink-0" />
              <div>
                <p className="font-black uppercase tracking-tight text-xl">
                  Open the live dashboard
                </p>
                <p className="text-sm font-medium mt-1 max-w-xl">
                  Start it with{" "}
                  <code className="bg-white border border-ink/30 px-1">./run_website.command</code>{" "}
                  — one double-click runs the engine and opens the dashboard at{" "}
                  <code className="bg-white border border-ink/30 px-1">localhost:8757/dashboard</code>.
                  Voice, head tracking, eye gaze, tongue and blink clicks — the
                  whole system, driven from the browser.
                </p>
              </div>
            </div>
            <Link href="/dashboard" className="btn-bauhaus btn-bauhaus-md bg-red text-white shrink-0">
              Go to dashboard <IconArrowRight size={18} />
            </Link>
          </div>
        </div>

        {/* Pipeline chips */}
        <div className="mt-8 grid sm:grid-cols-3 gap-4">
          {PIPELINE.map((p) => (
            <div key={p.label} className="border-4 border-ink bg-white shadow-hard p-4 flex items-center gap-4">
              <div className={`w-12 h-12 ${p.color === "bg-yellow" ? "text-ink" : "text-white"} ${p.color} border-2 border-ink flex items-center justify-center shrink-0`}>
                <p.icon size={24} strokeWidth={2.5} />
              </div>
              <div>
                <p className="font-black uppercase tracking-tight">{p.label}</p>
                <p className="text-xs text-ink/70">{p.note}</p>
              </div>
            </div>
          ))}
        </div>

        <p className="mt-6 text-xs font-bold uppercase tracking-widest text-ink/50 flex items-center gap-2">
          <IconShield size={14} />
          All inference stays on your Mac — nothing is uploaded
        </p>
      </div>
    </section>
  );
}
