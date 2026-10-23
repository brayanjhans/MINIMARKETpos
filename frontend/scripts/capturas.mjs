// Capturas de las pantallas protegidas para revisar el diseño (usa el cliente CDP de taste-skill).
// Inicia sesión por la API, pone la cookie de sesión en un Chrome sin ventana y fotografía cada ruta.
//
// Uso (desde la raíz del proyecto, con backend y frontend levantados):
//   node frontend/scripts/capturas.mjs [carpeta] [--rutas /dashboard,/usuarios] [--anchos 1440,768,390] [--oscuro]

import { mkdirSync } from "node:fs";
import { join, resolve } from "node:path";

import { Browser } from "../../.claude/skills/taste-skill/scripts/lib/cdp.mjs";

const FRONT = process.env.FRONT_URL ?? "http://localhost:3010";
const args = process.argv.slice(2);
const opcion = (nombre, defecto) => {
  const i = args.indexOf(nombre);
  return i >= 0 ? args[i + 1] : defecto;
};
const carpeta = resolve(args[0] && !args[0].startsWith("--") ? args[0] : ".taste-skill/capturas");
const rutas = opcion("--rutas", "/login,/dashboard,/usuarios,/roles,/auditoria").split(",");
const anchos = opcion("--anchos", "1440,768,390").split(",").map(Number);
const oscuro = args.includes("--oscuro");
mkdirSync(carpeta, { recursive: true });

async function cookieSesion() {
  const r = await fetch(`${FRONT}/api/v1/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username: process.env.CAP_USER ?? "admin", password: process.env.CAP_PASS ?? "Admin123*" }),
  });
  if (!r.ok) throw new Error(`Login falló: ${r.status} ${await r.text()}`);
  const valor = /mm_refresh=([^;]+)/.exec(r.headers.get("set-cookie") ?? "")?.[1];
  if (!valor) throw new Error("No llegó la cookie de sesión");
  return valor;
}

const browser = await Browser.launch();
try {
  for (const ancho of anchos) {
    const alto = ancho < 600 ? 844 : ancho < 1000 ? 1024 : 900;
    for (const ruta of rutas) {
      const page = await browser.newPage({ width: ancho, height: alto, mobile: ancho < 600 });
      if (oscuro) {
        // next-themes guarda la elección del usuario en localStorage("theme")
        await page.send("Page.addScriptToEvaluateOnNewDocument", { source: "localStorage.setItem('theme','dark')" });
      }
      // Las páginas comparten las cookies del navegador: el login se fotografía sin sesión
      if (ruta === "/login") await page.send("Network.clearBrowserCookies").catch(() => {});
      else {
        // Cada página obtiene su propia sesión: el refresh rota la cookie en cada carga
        await page.send("Network.enable");
        await page.send("Network.setCookie", { name: "mm_refresh", value: await cookieSesion(), url: FRONT, httpOnly: true });
      }
      await page.goto(`${FRONT}${ruta}`, { timeoutMs: 45000, settleMs: 2500 });
      const nombre = `${ruta.replace(/\//g, "") || "inicio"}-${ancho}${oscuro ? "-oscuro" : ""}.jpg`;
      await page.screenshot({ path: join(carpeta, nombre), quality: 80 });
      console.log(join(carpeta, nombre));
      await page.close();
    }
  }
} finally {
  await browser.close();
}
