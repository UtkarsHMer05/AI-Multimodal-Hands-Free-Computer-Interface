/**
 * Hand-drawn geometric SVG icons for the landing page.
 *
 * Deliberately NOT an icon library: every mark is pure inline SVG built from
 * circles, squares, triangles, and hard strokes — Bauhaus primitives that
 * render identically everywhere and cannot be affected by icon-package
 * version quirks. Each accepts a size and uses currentColor.
 */

interface IconProps {
  size?: number;
  className?: string;
  strokeWidth?: number;
}

function svgProps({ size = 24, className = "", strokeWidth = 2.5 }: IconProps) {
  return {
    width: size,
    height: size,
    viewBox: "0 0 24 24",
    fill: "none",
    stroke: "currentColor",
    strokeWidth,
    strokeLinecap: "round" as const,
    strokeLinejoin: "round" as const,
    className,
    "aria-hidden": true,
  };
}

/** Voice — sound waves radiating from a mouth/circle */
export function IconVoice(props: IconProps) {
  return (
    <svg {...svgProps(props)}>
      <circle cx="12" cy="12" r="3.5" fill="currentColor" stroke="none" />
      <path d="M3 12a9 9 0 0 1 4-7.5" />
      <path d="M3 12a9 9 0 0 0 4 7.5" />
      <path d="M21 12a9 9 0 0 0-4-7.5" />
      <path d="M21 12a9 9 0 0 1-4 7.5" />
    </svg>
  );
}

/** Head tracking — head square with direction arrows */
export function IconHead(props: IconProps) {
  return (
    <svg {...svgProps(props)}>
      <circle cx="12" cy="12" r="4.5" fill="currentColor" stroke="none" />
      <path d="M12 4V1.5" />
      <path d="M12 22.5V20" />
      <path d="M4 12H1.5" />
      <path d="M22.5 12H20" />
      <path d="M6.3 6.3 4.6 4.6" />
      <path d="M17.7 17.7l1.7 1.7" />
      <path d="M6.3 17.7 4.6 19.4" />
      <path d="M17.7 6.3l1.7-1.7" />
    </svg>
  );
}

/** Eye gaze — eye with iris */
export function IconGaze(props: IconProps) {
  return (
    <svg {...svgProps(props)}>
      <path d="M2 12s3.5-6.5 10-6.5S22 12 22 12s-3.5 6.5-10 6.5S2 12 2 12Z" />
      <circle cx="12" cy="12" r="3" fill="currentColor" stroke="none" />
    </svg>
  );
}

/** Gesture click — cursor with click burst */
export function IconGestureClick(props: IconProps) {
  return (
    <svg {...svgProps(props)}>
      <path d="M6 3v4" />
      <path d="M3 6h4" />
      <path d="M6 21l14-8.5-8.5-2L6 3v18Z" fill="currentColor" />
    </svg>
  );
}

/** Numbered click ring — the app's signature feedback */
export function IconClickRing(props: IconProps) {
  return (
    <svg {...svgProps(props)}>
      <circle cx="12" cy="12" r="9" />
      <circle cx="12" cy="12" r="3.5" fill="currentColor" stroke="none" />
    </svg>
  );
}

/** Audio waveform — capture stage */
export function IconWaveform(props: IconProps) {
  return (
    <svg {...svgProps(props)}>
      <path d="M3 12h2" />
      <path d="M7 8v8" />
      <path d="M11 4v16" />
      <path d="M15 7v10" />
      <path d="M19 10v4" />
    </svg>
  );
}

/** Brain/chip — local inference */
export function IconChip(props: IconProps) {
  return (
    <svg {...svgProps(props)}>
      <rect x="5" y="5" width="14" height="14" />
      <rect x="9.5" y="9.5" width="5" height="5" fill="currentColor" stroke="none" />
      <path d="M9 2v3" />
      <path d="M15 2v3" />
      <path d="M9 19v3" />
      <path d="M15 19v3" />
      <path d="M2 9h3" />
      <path d="M2 15h3" />
      <path d="M19 9h3" />
      <path d="M19 15h3" />
    </svg>
  );
}

/** Scan text — resolution stage */
export function IconScanText(props: IconProps) {
  return (
    <svg {...svgProps(props)}>
      <path d="M4 8V5a1 1 0 0 1 1-1h3" />
      <path d="M20 8V5a1 1 0 0 0-1-1h-3" />
      <path d="M4 16v3a1 1 0 0 0 1 1h3" />
      <path d="M20 16v3a1 1 0 0 1-1 1h-3" />
      <path d="M8 10h8" />
      <path d="M8 14h5" />
    </svg>
  );
}

