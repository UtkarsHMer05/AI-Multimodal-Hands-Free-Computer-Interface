"use client";

/**
 * /dashboard — the live control surface for the real Voice Cursor engine.
 *
 * Connects to the local Python engine (voice_cursor/web_server.py, started
 * by ./run_website.command) over a WebSocket at ws://localhost:8757/bridge
 * and mirrors the Tk application's controls:
 *
 *  - continuous voice recognition (Parakeet/Vosk, exactly as the desktop app)
 *  - head tracking and eye-gaze pointer control
 *  - tongue and blink click calibration
 *  - enable/pause safety state, transcript, feedback, camera/tongue/blink
 *    status lines, click-ring feedback, and the session log
 *
 * Commands sent from here execute on the Mac through the same guarded
 * ActionExecutor used by the Tk app: the real pointer moves, real controls
 * get clicked, and the real numbered click rings appear on screen.
 */

import { useCallback, useEffect, useRef, useState } from "react";
import {
  IconMic, IconMicOff, IconCamera, IconCameraOff, IconPause, IconPlay,
  IconRecalibrate, IconKeyboard, IconAlert, IconShield, IconActivity,
  IconGaze, IconEyeOff, IconWifi, IconWifiOff,
} from "@/components/icons";
import Link from "next/link";

const BRIDGE_URL = "ws://localhost:8757/bridge";

interface ServerMessage {
  kind: string;
  [key: string]: unknown;
}

interface LogRow {
  time: string;
  message: string;
}

interface ClickRing {
  key: number;
  action: string;
  x: number;
  y: number;
}

