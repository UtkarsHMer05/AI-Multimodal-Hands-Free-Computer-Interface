/**
 * TypeScript port of the Voice Cursor command engine.
 *
 * Mirrors voice_cursor/commands.py and voice_cursor/text_matching.py so the
 * website demo behaves exactly like the real macOS application:
 *  - same dispatch order (screen-target actions checked before direct
 *    commands, as in app.py _handle_recognized_text),
 *  - same constrained vocabulary and phrase aliases,
 *  - same normalization (strip punctuation, collapse spaces, drop
 *    "please"/"computer" prefixes),
 *  - same fuzzy fallback (ratio >= 0.84 and runner-up gap >= 0.08),
 *  - same screen-target parsing ("click <label>", "double click on <label>",
 *    "move to <label>", 1-8 word labels, "the " prefix stripped),
 *  - same target matching key (case/whitespace/separator-insensitive,
 *    spelling-sensitive).
 *
 * scripts/verify_port_parity.py (repo root) asserts parity between this module
 * and the original Python implementation on a shared battery of utterances.
 */

export type CommandName =
  | "move_left"
  | "move_right"
  | "move_up"
  | "move_down"
  | "left_click"
  | "double_click"
  | "right_click"
  | "scroll_up"
  | "scroll_down"
  | "open_browser"
  | "new_tab"
  | "close_tab"
  | "pause_control"
  | "resume_control";

export type ScreenActionKind =
  | "screen_click"
  | "screen_double_click"
  | "screen_right_click"
  | "screen_hover";

export interface VoiceCommand {
  name: CommandName;
  label: string;
  phrases: string[];
}

export interface ScreenTextAction {
  kind: ScreenActionKind;
  label: string;
}

export const COMMANDS: VoiceCommand[] = [
  { name: "move_left", label: "Move left", phrases: ["move left", "go left"] },
  { name: "move_right", label: "Move right", phrases: ["move right", "go right"] },
  { name: "move_up", label: "Move up", phrases: ["move up", "go up"] },
  { name: "move_down", label: "Move down", phrases: ["move down", "go down"] },
  { name: "left_click", label: "Click", phrases: ["click", "left click"] },
  { name: "double_click", label: "Double click", phrases: ["double click"] },
  { name: "right_click", label: "Right click", phrases: ["right click"] },
  { name: "scroll_up", label: "Scroll up", phrases: ["scroll up"] },
  { name: "scroll_down", label: "Scroll down", phrases: ["scroll down"] },
  { name: "open_browser", label: "Open browser", phrases: ["open browser"] },
  { name: "new_tab", label: "New tab", phrases: ["new tab", "open new tab"] },
  { name: "close_tab", label: "Close tab", phrases: ["close tab"] },
  { name: "pause_control", label: "Pause control", phrases: ["pause control", "disable control"] },
  { name: "resume_control", label: "Resume control", phrases: ["resume control", "enable control"] },
];

const normalizeForMatch = (text: string): string =>
  text.toLowerCase().replace(/[^a-z0-9\s]/g, " ").replace(/\s+/g, " ").trim();

/** Normalize speech-recognition output for exact command matching. */
export function normalizePhrase(text: string): string {
  let normalized = normalizeForMatch(text);
  for (const prefix of ["please ", "computer "]) {
    if (normalized.startsWith(prefix)) {
      normalized = normalized.slice(prefix.length);
    }
  }
  return normalized;
}

export const COMMAND_BY_NAME: Record<CommandName, VoiceCommand> = Object.fromEntries(
  COMMANDS.map((command) => [command.name, command])
) as Record<CommandName, VoiceCommand>;

const PHRASE_TO_COMMAND: Map<string, VoiceCommand> = new Map(
  COMMANDS.flatMap((command) =>
    command.phrases.map((phrase) => [normalizePhrase(phrase), command] as const)
  )
);

/** Constrained grammar recognized by the Vosk fallback engine. */
export function recognitionPhrases(): string[] {
  return Array.from(PHRASE_TO_COMMAND.keys()).sort().concat(["[unk]"]);
}

// ---------------------------------------------------------------------------
// difflib SequenceMatcher port (find_longest_match / get_matching_blocks as in
// CPython), so the fuzzy fallback in interpretCommand behaves like the real
// Python application.
// ---------------------------------------------------------------------------

interface Match {
  a: number;
  b: number;
  size: number;
}

class SequenceMatcher {
  private a: string;
  private b: string;
  private b2j: Map<string, number[]>;

  constructor(a: string, b: string) {
    this.a = a;
    this.b = b;
    this.b2j = SequenceMatcher.chainB(b);
  }

  private static chainB(b: string): Map<string, number[]> {
    const b2j = new Map<string, number[]>();
    for (let i = 0; i < b.length; i++) {
      const c = b[i];
      const indices = b2j.get(c);
      if (indices) indices.push(i);
      else b2j.set(c, [i]);
    }
    return b2j;
  }

  /** CPython difflib find_longest_match (no autojunk/popular handling). */
  findLongestMatch(alo: number, ahi: number, blo: number, bhi: number): Match {
    const { a, b, b2j } = this;
    let besti = alo;
    let bestj = blo;
    let bestsize = 0;

    let j2len = new Map<number, number>();
    const nothing: number[] = [];

    for (let i = alo; i < ahi; i++) {
      const newj2len = new Map<number, number>();
      const indices = b2j.get(a[i]) ?? nothing;
      for (const j of indices) {
        if (j < blo) continue;
        if (j >= bhi) break;
        const k = (j2len.get(j - 1) ?? 0) + 1;
        newj2len.set(j, k);
        if (k > bestsize) {
          besti = i - k + 1;
          bestj = j - k + 1;
          bestsize = k;
        }
      }
      j2len = newj2len;
    }

    // Extend over popular adjacent equal elements (difflib's "junk"-free
    // extension step): while matches can be grown by one char on either
    // side, keep growing. This mirrors the loop in difflib that extends
    // the best match with adjacent positions at the boundaries.
    while (
      besti > alo &&
      bestj > blo &&
      a[besti - 1] === b[bestj - 1]
    ) {
      besti--;
      bestj--;
      bestsize++;
    }
    while (
      besti + bestsize < ahi &&
      bestj + bestsize < bhi &&
      a[besti + bestsize] === b[bestj + bestsize]
    ) {
      bestsize++;
    }

    return { a: besti, b: bestj, size: bestsize };
  }

