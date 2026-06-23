import { readFileSync, writeFileSync } from "fs";
import { resolve } from "path";

const entryPath = resolve(import.meta.dirname || ".", "../dist/server/entry.mjs");

let content = readFileSync(entryPath, "utf-8");

content = content.replace(
  "const locals = createLocals(context);",
  "const locals = createLocals(context, env);",
);

content = content.replace(
  "function createLocals(ctx) {",
  `function createLocals(ctx, env) {`,
);

content = content.replace(
  'const locals = { cfContext: ctx };',
  `const locals = { cfContext: ctx, _env: env };`,
);

writeFileSync(entryPath, content, "utf-8");
console.log("Patched entry.mjs to pass env to locals._env");
