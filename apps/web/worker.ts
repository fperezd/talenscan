/**
 * Talenscan Cloudflare Worker.
 *
 * Reescribe rutas dinámicas (p.ej. /mandatos/42) hacia el HTML estático
 * exportado por Next (generateStaticParams sólo genera /mandatos/demo).
 * El navegador conserva la URL real; el cliente lee el id desde
 * usePathname() y carga el recurso correcto del backend.
 */

type Env = {
  ASSETS: Fetcher;
};

const REWRITES: Array<[RegExp, string]> = [
  [/^\/mandatos\/([^/]+)\/pipeline\/?$/, "/mandatos/demo/pipeline"],
  [/^\/mandatos\/([^/]+)\/perfil-objetivo\/?$/, "/mandatos/demo/perfil-objetivo"],
  [/^\/mandatos\/([^/]+)\/evaluar\/?$/, "/mandatos/demo/evaluar"],
  [/^\/mandatos\/([^/]+)\/comparar\/?$/, "/mandatos/demo/comparar"],
  [/^\/mandatos\/([^/]+)\/decision-room\/?$/, "/mandatos/demo/decision-room"],
  [/^\/mandatos\/([^/]+)\/talent-market-map\/?$/, "/mandatos/demo/talent-market-map"],
  [/^\/mandatos\/([^/]+)\/?$/, "/mandatos/demo"],
  [/^\/candidatos\/([^/]+)\/?$/, "/candidatos/demo"],
  [/^\/evaluaciones\/([^/]+)\/?$/, "/evaluaciones/demo"],
  [/^\/shortlist-cliente\/([^/]+)\/?$/, "/shortlist-cliente/demo"],
];

const RESERVED_FIRST_SEGMENTS = new Set([
  "nuevo",
  "demo",
  "_next",
]);

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const url = new URL(request.url);
    const pathname = url.pathname;

    for (const [pattern, target] of REWRITES) {
      const match = pathname.match(pattern);
      if (!match) continue;
      const dynamicSegment = match[1];
      if (RESERVED_FIRST_SEGMENTS.has(dynamicSegment)) continue;
      const rewritten = new URL(target, url.origin);
      rewritten.search = url.search;
      return env.ASSETS.fetch(new Request(rewritten.toString(), request));
    }

    return env.ASSETS.fetch(request);
  },
};
