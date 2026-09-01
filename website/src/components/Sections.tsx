"use client";

/**
 * Landing-page sections. Client components (Nav/FAQ need state); the rest
 * are plain presentational functions.
 *
 * All icons come from ./icons — hand-drawn geometric SVGs, no icon library.
 */

import { useState } from "react";
import Image from "next/image";
import {
  IconVoice, IconHead, IconGaze, IconGestureClick, IconWaveform,
  IconChip, IconScanText, IconShieldBolt, IconShield, IconLock,
  IconCheck, IconTerminal, IconClone, IconPlay, IconMonitor,
  IconActivity, IconDoc, IconChevronDown, IconArrowRight, IconX,
  IconCode, IconMenu,
} from "./icons";

const REPO_URL = "https://github.com/UtkarsHMer05/AI-Multimodal-Hands-Free-Computer-Interface";

/* ------------------------------------------------------------------ Nav */

export function Nav() {
  const [open, setOpen] = useState(false);
  const links = [
    ["Dashboard", "/dashboard/"],
    ["Modalities", "#modalities"],
    ["How it works", "#how"],
    ["Commands", "#commands"],
    ["Architecture", "#architecture"],
    ["Evaluation", "#evaluation"],
    ["Get started", "#get-started"],
    ["FAQ", "#faq"],
  ] as const;
  return (
    <header className="sticky top-0 z-40 bg-canvas border-b-4 border-ink">
      <div className="max-w-7xl mx-auto px-4 md:px-8 py-3 flex items-center justify-between gap-4">
        <a href="#hero" className="flex items-center gap-3 group" aria-label="Voice Cursor home">
          <span className="flex items-center gap-1.5" aria-hidden>
            <span className="w-[18px] h-[18px] rounded-full bg-red group-hover:scale-110 transition-transform" />
            <span className="w-[15px] h-[15px] bg-blue group-hover:scale-110 transition-transform" />
            <span className="w-[18px] h-[18px] triangle-up bg-yellow group-hover:scale-110 transition-transform" />
          </span>
          <span className="font-black uppercase tracking-tighter text-lg md:text-xl">
            Voice<span className="text-red">Cursor</span>
          </span>
        </a>
        <nav className="hidden lg:flex items-center gap-1 text-sm font-bold uppercase tracking-wider" aria-label="Main">
          {links.map(([label, href]) => (
            <a key={href} href={href} className="px-3 py-1.5 hover:bg-yellow border-2 border-transparent hover:border-ink transition-colors">
              {label}
            </a>
          ))}
          <a
            href={REPO_URL}
            target="_blank"
            rel="noreferrer"
            className="ml-2 inline-flex items-center gap-1.5 border-2 border-ink bg-ink text-white px-3 py-1.5 shadow-hard-sm hover:-translate-y-0.5 transition-transform"
          >
            <IconCode size={15} /> Source
          </a>
        </nav>
        <button
          className="lg:hidden border-2 border-ink bg-white p-2 shadow-hard-sm active:translate-x-[2px] active:translate-y-[2px] active:shadow-none"
          onClick={() => setOpen((o) => !o)}
          aria-expanded={open}
          aria-label="Toggle menu"
        >
          {open ? <IconX size={20} /> : <IconMenu size={20} />}
        </button>
      </div>
      {open && (
        <nav className="lg:hidden border-t-4 border-ink bg-white px-4 py-3 flex flex-col gap-1 text-sm font-bold uppercase tracking-wider" aria-label="Mobile">
          {links.map(([label, href]) => (
            <a key={href} href={href} onClick={() => setOpen(false)} className="px-3 py-2 hover:bg-yellow border-2 border-transparent hover:border-ink">
              {label}
            </a>
          ))}
          <a href={REPO_URL} target="_blank" rel="noreferrer" className="px-3 py-2 mt-1 bg-ink text-white inline-flex items-center gap-2 w-fit">
            <IconCode size={16} /> Source
          </a>
        </nav>
      )}
    </header>
  );
}

/* ------------------------------------------------------------------ Hero */

