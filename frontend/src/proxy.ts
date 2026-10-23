import { NextResponse, type NextRequest } from "next/server";

// Debe coincidir con COOKIE_REFRESH_NOMBRE del backend
const COOKIE_SESION = "mm_refresh";

/**
 * Redirección rápida en el servidor según exista o no la cookie de sesión.
 * No valida el token (eso lo hace el backend en cada petición); solo evita mostrar
 * pantallas protegidas a quien claramente no inició sesión.
 */
export function proxy(request: NextRequest) {
  const { pathname, search } = request.nextUrl;
  const conSesion = request.cookies.has(COOKIE_SESION);
  const esLogin = pathname === "/login";

  if (!conSesion && !esLogin) {
    const url = new URL("/login", request.url);
    if (pathname !== "/" && pathname !== "/dashboard") url.searchParams.set("siguiente", pathname + search);
    return NextResponse.redirect(url);
  }
  if (conSesion && esLogin) {
    return NextResponse.redirect(new URL("/dashboard", request.url));
  }
  return NextResponse.next();
}

export const config = {
  // Todo excepto la API, archivos estáticos y recursos de Next
  matcher: ["/((?!api|_next/static|_next/image|favicon.ico|.*\\.(?:png|jpg|jpeg|svg|webp|ico)$).*)"],
};