/** Guarded action — shield with bolt */
export function IconShieldBolt(props: IconProps) {
  return (
    <svg {...svgProps(props)}>
      <path d="M12 2 4 5v6c0 5 3.5 8.5 8 11 4.5-2.5 8-6 8-11V5l-8-3Z" />
      <path d="M13 7l-3 5h4l-3 5" />
    </svg>
  );
}

/** Shield — safety */
export function IconShield(props: IconProps) {
  return (
    <svg {...svgProps(props)}>
      <path d="M12 2 4 5v6c0 5 3.5 8.5 8 11 4.5-2.5 8-6 8-11V5l-8-3Z" />
      <path d="m8.5 12 2.5 2.5 4.5-5" />
    </svg>
  );
}

/** Lock — offline privacy */
export function IconLock(props: IconProps) {
  return (
    <svg {...svgProps(props)}>
      <rect x="4" y="10" width="16" height="11" />
      <path d="M8 10V7a4 4 0 0 1 8 0v3" />
      <circle cx="12" cy="15.5" r="1.6" fill="currentColor" stroke="none" />
    </svg>
  );
}

/** Check mark */
export function IconCheck(props: IconProps) {
  return (
    <svg {...svgProps(props)}>
      <path d="M4 12.5 9.5 18 20 6.5" />
    </svg>
  );
}

/** Terminal prompt */
export function IconTerminal(props: IconProps) {
  return (
    <svg {...svgProps(props)}>
      <path d="M5 8l4 4-4 4" />
      <path d="M13 16h6" />
    </svg>
  );
}

/** Download/clone — repo step */
export function IconClone(props: IconProps) {
  return (
    <svg {...svgProps(props)}>
      <rect x="3" y="3" width="10" height="10" />
      <rect x="11" y="11" width="10" height="10" />
    </svg>
  );
}

/** Play — enable */
export function IconPlay(props: IconProps) {
  return (
    <svg {...svgProps(props)}>
      <path d="M7 4.5 19 12 7 19.5V4.5Z" fill="currentColor" />
    </svg>
  );
}

/** Monitor / dashboard */
export function IconMonitor(props: IconProps) {
  return (
    <svg {...svgProps(props)}>
      <rect x="2.5" y="4" width="19" height="12.5" />
      <path d="M9 20.5h6" />
      <path d="M12 16.5v4" />
    </svg>
  );
}

/** Activity pulse */
export function IconActivity(props: IconProps) {
  return (
    <svg {...svgProps(props)}>
      <path d="M2 12h5l2.5-7 4 14L16 12h6" />
    </svg>
  );
}

/** Document */
export function IconDoc(props: IconProps) {
  return (
    <svg {...svgProps(props)}>
      <path d="M6 2h8l4 4v16H6V2Z" />
      <path d="M14 2v4h4" />
      <path d="M9 12h6" />
      <path d="M9 16h6" />
    </svg>
  );
}

/** Chevron down — FAQ */
export function IconChevronDown(props: IconProps) {
  return (
    <svg {...svgProps(props)}>
      <path d="m5 9 7 7 7-7" />
    </svg>
  );
}

/** Arrow right — CTAs */
export function IconArrowRight(props: IconProps) {
  return (
    <svg {...svgProps(props)}>
      <path d="M4 12h16" />
      <path d="m13 5 7 7-7 7" />
    </svg>
  );
}

/** Close X */
export function IconX(props: IconProps) {
  return (
    <svg {...svgProps(props)}>
      <path d="M5 5l14 14" />
      <path d="M19 5 5 19" />
    </svg>
  );
}

/** Code / source */
export function IconCode(props: IconProps) {
  return (
    <svg {...svgProps(props)}>
      <path d="m8 6-6 6 6 6" />
      <path d="m16 6 6 6-6 6" />
    </svg>
  );
}

/** Menu — mobile nav */
export function IconMenu(props: IconProps) {
  return (
    <svg {...svgProps(props)}>
      <path d="M3 6h18" />
      <path d="M3 12h18" />
      <path d="M3 18h18" />
    </svg>
  );
}

/** Eye */
export function IconEye(props: IconProps) {
  return (
    <svg {...svgProps(props)}>
      <path d="M2 12s3.5-6.5 10-6.5S22 12 22 12s-3.5 6.5-10 6.5S2 12 2 12Z" />
      <circle cx="12" cy="12" r="3" />
    </svg>
  );
}

/** Mouse pointer */
export function IconPointer(props: IconProps) {
  return (
    <svg {...svgProps(props)}>
      <path d="M6 3v18l4-4.5 3 1.5L6 3Z" fill="currentColor" />
    </svg>
  );
}

