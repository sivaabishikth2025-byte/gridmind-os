import { NextResponse } from "next/server";

export async function GET() {
  return NextResponse.json({ status: "ok", service: "gridmind-os", timestamp: new Date().toISOString() });
}
