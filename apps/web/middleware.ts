import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

// Protected application workspace routes
const PROTECTED_PREFIXES = [
  "/dashboard",
  "/profile",
  "/equity",
  "/instruments",
  "/portfolio",
  "/funds",
  "/market",
  "/quantlab",
  "/ai",
];

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;
  const token = request.cookies.get("access_token")?.value;

  // Check if current route is protected
  const isProtected = PROTECTED_PREFIXES.some(
    (prefix) => pathname === prefix || pathname.startsWith(`${prefix}/`)
  );

  // If visiting protected route without an auth cookie, redirect to /login
  if (isProtected && !token) {
    const loginUrl = new URL("/login", request.url);
    loginUrl.searchParams.set("next", pathname);
    return NextResponse.redirect(loginUrl);
  }

  // If visiting login or register while already authenticated with a cookie, redirect to /dashboard
  if ((pathname === "/login" || pathname === "/register") && token) {
    return NextResponse.redirect(new URL("/dashboard", request.url));
  }

  return NextResponse.next();
}

export const config = {
  matcher: [
    "/dashboard/:path*",
    "/profile/:path*",
    "/equity/:path*",
    "/instruments/:path*",
    "/portfolio/:path*",
    "/funds/:path*",
    "/market/:path*",
    "/quantlab/:path*",
    "/ai/:path*",
    "/login",
    "/register",
  ],
};