export default function DashboardPage() {
  const [connected, setConnected] = useState(false);
  const [paused, setPaused] = useState(true);
  const [listening, setListening] = useState(false);
  const [cameraRunning, setCameraRunning] = useState(false);
  const [cameraMode, setCameraMode] = useState<"head" | "gaze" | null>(null);
  const [transcript, setTranscript] = useState("");
  const [feedback, setFeedback] = useState("Connecting to the Voice Cursor engine…");
  const [status, setStatus] = useState("—");
  const [cameraStatus, setCameraStatus] = useState("Camera control is off");
  const [tongueStatus, setTongueStatus] = useState("Tongue clicks are off");
  const [blinkStatus, setBlinkStatus] = useState("Blink clicks are off");
  const [logs, setLogs] = useState<LogRow[]>([]);
  const [typed, setTyped] = useState("");
  const [rings, setRings] = useState<ClickRing[]>([]);
  const wsRef = useRef<WebSocket | null>(null);
  const ringKey = useRef(0);

  const send = useCallback((kind: string, extra: Record<string, unknown> = {}) => {
    const ws = wsRef.current;
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({ kind, ...extra }));
    }
  }, []);

  useEffect(() => {
    let ws: WebSocket;
    let closed = false;
    let retry: ReturnType<typeof setTimeout> | null = null;

    const connect = () => {
      ws = new WebSocket(BRIDGE_URL);
      wsRef.current = ws;

      ws.onopen = () => setConnected(true);

      ws.onmessage = (event) => {
        let m: ServerMessage;
        try {
          m = JSON.parse(event.data as string);
        } catch {
          return;
        }
        switch (m.kind) {
          case "snapshot":
            setPaused(Boolean(m.paused));
            setListening(Boolean(m.listening));
            setCameraRunning(Boolean(m.camera_running));
            setCameraMode((m.camera_mode as "head" | "gaze" | null) ?? null);
            setTranscript(String(m.transcript ?? ""));
            setFeedback(String(m.feedback ?? ""));
            setStatus(String(m.status ?? "—"));
            setLogs((m.logs as unknown as [string, string][])?.map(([time, message]) => ({ time, message })) ?? []);
            break;
          case "transcript":
            setTranscript(String(m.text ?? ""));
            break;
          case "feedback":
            setFeedback(String(m.message ?? ""));
            break;
          case "status":
            setStatus(String(m.message ?? ""));
            break;
          case "paused":
            setPaused(Boolean(m.paused));
            break;
          case "listening":
            setListening(Boolean(m.listening));
            break;
          case "camera_running":
            setCameraRunning(Boolean(m.running));
            break;
          case "camera_status":
            setCameraStatus(String(m.message ?? ""));
            break;
          case "tongue_status":
            setTongueStatus(String(m.message ?? ""));
            break;
          case "blink_status":
            setBlinkStatus(String(m.message ?? ""));
            break;
          case "log":
            setLogs((prev) => [{ time: String(m.time), message: String(m.message) }, ...prev].slice(0, 40));
            break;
          case "click_feedback": {
            ringKey.current += 1;
            const ring = {
              key: ringKey.current,
              action: String(m.action),
              x: Number(m.x),
              y: Number(m.y),
            };
            setRings((prev) => [...prev.slice(-5), ring]);
            setTimeout(() => setRings((prev) => prev.filter((r) => r.key !== ring.key)), 900);
            break;
          }
        }
      };

      ws.onclose = () => {
        setConnected(false);
        if (!closed) {
          retry = setTimeout(connect, 1500);
        }
      };
      ws.onerror = () => ws.close();
    };

    connect();
    return () => {
      closed = true;
      if (retry) clearTimeout(retry);
      wsRef.current?.close();
    };
  }, []);

  const runTyped = () => {
    if (!typed.trim()) return;
    send("text", { text: typed.trim() });
    setTyped("");
  };

  return (
    <main id="main" className="min-h-screen bg-canvas">
      {/* Top bar */}
      <header className="sticky top-0 z-40 bg-ink text-white border-b-4 border-ink">
        <div className="max-w-7xl mx-auto px-4 md:px-8 py-3 flex items-center gap-4 flex-wrap">
          <Link href="/" className="font-black uppercase tracking-tighter text-lg">
            Voice<span className="text-red">Cursor</span>
          </Link>
          <span className="text-xs font-bold uppercase tracking-widest text-yellow">
            Live Dashboard
          </span>
          <div className="ml-auto flex items-center gap-3 text-xs font-bold uppercase tracking-widest">
            <span className={`inline-flex items-center gap-1.5 px-2 py-1 border-2 ${connected ? "bg-blue border-white/40" : "bg-red border-white/40"}`}>
              {connected ? <IconWifi size={13} /> : <IconWifiOff size={13} />}
              {connected ? "Engine connected" : "Engine offline"}
            </span>
            <span className={`inline-flex items-center gap-1.5 px-2 py-1 border-2 border-white/40 ${paused ? "bg-yellow text-ink" : "bg-[#30c030] text-white"}`}>
              <IconActivity size={13} />
              {paused ? "Paused" : "Enabled"}
            </span>
            <Link href="/" className="px-2 py-1 border-2 border-white/40 hover:bg-white hover:text-ink">
              ← Site
            </Link>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 md:px-8 py-8 space-y-6">
        {/* Connection banner */}
        {!connected && (
          <div className="border-4 border-ink bg-yellow-soft p-4 flex gap-3 items-start shadow-hard">
            <IconAlert size={22} className="text-red shrink-0 mt-0.5" />
            <div className="text-sm font-medium leading-relaxed">
              <p className="font-black uppercase tracking-tight">Engine not running</p>
              <p className="mt-1">
                This dashboard controls the real Voice Cursor engine on this Mac. Start it
                by double-clicking <code className="bg-white border border-ink/30 px-1">run_website.command</code>{" "}
                in the project folder, or run{" "}
                <code className="bg-white border border-ink/30 px-1">python -m voice_cursor.web_server</code>.
                Retrying automatically…
              </p>
            </div>
          </div>
        )}

        {/* Control deck */}
        <section className="grid lg:grid-cols-[1fr_380px] gap-6 items-start">
          {/* Left: primary controls */}
          <div className="space-y-4">
            {/* Enable / Listen / Camera */}
            <div className="border-4 border-ink bg-white shadow-hard-lg p-5">
              <h2 className="font-black uppercase tracking-tighter text-2xl mb-4">
                Control deck
              </h2>
              <div className="flex flex-wrap gap-3">
                {paused ? (
                  <button onClick={() => send("enable")} className="btn-bauhaus btn-bauhaus-md bg-[#30c030] text-white">
                    <IconPlay size={18} /> Enable control
                  </button>
                ) : (
                  <button onClick={() => send("pause")} className="btn-bauhaus btn-bauhaus-md bg-yellow text-ink">
                    <IconPause size={18} /> Pause control
                  </button>
                )}
                {listening ? (
                  <button onClick={() => send("listen_stop")} className="btn-bauhaus btn-bauhaus-md bg-ink text-white">
                    <IconMicOff size={18} /> Stop listening
                  </button>
                ) : (
                  <button onClick={() => send("listen_start")} className="btn-bauhaus btn-bauhaus-md bg-red text-white">
                    <IconMic size={18} /> Start listening
                  </button>
                )}
              </div>
              <p className="mt-3 text-xs font-bold uppercase tracking-widest text-ink/50">
                Voice runs Parakeet/Vosk on this Mac — same engine as the desktop app
              </p>
            </div>

            {/* Camera */}
            <div className="border-4 border-ink bg-white shadow-hard-lg p-5">
              <h2 className="font-black uppercase tracking-tighter text-2xl mb-4">
                Camera pointer
              </h2>
              {cameraRunning ? (
                <div className="flex flex-wrap gap-3">
                  <button onClick={() => send("camera_stop")} className="btn-bauhaus btn-bauhaus-sm bg-ink text-white">
                    <IconCameraOff size={16} /> Stop camera
                  </button>
                  <button onClick={() => send("camera_recalibrate")} className="btn-bauhaus btn-bauhaus-sm bg-white text-ink">
                    <IconRecalibrate size={16} /> Recalibrate
                  </button>
                </div>
              ) : (
                <div className="flex flex-wrap gap-3">
                  <button onClick={() => send("camera_start", { mode: "head" })} className="btn-bauhaus btn-bauhaus-sm bg-blue text-white">
                    <IconCamera size={16} /> Start head tracking
                  </button>
                  <button onClick={() => send("camera_start", { mode: "gaze" })} className="btn-bauhaus btn-bauhaus-sm bg-blue text-white">
                    <IconGaze size={16} /> Start eye gaze
                  </button>
                </div>
              )}
              <p className="mt-3 text-sm font-medium border-2 border-ink/20 bg-canvas px-3 py-2">
                {cameraStatus}
                {cameraMode && cameraRunning && (
                  <span className="ml-2 text-xs font-bold uppercase text-blue">
                    ({cameraMode === "head" ? "head" : "gaze"} mode)
                  </span>
                )}
              </p>
            </div>

            {/* Tongue & blink */}
            <div className="grid sm:grid-cols-2 gap-4">
              <div className="border-4 border-ink bg-white shadow-hard p-4">
                <h3 className="font-black uppercase tracking-tight mb-3">Tongue clicks</h3>
                <div className="flex flex-wrap gap-2">
                  <button onClick={() => send("tongue_calibrate")} className="btn-bauhaus btn-bauhaus-sm bg-red text-white">
                    Calibrate
                  </button>
                  <button onClick={() => send("tongue_disable")} className="btn-bauhaus btn-bauhaus-sm bg-white text-ink">
                    <IconEyeOff size={14} /> Disable
                  </button>
                </div>
                <p className="mt-3 text-xs font-medium text-ink/70">{tongueStatus}</p>
              </div>
              <div className="border-4 border-ink bg-white shadow-hard p-4">
                <h3 className="font-black uppercase tracking-tight mb-3">Blink clicks</h3>
                <div className="flex flex-wrap gap-2">
                  <button onClick={() => send("blink_calibrate")} className="btn-bauhaus btn-bauhaus-sm bg-red text-white">
                    Calibrate
                  </button>
                  <button onClick={() => send("blink_disable")} className="btn-bauhaus btn-bauhaus-sm bg-white text-ink">
                    <IconEyeOff size={14} /> Disable
                  </button>
                </div>
                <p className="mt-3 text-xs font-medium text-ink/70">{blinkStatus}</p>
              </div>
            </div>

            {/* Session log */}
            <div className="border-4 border-ink bg-white shadow-hard p-5">
              <h2 className="font-black uppercase tracking-tighter text-xl mb-3 flex items-center gap-2">
                <IconShield size={20} /> Session log
              </h2>
              <div className="max-h-64 overflow-y-auto text-xs font-mono space-y-1">
                {logs.length === 0 ? (
                  <p className="text-ink/40">No entries yet.</p>
                ) : (
                  logs.map((l, i) => (
                    <div key={i} className="flex gap-2 items-baseline">
                      <span className="text-ink/50">{l.time}</span>
                      <span className="flex-1">{l.message}</span>
                    </div>
                  ))
                )}
              </div>
            </div>
          </div>

          {/* Right: live telemetry */}
          <div className="space-y-4 lg:sticky lg:top-24">
            {/* Transcript */}
            <div className="border-4 border-ink bg-white shadow-hard p-4">
              <p className="text-[10px] font-bold uppercase tracking-widest text-ink/60 mb-1">Transcript</p>
              <p className="font-mono text-sm min-h-[24px]">
                {transcript || <span className="text-ink/40">—</span>}
              </p>
              {listening && (
                <p className="mt-2 inline-flex items-center gap-2 text-xs font-bold uppercase tracking-widest text-red">
                  <span className="w-2 h-2 rounded-full bg-red pulse-dot" /> Listening
                </p>
              )}
            </div>

            {/* Feedback */}
            <div className="border-4 border-ink bg-yellow-soft shadow-hard p-4">
              <p className="text-[10px] font-bold uppercase tracking-widest text-ink/60 mb-1">Feedback</p>
              <p className="text-sm font-medium min-h-[24px]">{feedback}</p>
            </div>

            {/* Engine status */}
            <div className="border-4 border-ink bg-ink text-white shadow-hard p-4">
              <p className="text-[10px] font-bold uppercase tracking-widest text-yellow mb-1">Speech engine</p>
              <p className="text-sm font-medium min-h-[24px]">{status}</p>
              <p className="mt-3 text-[10px] font-bold uppercase tracking-widest text-yellow mb-1">Click feedback</p>
              <div className="min-h-[28px] flex flex-wrap gap-2">
                {rings.length === 0 ? (
                  <span className="text-xs text-white/40">Clicks appear here</span>
                ) : (
                  rings.map((r) => (
                    <span
                      key={r.key}
                      className="inline-flex items-center gap-1 text-xs font-black border-2 border-white/50 px-2 py-0.5"
                    >
                      {r.action} @ ({r.x},{r.y})
                    </span>
                  ))
                )}
              </div>
            </div>

            {/* Typed command */}
            <div className="border-4 border-ink bg-white shadow-hard p-4">
              <label htmlFor="demo-command" className="flex items-center gap-2 text-xs font-bold uppercase tracking-widest mb-2">
                <IconKeyboard size={14} /> Typed command
              </label>
              <form
                onSubmit={(e) => {
                  e.preventDefault();
                  runTyped();
                }}
              >
                <input
                  id="demo-command"
                  value={typed}
                  onChange={(e) => setTyped(e.target.value)}
                  placeholder="e.g. click Submit"
                  className="w-full border-2 border-ink px-3 py-2 font-mono text-sm bg-canvas focus:outline-none focus:ring-2 ring-yellow"
                  autoComplete="off"
                />
                <button type="submit" className="btn-bauhaus btn-bauhaus-sm bg-blue text-white mt-3 w-full">
                  Send to engine
                </button>
              </form>
              <div className="mt-3 flex flex-wrap gap-2">
                {["resume control", "click", "move left", "pause control"].map((c) => (
                  <button
                    key={c}
                    onClick={() => send("text", { text: c })}
                    className="text-xs font-mono border-2 border-ink/40 px-2 py-1 hover:bg-yellow transition-colors"
                  >
                    {c}
                  </button>
                ))}
              </div>
            </div>
          </div>
        </section>
      </div>
    </main>
  );
}
