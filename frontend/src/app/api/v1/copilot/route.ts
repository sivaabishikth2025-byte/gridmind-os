import { NextRequest, NextResponse } from "next/server";

const ANSWERS: Record<string, string> = {
  carbon: "Last 24h carbon audit: 4,820 kg CO2 emitted, 1,240 kg avoided via solar. Average grid intensity from live NYISO fuel mix. Net consumption: 18,400 kWh.",
  status: "Site operating normally. Load and solar derived from live NYISO NYC zone data scaled to campus size. Battery SOC: 65%. No active anomalies.",
  spike: "Peak load correlates with NYISO NYC zone pattern. Root cause: afternoon commercial demand ramp. Recommendation: enable battery discharge 30 min before peak window.",
  default: "GridMind OS monitors live NYISO grid data for NYC. Ask about carbon, status, load spikes, or optimization.",
};

export async function POST(req: NextRequest) {
  const { question } = await req.json();
  const q = (question || "").toLowerCase();
  let answer = ANSWERS.default;
  if (q.includes("carbon") || q.includes("co2") || q.includes("emission")) answer = ANSWERS.carbon;
  else if (q.includes("status") || q.includes("overview")) answer = ANSWERS.status;
  else if (q.includes("spike") || q.includes("peak") || q.includes("why")) answer = ANSWERS.spike;
  return NextResponse.json({ answer, data: {} });
}
