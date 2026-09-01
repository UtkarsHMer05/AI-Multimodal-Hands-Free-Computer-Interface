// Parity harness: runs the compiled TS command engine on the shared battery
// and writes results for scripts/verify_port_parity.py to compare.
import { createRequire } from "node:module";
import { readFileSync, writeFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import path from "node:path";

const here = path.dirname(fileURLToPath(import.meta.url));
const require = createRequire(import.meta.url);
const engine = require("../.parity/commands.js");

const batteryPath = process.argv[2] ?? path.join(here, "../.parity/battery.json");
const outPath = process.argv[3] ?? path.join(here, "../.parity/ts-results.json");

const battery = JSON.parse(readFileSync(batteryPath, "utf8"));

const results = {
  utterances: battery.utterances.map((u) => {
    const command = engine.interpretCommand(u);
    const screen = engine.interpretScreenTextAction(u);
    return {
      command: command ? command.name : null,
      screen: screen ? { kind: screen.kind, label: screen.label } : null,
    };
  }),
  ratios: battery.ratioPairs.map(([a, b]) => engine.similarityRatio(a, b)),
  targetKeys: battery.targetPairs.map(([a]) => engine.targetComparisonKey(a)),
  targetMatches: battery.targetPairs.map(([a, b]) => engine.targetTextsMatch(a, b)),
};

writeFileSync(outPath, JSON.stringify(results));
console.log(`wrote ${results.utterances.length} utterance results, ${results.ratios.length} ratios`);
