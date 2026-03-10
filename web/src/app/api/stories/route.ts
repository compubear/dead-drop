// Dead Drop — Stories API route
// Returns scored stories for the web archive

import { NextRequest, NextResponse } from "next/server";

// Mock data for development — will connect to PostgreSQL in production
const MOCK_STORIES = [
  {
    id: 1,
    title:
      "NSA's Secret Partnership with Danish Intelligence for Tapping EU Leaders",
    summary:
      "Leaked documents reveal the NSA used Denmark's defense intelligence agency FE to tap undersea cables, enabling surveillance of European allies including German Chancellor Angela Merkel.",
    pillar: "intelligence",
    significance_score: 9.2,
    coverage_score: 3.5,
    gap_score: 5.7,
    status: "published",
    sources: ["Danish Broadcasting Corporation (DR)", "Le Monde"],
    created_at: "2024-01-15T08:00:00Z",
    published_at: "2024-01-16T10:00:00Z",
  },
  {
    id: 2,
    title:
      "China's Underground Military Tunnel Network Expands Near Taiwan Strait",
    summary:
      "Satellite imagery analysis reveals a significant expansion of PLA underground facilities along the Fujian coast, suggesting preparations for potential operations across the Taiwan Strait.",
    pillar: "conflicts",
    significance_score: 8.8,
    coverage_score: 2.1,
    gap_score: 6.7,
    status: "published",
    sources: [
      "Planet Labs Satellite Data",
      "CSIS Asia Maritime Transparency Initiative",
    ],
    created_at: "2024-01-12T14:00:00Z",
    published_at: "2024-01-13T09:00:00Z",
  },
  {
    id: 3,
    title:
      "AI-Generated Deepfakes Used in African Election Interference Campaign",
    summary:
      "A coordinated campaign using Claude-generated text and AI voice cloning has been targeting voters in three West African nations ahead of upcoming elections.",
    pillar: "ai",
    significance_score: 8.5,
    coverage_score: 2.8,
    gap_score: 5.7,
    status: "published",
    sources: ["Stanford Internet Observatory", "Atlantic Council DFR Lab"],
    created_at: "2024-01-10T11:00:00Z",
    published_at: "2024-01-11T08:30:00Z",
  },
  {
    id: 4,
    title:
      "Critical SCADA Vulnerability in European Power Grid Goes Unpatched for 18 Months",
    summary:
      "A critical remote code execution vulnerability in Siemens SCADA systems used by 12 European power utilities has remained unpatched despite being reported to CISA in mid-2022.",
    pillar: "cyber",
    significance_score: 9.0,
    coverage_score: 1.5,
    gap_score: 7.5,
    status: "published",
    sources: ["CISA Advisory ICS-CERT-2023-0892", "Dragos Industrial Security"],
    created_at: "2024-01-08T16:00:00Z",
    published_at: "2024-01-09T07:00:00Z",
  },
  {
    id: 5,
    title:
      "Newly Declassified CIA Files Reveal 1980s Operation to Destabilize Suriname",
    summary:
      "FOIA-released documents detail a previously unknown CIA operation codenamed GREENTHUMB, aimed at destabilizing the Bouterse government in Suriname through economic warfare.",
    pillar: "historical",
    significance_score: 7.8,
    coverage_score: 1.2,
    gap_score: 6.6,
    status: "published",
    sources: ["CIA FOIA Electronic Reading Room", "National Security Archive"],
    created_at: "2024-01-05T09:00:00Z",
    published_at: "2024-01-06T10:00:00Z",
  },
  {
    id: 6,
    title:
      "Russia's Wagner Group Rebrands Operations Across the Sahel Under 'Africa Corps'",
    summary:
      "Russian military operations previously conducted under the Wagner Group PMC banner are being reorganized under a new GRU-linked entity called 'Africa Corps', expanding into new territories.",
    pillar: "conflicts",
    significance_score: 8.2,
    coverage_score: 4.0,
    gap_score: 4.2,
    status: "published",
    sources: ["Le Monde Afrique", "ACLED Conflict Data"],
    created_at: "2024-01-03T13:00:00Z",
    published_at: "2024-01-04T08:00:00Z",
  },
];

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);

  const pillar = searchParams.get("pillar");
  const limit = parseInt(searchParams.get("limit") || "10");
  const offset = parseInt(searchParams.get("offset") || "0");

  let stories = [...MOCK_STORIES];

  // Filter by pillar
  if (pillar && pillar !== "all") {
    stories = stories.filter((s) => s.pillar === pillar);
  }

  // Sort by gap_score descending
  stories.sort((a, b) => b.gap_score - a.gap_score);

  // Paginate
  const total = stories.length;
  const paginated = stories.slice(offset, offset + limit);

  return NextResponse.json({
    stories: paginated,
    total,
    limit,
    offset,
    has_more: offset + limit < total,
  });
}