/** Wifi — engine connection */
export function IconWifi(props: IconProps) {
  return (
    <svg {...svgProps(props)}>
      <path d="M2 8.5a15 15 0 0 1 20 0" />
      <path d="M5.5 12a10 10 0 0 1 13 0" />
      <path d="M9 15.5a5 5 0 0 1 6 0" />
      <circle cx="12" cy="19.5" r="1.4" fill="currentColor" stroke="none" />
    </svg>
  );
}

/** Wifi off — engine offline */
export function IconWifiOff(props: IconProps) {
  return (
    <svg {...svgProps(props)}>
      <path d="M2 8.5a15 15 0 0 1 6-3.7" />
      <path d="M16 4.8a15 15 0 0 1 6 3.7" />
      <path d="M5.5 12a10 10 0 0 1 3-2" />
      <path d="M15.5 10a10 10 0 0 1 3 2" />
      <path d="M9 15.5a5 5 0 0 1 3.5-1.2" />
      <circle cx="12" cy="19.5" r="1.4" fill="currentColor" stroke="none" />
      <path d="M3 3l18 18" />
    </svg>
  );
}

/** Mic off */
export function IconMicOff(props: IconProps) {
  return (
    <svg {...svgProps(props)}>
      <rect x="9" y="2.5" width="6" height="11" rx="0" />
      <path d="M5.5 11a6.5 6.5 0 0 0 13 0" />
      <path d="M12 17.5V21" />
      <path d="M8 21h8" />
      <path d="M3 3l18 18" />
    </svg>
  );
}

/** Mic */
export function IconMic(props: IconProps) {
  return (
    <svg {...svgProps(props)}>
      <rect x="9" y="2.5" width="6" height="11" />
      <path d="M5.5 11a6.5 6.5 0 0 0 13 0" />
      <path d="M12 17.5V21" />
      <path d="M8 21h8" />
    </svg>
  );
}

/** Camera */
export function IconCamera(props: IconProps) {
  return (
    <svg {...svgProps(props)}>
      <rect x="2.5" y="6" width="19" height="13" />
      <circle cx="12" cy="12.5" r="4" />
      <path d="M8 6l1.5-2.5h5L16 6" />
    </svg>
  );
}

/** Camera off */
export function IconCameraOff(props: IconProps) {
  return (
    <svg {...svgProps(props)}>
      <path d="M16 6l-1.5-2.5h-5L8 6" />
      <path d="M2.5 15.2V19h19v-13h-3" />
      <path d="M2.5 6h2" />
      <circle cx="12" cy="12.5" r="4" />
      <path d="M3 3l18 18" />
    </svg>
  );
}

/** Recalibrate — circular arrow */
export function IconRecalibrate(props: IconProps) {
  return (
    <svg {...svgProps(props)}>
      <path d="M20 12a8 8 0 1 1-2.3-5.6" />
      <path d="M20 3v4h-4" />
      <circle cx="12" cy="12" r="1.6" fill="currentColor" stroke="none" />
    </svg>
  );
}

/** Keyboard — typed command */
export function IconKeyboard(props: IconProps) {
  return (
    <svg {...svgProps(props)}>
      <rect x="2" y="6" width="20" height="12" />
      <path d="M6 10h.01" />
      <path d="M10 10h.01" />
      <path d="M14 10h.01" />
      <path d="M18 10h.01" />
      <path d="M7 14h10" />
    </svg>
  );
}

/** Alert triangle */
export function IconAlert(props: IconProps) {
  return (
    <svg {...svgProps(props)}>
      <path d="M12 3 2.5 20h19L12 3Z" />
      <path d="M12 10v4.5" />
      <circle cx="12" cy="17" r="0.9" fill="currentColor" stroke="none" />
    </svg>
  );
}

/** Eye off */
export function IconEyeOff(props: IconProps) {
  return (
    <svg {...svgProps(props)}>
      <path d="M2 12s3.5-6.5 10-6.5c1.8 0 3.4.5 4.7 1.2" />
      <path d="M19.5 8.5C21 10 22 12 22 12s-3.5 6.5-10 6.5c-1.8 0-3.4-.5-4.7-1.2" />
      <circle cx="12" cy="12" r="3" />
      <path d="M3 3l18 18" />
    </svg>
  );
}

/** Pause */
export function IconPause(props: IconProps) {
  return (
    <svg {...svgProps(props)}>
      <rect x="6" y="4" width="4" height="16" fill="currentColor" stroke="none" />
      <rect x="14" y="4" width="4" height="16" fill="currentColor" stroke="none" />
    </svg>
  );
}