export function Hero() {
  return (
    <section id="hero" className="border-b-4 border-ink">
      <div className="max-w-7xl mx-auto grid lg:grid-cols-2">
        <div className="py-12 md:py-24 px-4 md:px-8 flex flex-col justify-center">
          <p className="inline-flex items-center gap-2 text-xs md:text-sm font-bold uppercase tracking-widest bg-ink text-white w-fit px-3 py-1.5 mb-6">
            <IconLock size={14} className="text-yellow" /> Offline · On-device · No cloud keys
          </p>
          <h1 className="text-5xl md:text-7xl xl:text-8xl font-black uppercase tracking-tighter leading-[0.9]">
            Control your{" "}
            <span className="inline-block bg-red text-white px-3 -rotate-1">Mac</span>{" "}
            without a{" "}
            <span className="inline-block bg-yellow px-3 rotate-1">mouse</span>
          </h1>
          <p className="mt-6 text-lg md:text-xl leading-relaxed max-w-xl">
            Voice Cursor is a hands-free human–computer interface combining{" "}
            <strong>voice commands</strong>, <strong>head tracking</strong>,{" "}
            <strong>eye-gaze estimation</strong>, and calibrated{" "}
            <strong>tongue & blink gestures</strong> — all running locally on
            ordinary MacBook hardware.
          </p>
          <div className="mt-8 flex flex-wrap gap-4">
            <a href="/dashboard/" className="btn-bauhaus btn-bauhaus-md bg-red text-white">
              Open live dashboard <IconArrowRight size={18} />
            </a>
            <a href="#how" className="btn-bauhaus btn-bauhaus-md bg-white text-ink">
              How it works
            </a>
          </div>
          <p className="mt-6 text-xs font-bold uppercase tracking-widest text-ink/60">
            DA1 · Voice-based control of computer actions, extended with camera-based assistive interaction
          </p>
        </div>

        <div className="relative bg-blue border-l-0 lg:border-l-4 border-ink min-h-[320px] lg:min-h-full dot-grid overflow-hidden">
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="relative w-56 h-56 md:w-72 md:h-72 shape-drift">
              <div className="absolute inset-0 rounded-full bg-yellow border-4 border-ink" />
              <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-3/5 h-3/5 bg-white border-4 border-ink rotate-45" />
              <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-1/3 h-1/3 bg-red border-4 border-ink" />
              <div className="absolute -top-6 -right-6 w-16 h-16 triangle-up bg-yellow border-0" />
            </div>
          </div>
          <div className="absolute bottom-6 left-6 bg-white border-2 border-ink shadow-hard px-4 py-3 max-w-[240px]">
            <p className="text-xs font-bold uppercase tracking-widest text-blue">Live transcript</p>
            <p className="font-mono text-sm mt-1">&ldquo;click Enable&rdquo;</p>
            <p className="text-xs mt-1 text-ink/70">→ Found the real button. Clicked.</p>
          </div>
          <div className="absolute top-6 right-6 bg-white border-2 border-ink shadow-hard px-4 py-3">
            <p className="text-xs font-bold uppercase tracking-widest text-red">Session log</p>
            <p className="font-mono text-xs mt-1">12:01:07 · success</p>
          </div>
        </div>
      </div>
    </section>
  );
}

/* ------------------------------------------------------------------ Stats */

