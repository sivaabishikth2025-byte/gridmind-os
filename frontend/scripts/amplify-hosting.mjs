import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const root = path.join(__dirname, "..");
const hosting = path.join(root, ".amplify-hosting");
const compute = path.join(hosting, "compute", "default");
const staticDir = path.join(hosting, "static");

function copyDir(src, dest) {
  fs.mkdirSync(dest, { recursive: true });
  for (const entry of fs.readdirSync(src, { withFileTypes: true })) {
    const from = path.join(src, entry.name);
    const to = path.join(dest, entry.name);
    if (entry.isDirectory()) copyDir(from, to);
    else fs.copyFileSync(from, to);
  }
}

function rmDir(target) {
  if (fs.existsSync(target)) fs.rmSync(target, { recursive: true, force: true });
}

fs.rmSync(hosting, { recursive: true, force: true });
fs.mkdirSync(compute, { recursive: true });
fs.mkdirSync(staticDir, { recursive: true });

const standaloneRoot = path.join(root, ".next", "standalone");
const appDir = fs.existsSync(path.join(standaloneRoot, "frontend"))
  ? path.join(standaloneRoot, "frontend")
  : standaloneRoot;

// Server bundle → compute/default
copyDir(appDir, compute);

// Static assets must live under .amplify-hosting/static (not inside compute)
copyDir(path.join(root, ".next", "static"), path.join(staticDir, "_next", "static"));

if (fs.existsSync(path.join(root, "public"))) {
  copyDir(path.join(root, "public"), staticDir);
}

// Remove duplicates from compute — Amplify serves these from static/
rmDir(path.join(compute, ".next", "static"));
rmDir(path.join(compute, "public"));

const manifest = {
  version: 1,
  routes: [
    {
      path: "/_next/static/*",
      target: { kind: "Static", cacheControl: "public, max-age=31536000, immutable" },
    },
    {
      path: "/*.*",
      target: { kind: "Static" },
      fallback: { kind: "Compute", src: "default" },
    },
    {
      path: "/*",
      target: { kind: "Compute", src: "default" },
    },
  ],
  computeResources: [
    {
      name: "default",
      entrypoint: "server.js",
      runtime: "nodejs20.x",
    },
  ],
  framework: { name: "next", version: "14.2.35" },
};

fs.writeFileSync(path.join(hosting, "deploy-manifest.json"), JSON.stringify(manifest, null, 2));
console.log("Amplify hosting bundle ready at .amplify-hosting");