  getMatchingBlocks(): Match[] {
    const queue: Array<[number, number, number, number]> = [
      [0, this.a.length, 0, this.b.length],
    ];
    const matches: Match[] = [];
    while (queue.length > 0) {
      const [alo, ahi, blo, bhi] = queue.pop()!;
      const [i, j, k] = (() => {
        const m = this.findLongestMatch(alo, ahi, blo, bhi);
        return [m.a, m.b, m.size] as const;
      })();
      if (k > 0) {
        matches.push({ a: i, b: j, size: k });
        if (alo < i && blo < j) queue.push([alo, i, blo, j]);
        if (i + k < ahi && j + k < bhi) queue.push([i + k, ahi, j + k, bhi]);
      }
    }
    matches.sort((m1, m2) => (m1.a - m2.a) || (m1.b - m2.b));
    // Collapse adjacent blocks exactly like difflib (non-standard for equal
    // positions but required for parity).
    const collapsed: Match[] = [];
    let ai = 0;
    let bj = 0;
    let size = 0;
    for (const m of matches) {
      if (ai + size === m.a && bj + size === m.b) {
        size += m.size;
      } else {
        if (size > 0) collapsed.push({ a: ai, b: bj, size });
        ai = m.a;
        bj = m.b;
        size = m.size;
      }
    }
    if (size > 0) collapsed.push({ a: ai, b: bj, size });
    collapsed.push({ a: this.a.length, b: this.b.length, size: 0 });
    return collapsed;
  }

  ratio(): number {
    const matches = this.getMatchingBlocks();
    let total = 0;
    for (const m of matches) total += m.size;
    if (this.a.length === 0 && this.b.length === 0) return 1;
    return (2 * total) / (this.a.length + this.b.length);
  }
}

/** Python difflib.SequenceMatcher(None, a, b).ratio() parity. */
export function similarityRatio(a: string, b: string): number {
  return new SequenceMatcher(a, b).ratio();
}

// ---------------------------------------------------------------------------
// Command interpretation (commands.py parity)
// ---------------------------------------------------------------------------

/** Return an exact or clearly dominant fixed-vocabulary command match. */
export function interpretCommand(text: string): VoiceCommand | null {
  const normalized = normalizePhrase(text);
  const exact = PHRASE_TO_COMMAND.get(normalized);
  if (exact) return exact;
  if (normalized.length < 5) return null;

  const ranked = Array.from(PHRASE_TO_COMMAND.entries())
    .map(([phrase, command]) => ({
      ratio: similarityRatio(normalized, phrase),
      phrase,
      command,
    }))
    .sort((x, y) => {
      if (y.ratio !== x.ratio) return y.ratio - x.ratio;
      // Python sorts tuples (ratio, command) where command comparison falls
      // back to enum value ordering; keep deterministic stable order.
      return 0;
    });
  if (ranked.length === 0 || ranked[0].ratio < 0.84) return null;
  if (ranked.length > 1 && ranked[0].ratio - ranked[1].ratio < 0.08) return null;
  return ranked[0].command;
}

const SCREEN_ACTION_PATTERNS: Array<[RegExp, ScreenActionKind]> = [
  [/^(?:double click)(?: on)? (.+)$/, "screen_double_click"],
  [/^(?:right click)(?: on)? (.+)$/, "screen_right_click"],
  [/^(?:click|press)(?: on)? (.+)$/, "screen_click"],
  [/^(?:move to|hover over|hover on) (.+)$/, "screen_hover"],
];

/** Parse actions such as "click Submit" or "double click Sign In". */
export function interpretScreenTextAction(text: string): ScreenTextAction | null {
  const normalized = normalizePhrase(text);
  for (const [pattern, kind] of SCREEN_ACTION_PATTERNS) {
    const matched = pattern.exec(normalized);
    if (matched === null) continue;
    let label = matched[1].trim();
    if (label.startsWith("the ")) label = label.slice(4).trim();
    const words = label.split(" ").filter((w) => w.length > 0);
    if (words.length >= 1 && words.length <= 8) {
      return { kind, label };
    }
  }
  return null;
}

// ---------------------------------------------------------------------------
// Target text matching (text_matching.py parity)
// ---------------------------------------------------------------------------

/** Return lowercase alphanumeric words separated by single spaces. */
export function normalizeTargetText(text: string): string {
  return text.toLowerCase().replace(/[^a-z0-9]+/g, " ").trim();
}

/**
 * A key insensitive to case, whitespace, and separators. Removing only
 * separators allows "backend", "back end", and "BACK-END" to match while
 * keeping genuinely different spellings such as "project" and "projects"
 * distinct.
 */
export function targetComparisonKey(text: string): string {
  return normalizeTargetText(text).replace(/ /g, "");
}

/** Return whether two non-empty target labels have the same key. */
export function targetTextsMatch(first: string, second: string): boolean {
  const firstKey = targetComparisonKey(first);
  return firstKey.length > 0 && firstKey === targetComparisonKey(second);
}