export function Stats() {
  const stats = [
    { value: "4", label: "Input modalities", sub: "voice · head · gaze · gestures" },
    { value: "65+", label: "Automated tests", sub: "grammar, safety, targeting" },
    { value: "0", label: "Cloud API keys", sub: "fully offline inference" },
    { value: "$0", label: "Extra hardware", sub: "just a MacBook" },
  ];
  return (
    <section className="bg-yellow border-b-4 border-ink">
      <div className="max-w-7xl mx-auto grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 divide-y sm:divide-y-0 sm:divide-x divide-ink/30">
        {stats.map((s, i) => (
          <div key={s.label} className="px-6 py-8 md:py-12 flex items-center gap-4">
            <span
              aria-hidden
              className={
                i % 3 === 0
                  ? "w-10 h-10 shrink-0 rounded-full bg-white border-2 border-ink"
                  : i % 3 === 1
                    ? "w-10 h-10 shrink-0 bg-white border-2 border-ink rotate-45"
                    : "w-10 h-10 shrink-0 triangle-up bg-white"
              }
            />
            <div>
              <p className="text-3xl md:text-5xl font-black tracking-tighter">{s.value}</p>
              <p className="text-xs font-bold uppercase tracking-widest">{s.label}</p>
              <p className="text-xs text-ink/70">{s.sub}</p>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}

/* ------------------------------------------------------------------ Modalities */

export function Modalities() {
  const items = [
    {
      icon: IconVoice,
      color: "bg-red",
      title: "Voice commands",
      body: "A constrained vocabulary of about twenty phrases — moves, clicks, scrolling, tabs — transcribed locally by Parakeet TDT 0.6B v3 with a Vosk fallback. A small grammar means fewer accidental actions.",
      points: ["Exact + fuzzy matching with a 0.84 confidence floor", "Named targets: “click Sign In”", "Pause / resume by voice"],
    },
    {
      icon: IconHead,
      color: "bg-blue",
      title: "Head tracking",
      body: "MediaPipe face landmarks estimate head pose. Look at the screen centre during the brief automatic calibration, then tilt or turn your head — the pointer follows continuously, like a joystick.",
      points: ["Automatic neutral-position calibration", "Movement dead zone + smoothing", "Recalibrate any time"],
    },
    {
      icon: IconGaze,
      color: "bg-yellow",
      title: "Eye gaze",
      body: "Iris position relative to both eyes estimates where you look. An estimate, not a medical tracker — good front lighting and a stable seat improve accuracy, and recalibration fixes drift.",
      points: ["Built-in RGB camera only", "Per-user calibrated thresholds", "Smoothed, dead-zoned signal"],
    },
    {
      icon: IconGestureClick,
      color: "bg-red",
      title: "Tongue & blink clicks",
      body: "Stick out and retract your tongue once, twice, or three times for single-, double-, and triple-click. Or blink rapidly: two blinks click, four double-click. One ordinary blink does nothing.",
      points: ["In-app guided calibration", "Numbered click rings (1 · 2 · 3 · R)", "Cursor freezes while a gesture confirms"],
    },
  ];
  return (
    <section id="modalities" className="py-12 md:py-24 px-4 md:px-8 border-b-4 border-ink bg-canvas">
      <div className="max-w-7xl mx-auto">
        <header className="mb-10 md:mb-16">
          <p className="font-bold uppercase tracking-widest text-sm mb-2 text-blue">Modalities</p>
          <h2 className="text-4xl md:text-6xl font-black uppercase tracking-tighter">
            Four channels, one pointer
          </h2>
          <p className="mt-4 max-w-2xl text-lg leading-relaxed">
            Each channel is optional and none replaces the others. They combine through a guarded action layer that refuses to guess.
          </p>
        </header>
        <div className="grid md:grid-cols-2 gap-6">
          {items.map((item) => (
            <article key={item.title} className="card-bauhaus p-6 md:p-8">
              <span
                aria-hidden
                className={`absolute top-4 right-4 w-3 h-3 ${item.color} rounded-full`}
              />
              <div className={`w-14 h-14 ${item.color === "bg-yellow" ? "text-ink" : "text-white"} ${item.color} border-2 border-ink shadow-hard-sm flex items-center justify-center mb-4`}>
                <item.icon size={28} />
              </div>
              <h3 className="text-xl md:text-2xl font-black uppercase tracking-tight">{item.title}</h3>
              <p className="mt-3 text-base leading-relaxed">{item.body}</p>
              <ul className="mt-4 space-y-1.5">
                {item.points.map((p) => (
                  <li key={p} className="flex gap-2 text-sm items-baseline">
                    <IconCheck size={14} className="shrink-0 mt-1 text-blue" />
                    <span>{p}</span>
                  </li>
                ))}
              </ul>
            </article>
          ))}
        </div>
      </div>
    </section>
  );
}

/* ------------------------------------------------------------------ How it works */

export function HowItWorks() {
  const steps = [
    {
      n: "1", icon: IconWaveform, color: "bg-red", title: "Capture",
      body: "Microphone audio and webcam frames are captured in isolated worker processes — a native failure can never close the app.",
    },
    {
      n: "2", icon: IconChip, color: "bg-blue", title: "Recognize",
      body: "Pretrained local models transcribe speech and extract face, iris, and mouth landmarks. Nothing is uploaded.",
    },
    {
      n: "3", icon: IconScanText, color: "bg-yellow", title: "Resolve",
      body: "Named targets resolve through macOS Accessibility first — genuine buttons and menus — then local OCR over visible words.",
    },
    {
      n: "4", icon: IconShieldBolt, color: "bg-red", title: "Act, safely",
      body: "A guarded layer checks pause state, activates the app under the pointer, sends native events, and shows numbered click rings.",
    },
  ];
  return (
    <section id="how" className="py-12 md:py-24 px-4 md:px-8 border-b-4 border-ink bg-white">
      <div className="max-w-7xl mx-auto">
        <header className="mb-10 md:mb-16">
          <p className="font-bold uppercase tracking-widest text-sm mb-2 text-red">Pipeline</p>
          <h2 className="text-4xl md:text-6xl font-black uppercase tracking-tighter">How it works</h2>
        </header>
        <div className="grid sm:grid-cols-2 md:grid-cols-4 gap-6">
          {steps.map((step, i) => (
            <div key={step.n} className="relative">
              <div className={`w-14 h-14 ${i % 2 === 0 ? "" : "rotate-45"} ${step.color} border-4 border-ink shadow-hard flex items-center justify-center`}>
                <span className={`font-black text-2xl ${step.color === "bg-yellow" ? "text-ink" : "text-white"} ${i % 2 === 0 ? "" : "-rotate-45"}`}>
                  {step.n}
                </span>
              </div>
              <div className="mt-4 border-l-4 border-ink pl-4 py-1">
                <step.icon size={22} className="mb-2" />
                <h3 className="font-black uppercase tracking-tight text-lg">{step.title}</h3>
                <p className="mt-2 text-sm leading-relaxed">{step.body}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

/* ------------------------------------------------------------------ Commands table */

export function CommandTable() {
  const rows: Array<[string, string, (p: { size?: number; className?: string }) => JSX.Element]> = [
    ["move left / right / up / down", "Move the pointer 180 pixels", IconVoice],
    ["click", "Left click", IconGestureClick],
    ["double click", "Double click", IconGestureClick],
    ["right click", "Right click", IconGestureClick],
    ["scroll up / down", "Scroll four steps", IconVoice],
    ["open browser", "Open a blank page in the default browser", IconMonitor],
    ["new tab / close tab", "OS browser shortcuts", IconMonitor],
    ["click <visible words>", "Activate a control or click visible screen text", IconScanText],
    ["double click <visible words>", "Double-click a control, word, or folder label", IconScanText],
    ["right click <visible words>", "Right-click a visible control or word", IconScanText],
    ["move to <visible words>", "Move to a control or word without clicking", IconPointerRow],
    ["pause control", "Stop executing computer actions", IconShield],
    ["resume control", "Re-enable computer actions", IconShield],
  ];
  return (
    <section id="commands" className="py-12 md:py-24 px-4 md:px-8 border-b-4 border-ink bg-blue dot-grid">
      <div className="max-w-7xl mx-auto">
        <header className="mb-10 md:mb-16">
          <p className="font-bold uppercase tracking-widest text-sm mb-2 text-white">Grammar</p>
          <h2 className="text-4xl md:text-6xl font-black uppercase tracking-tighter text-white">
            The full vocabulary
          </h2>
          <p className="mt-4 max-w-2xl text-lg text-white/90 leading-relaxed">
            A deliberately small grammar: fewer phrases, fewer accidents. The same engine backs the live dashboard.
          </p>
        </header>
        <div className="bg-white border-4 border-ink shadow-hard-lg overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-ink text-white">
                <th className="px-4 py-3 text-xs font-bold uppercase tracking-widest">Spoken command</th>
                <th className="px-4 py-3 text-xs font-bold uppercase tracking-widest">Action</th>
                <th className="px-4 py-3 text-xs font-bold uppercase tracking-widest w-24 text-center">Channel</th>
              </tr>
            </thead>
            <tbody>
              {rows.map(([cmd, action, Icon], i) => (
                <tr key={cmd} className={i % 2 === 0 ? "bg-white" : "bg-muted/50"}>
                  <td className="px-4 py-3 font-mono text-sm border-t-2 border-ink/10">
                    <code className="bg-canvas border border-ink/20 px-1.5 py-0.5">{cmd}</code>
                  </td>
                  <td className="px-4 py-3 text-sm font-medium border-t-2 border-ink/10">{action}</td>
                  <td className="px-4 py-3 border-t-2 border-ink/10 text-center">
                    <Icon size={16} className="inline text-red" />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p className="mt-4 text-sm text-white/80">
          Matching ignores capitalization, spaces, and separators — <code>backend</code>, <code>back end</code>, and <code>BACK-END</code> are the same target — but stays spelling-sensitive: <code>project</code> never matches <strong>Projects</strong>.
        </p>
      </div>
    </section>
  );
}

function IconPointerRow(p: { size?: number; className?: string }) {
  return <IconGestureClick {...p} />;
}

/* ------------------------------------------------------------------ Architecture */

export function Architecture() {
  const diagrams = [
    { src: "/diagrams/system-architecture.png", alt: "Multimodal system architecture", caption: "Dual pipelines into a guarded action layer" },
    { src: "/diagrams/hardware-setup.png", alt: "Hardware setup schematic", caption: "Ordinary MacBook hardware only" },
    { src: "/diagrams/voice-architecture.png", alt: "Voice control architecture", caption: "Speech pipeline with isolated capture" },
    { src: "/diagrams/tongue-state-machine.png", alt: "Tongue click state machine", caption: "Complete out-and-retract gestures only" },
    { src: "/diagrams/methodology-workflow.png", alt: "Finalized methodology workflow", caption: "Nine-stage research methodology" },
  ];
  return (
    <section id="architecture" className="py-12 md:py-24 px-4 md:px-8 border-b-4 border-ink bg-canvas">
      <div className="max-w-7xl mx-auto">
        <header className="mb-10 md:mb-16">
          <p className="font-bold uppercase tracking-widest text-sm mb-2 text-blue">Design</p>
          <h2 className="text-4xl md:text-6xl font-black uppercase tracking-tighter">
            Architecture, documented
          </h2>
          <p className="mt-4 max-w-2xl text-lg leading-relaxed">
            Every diagram on this site is the real, reproducible output of the checked-in report scripts — not a mockup.
          </p>
        </header>
        <div className="grid md:grid-cols-2 gap-6">
          {diagrams.map((d, i) => (
            <figure key={d.src} className={`card-bauhaus p-4 ${i === 0 ? "md:col-span-2" : ""}`}>
              <span aria-hidden className={`absolute top-4 right-4 w-3 h-3 ${i % 3 === 0 ? "bg-red rounded-full" : i % 3 === 1 ? "bg-blue" : "bg-yellow triangle-up"}`} />
              <div className={`relative ${i === 0 ? "h-72 md:h-96" : "h-56"} border-2 border-ink bg-white`}>
                <Image src={d.src} alt={d.alt} fill className="object-contain" sizes="(max-width: 768px) 100vw, 50vw" />
              </div>
              <figcaption className="mt-3 text-sm font-bold uppercase tracking-wide flex items-center gap-2">
                <IconDoc size={14} /> {d.caption}
              </figcaption>
            </figure>
          ))}
        </div>
      </div>
    </section>
  );
}

/* ------------------------------------------------------------------ Safety */

export function Safety() {
  const rules = [
    "Starts paused; actions run only after “resume control” or the Enable button",
    "Dry-run mode recognizes and logs speech but never moves the cursor",
    "Slam the pointer into a screen corner to trigger the emergency failsafe",
    "Unmatched or ambiguous targets are rejected, never guessed",
    "Transcript text, labels, and text-entry fields are excluded from targeting",
    "A held tongue never repeats clicks — every click is a complete gesture",
    "Audio, video, OCR, and inference stay on the device",
    "Session logs record recognized text and outcomes, never raw media",
  ];
  return (
    <section className="py-12 md:py-24 px-4 md:px-8 border-b-4 border-ink bg-red dot-grid">
      <div className="max-w-7xl mx-auto">
        <header className="mb-10 md:mb-16">
          <p className="font-bold uppercase tracking-widest text-sm mb-2 text-white">Non-negotiables</p>
          <h2 className="text-4xl md:text-6xl font-black uppercase tracking-tighter text-white">
            Safety by design
          </h2>
        </header>
        <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {rules.map((rule, i) => (
            <div key={rule} className="bg-white border-2 border-ink p-4 shadow-hard flex flex-col gap-3">
              <span className={`w-8 h-8 shrink-0 flex items-center justify-center font-black ${i % 2 === 0 ? "bg-ink text-white rounded-full" : "bg-yellow text-ink"}`}>
                {i + 1}
              </span>
              <p className="text-sm font-medium leading-relaxed">{rule}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

/* ------------------------------------------------------------------ Evaluation */

export function Evaluation() {
  return (
    <section id="evaluation" className="py-12 md:py-24 px-4 md:px-8 border-b-4 border-ink bg-white">
      <div className="max-w-7xl mx-auto grid lg:grid-cols-2 gap-10 items-center">
        <div>
          <p className="font-bold uppercase tracking-widest text-sm mb-2 text-red">Measurement</p>
          <h2 className="text-4xl md:text-6xl font-black uppercase tracking-tighter">
            Guided evaluation
          </h2>
          <p className="mt-4 text-lg leading-relaxed">
            The app ships a built-in guided evaluation: it prompts one command per trial,
            never executes actions, and exports a CSV with expected vs. recognized text,
            per-trial correctness, response time, and summary accuracy.
          </p>
          <ul className="mt-6 space-y-3">
            {[
              "Twelve-second timeout per trial",
              "Expected command, recognized text, matched command, response time",
              "Overall accuracy and average response seconds",
              "Repeat under quiet and noisy conditions and compare the CSVs",
            ].map((p) => (
              <li key={p} className="flex gap-3 items-baseline">
                <IconActivity size={16} className="text-blue shrink-0 mt-1" />
                <span className="text-base">{p}</span>
              </li>
            ))}
          </ul>
        </div>
        <div className="code-block shadow-hard">
          <p className="text-yellow font-bold uppercase tracking-widest text-xs mb-3">
            evaluation_results/ · CSV export
          </p>
          <pre className="whitespace-pre-wrap">{`target_command,recognized_text,matched_command,correct,response_time_seconds
Move left,   please move left, Move left,       True,   2.31
Click,       click,           Click,           True,   1.88
Scroll down, sroll down,      Scroll down,     True,   3.05
Open browser,,                Unrecognized,    False, 12.000

summary_metric,value
total_trials,12
correct_trials,3
accuracy_percent,25.000
average_response_seconds,4.7`}</pre>
        </div>
      </div>
    </section>
  );
}

/* ------------------------------------------------------------------ Get started */

export function GetStarted() {
  return (
    <section id="get-started" className="py-12 md:py-24 px-4 md:px-8 border-b-4 border-ink bg-canvas">
      <div className="max-w-7xl mx-auto">
        <header className="mb-10 md:mb-14">
          <p className="font-bold uppercase tracking-widest text-sm mb-2 text-blue">Run it</p>
          <h2 className="text-4xl md:text-6xl font-black uppercase tracking-tighter">
            Get started
          </h2>
          <p className="mt-4 max-w-2xl text-lg leading-relaxed">
            Python 3.10+ and an Apple Silicon MacBook. The models are pretrained —
            no training data, no API keys, no extra devices. The website dashboard is
            the easiest way to drive the engine; the desktop app remains available.
          </p>
        </header>

        <div className="grid lg:grid-cols-2 gap-10 items-start">
          {/* Steps */}
          <ol className="space-y-4">
            {[
              {
                icon: IconClone,
                title: "1 · Get the repository",
                body: "Star it, fork it, or clone it. Create a project folder and clone into it:",
              },
              {
                icon: IconTerminal,
                title: "2 · Install the dependencies",
                body: "A venv and pip install -e . is all it takes. Node is only needed to rebuild the website.",
              },
              {
                icon: IconShield,
                title: "3 · Grant macOS permissions",
                body: "Microphone, Camera, Accessibility, and Screen Recording — for your terminal app. One-time setup, same as any assistive tool.",
              },
              {
                icon: IconPlay,
                title: "4 · Start the website",
                body: "One command runs the engine and opens the dashboard. The website automatically connects to whatever you started — just speak:",
              },
            ].map((s) => (
              <li key={s.title} className="flex gap-4 items-start border-2 border-ink bg-white p-4 shadow-hard-sm">
                <span className="w-11 h-11 shrink-0 bg-red text-white border-2 border-ink flex items-center justify-center">
                  <s.icon size={22} />
                </span>
                <div>
                  <h3 className="font-black uppercase tracking-tight">{s.title}</h3>
                  <p className="text-sm mt-1 leading-relaxed">{s.body}</p>
                </div>
              </li>
            ))}
          </ol>

          {/* Terminal */}
          <div className="code-block shadow-hard-lg lg:sticky lg:top-24">
            <p className="text-yellow font-bold uppercase tracking-widest text-xs mb-3">terminal</p>
            <pre className="whitespace-pre-wrap leading-relaxed">{`# 1 — get the repository
mkdir ~/projects && cd ~/projects
git clone https://github.com/UtkarsHMer05/\\
AI-Multimodal-Hands-Free-Computer-Interface.git
cd AI-Multimodal-Hands-Free-Computer-Interface

# 2 — install the dependencies
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .

# 3 — grant macOS permissions (one-time)
#  System Settings → Privacy & Security:
#  Microphone · Camera · Accessibility ·
#  Screen & System Audio Recording → Terminal

# 4 — start the website (engine + dashboard)
./run_website.command
# → opens http://localhost:8757/dashboard
#   press Enable control → Start listening

# Prefer the desktop app instead?
./run_live.command

# Run the test suite
python -m unittest discover -s tests -v`}</pre>
          </div>
        </div>

        {/* What you can say — ties back to the dashboard */}
        <div className="mt-10 border-4 border-ink bg-yellow shadow-hard-lg p-6">
          <div className="flex flex-wrap items-center gap-4 justify-between">
            <div>
              <h3 className="font-black uppercase tracking-tight text-xl">
                Once it&rsquo;s running, just speak
              </h3>
              <p className="mt-1 text-sm font-medium max-w-2xl">
                &ldquo;resume control&rdquo; · &ldquo;move left&rdquo; · &ldquo;click
                Submit&rdquo; · &ldquo;double click Sign In&rdquo; · &ldquo;pause
                control&rdquo; — the dashboard shows every transcript, action,
                and safety refusal live.
              </p>
            </div>
            <a href="/dashboard/" className="btn-bauhaus btn-bauhaus-md bg-red text-white shrink-0">
              Open the dashboard <IconArrowRight size={18} />
            </a>
          </div>
        </div>
      </div>
    </section>
  );
}

/* ------------------------------------------------------------------ FAQ */

export function FAQ() {
  const [openIndex, setOpenIndex] = useState<number | null>(0);
  const faqs = [
    {
      q: "Does anything leave my computer?",
      a: "No. Speech runs on Parakeet TDT 0.6B v3 (Core ML) or Vosk, face landmarks on MediaPipe, text recognition on Tesseract — all locally. No audio, video, frames, or transcripts are uploaded. The 3.6 MB MediaPipe model downloads once into .models/.",
    },
    {
      q: "Do I need any special hardware?",
      a: "No EEG headset, infrared eye tracker, depth camera, glove, or wearable. A MacBook with its built-in microphone and FaceTime camera is the entire BOM.",
    },
    {
      q: "What stops it from clicking things by accident?",
      a: "A constrained grammar, a pause-by-default start, consecutive-frame confirmation for gestures, cooldowns, per-user calibrated thresholds, a movement dead zone, and a hard rule: unmatched or ambiguous targets are refused rather than guessed.",
    },
    {
      q: "Why does “click project” not select the Projects folder?",
      a: "Matching is spelling-sensitive by design. backend, back end, and BACK-END are the same target because they differ only by separators — but project and projects are genuinely different words, so the singular command refuses instead of guessing. Known Finder labels are additionally protected from OCR misreads.",
    },
    {
      q: "How do tongue and blink clicks avoid false alarms?",
      a: "Each requires a complete out-and-retract (or close-and-reopen) cycle — holding never repeats. Sequences are aggregated in a ~0.7 s window so one, two, and three gestures map to single, double, and triple clicks; a cooldown prevents duplicate simultaneous detections.",
    },
    {
      q: "Is eye gaze precise enough for real work?",
      a: "It is an estimate from an ordinary RGB camera, not a medical or infrared tracker. Good lighting, stable posture, and recalibration improve it; this is documented as a limitation rather than oversold.",
    },
    {
      q: "What's the difference between the website and the desktop app?",
      a: "Same engine, two front-ends. The desktop app (run_live.command) is the Tk interface. The website dashboard (run_website.command) runs the identical engine headless and controls it from the browser — voice, head/gaze, tongue and blink, with live telemetry. Browsers cannot move a real pointer themselves, so the dashboard talks to the local Python engine that can.",
    },
  ];
  return (
    <section id="faq" className="py-12 md:py-24 px-4 md:px-8 border-b-4 border-ink bg-white">
      <div className="max-w-4xl mx-auto">
        <header className="mb-10">
          <p className="font-bold uppercase tracking-widest text-sm mb-2 text-yellow">FAQ</p>
          <h2 className="text-4xl md:text-6xl font-black uppercase tracking-tighter">Questions</h2>
        </header>
        <div className="space-y-4">
          {faqs.map((f, i) => {
            const isOpen = openIndex === i;
            return (
              <div
                key={f.q}
                className={`border-4 border-ink shadow-hard transition-colors ${isOpen ? "bg-red" : "bg-white"}`}
              >
                <button
                  className="w-full flex items-center justify-between gap-4 px-5 py-4 text-left"
                  onClick={() => setOpenIndex(isOpen ? null : i)}
                  aria-expanded={isOpen}
                >
                  <span className={`font-black uppercase tracking-tight text-base md:text-lg ${isOpen ? "text-white" : ""}`}>
                    {f.q}
                  </span>
                  <IconChevronDown size={20} className={`shrink-0 transition-transform duration-200 ${isOpen ? "rotate-180 text-white" : ""}`} />
                </button>
                <div
                  className={`grid transition-[grid-template-rows] duration-300 ease-out ${isOpen ? "grid-rows-[1fr]" : "grid-rows-[0fr]"}`}
                >
                  <div className="overflow-hidden">
                    <div className="bg-yellow-soft border-t-4 border-ink px-5 py-4 text-base leading-relaxed">
                      {f.a}
                    </div>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}

/* ------------------------------------------------------------------ Footer */

export function Footer() {
  return (
    <footer className="bg-ink text-white">
      <div className="max-w-7xl mx-auto px-4 md:px-8 py-12 grid gap-10 md:grid-cols-3">
        <div>
          <div className="flex items-center gap-2 mb-4">
            <span className="w-4 h-4 rounded-full bg-red" aria-hidden />
            <span className="w-3.5 h-3.5 bg-blue" aria-hidden />
            <span className="w-4 h-4 triangle-up bg-yellow" aria-hidden />
            <span className="font-black uppercase tracking-tighter text-xl ml-1">
              Voice<span className="text-red">Cursor</span>
            </span>
          </div>
          <p className="text-sm text-white/70 leading-relaxed">
            An offline-first multimodal hands-free computer interface. DA1 project:
            voice-based control of computer actions, extended with camera-based
            assistive interaction.
          </p>
        </div>
        <div>
          <p className="text-xs font-bold uppercase tracking-widest text-yellow mb-4">Project</p>
          <ul className="space-y-2 text-sm font-medium">
            <li><a className="hover:text-yellow inline-flex items-center gap-2" href={REPO_URL} target="_blank" rel="noreferrer"><IconCode size={14} /> GitHub repository</a></li>
            <li><a className="hover:text-yellow" href="/dashboard/">Live dashboard</a></li>
            <li><a className="hover:text-yellow" href="#commands">Command grammar</a></li>
            <li><a className="hover:text-yellow" href="#evaluation">Evaluation method</a></li>
          </ul>
        </div>
        <div>
          <p className="text-xs font-bold uppercase tracking-widest text-yellow mb-4">Research context</p>
          <ul className="space-y-2 text-xs text-white/70 leading-relaxed">
            <li>Deshmukh & Chalmeta — UX & Usability of Voice User Interfaces (2024)</li>
            <li>Clark et al. — The State of Speech in HCI (2019)</li>
            <li>Ramos et al. — Low-Cost HMI with Facial Landmarks & Voice (2022)</li>
          </ul>
        </div>
      </div>
      <div className="border-t-2 border-white/20">
        <div className="max-w-7xl mx-auto px-4 md:px-8 py-4 flex flex-wrap gap-3 justify-between text-xs text-white/50 font-bold uppercase tracking-widest">
          <span>Built with Next.js · TypeScript · Tailwind</span>
          <span>Runs entirely on your Mac</span>
        </div>
      </div>
    </footer>
  );
}
