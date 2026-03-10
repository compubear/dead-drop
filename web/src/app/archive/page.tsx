"use client";

import { useState, useEffect } from "react";
import Link from "next/link";

/* ── types ── */
interface Story {
  id: number;
  title: string;
  summary: string;
  pillar: string;
  significance_score: number;
  coverage_score: number;
  gap_score: number;
  status: string;
  sources: string[];
  created_at: string;
  published_at: string;
}

const PILLARS = [
  { key: "all", label: "All Intelligence", color: "#dc2626" },
  { key: "intelligence", label: "Intelligence", color: "#2563eb" },
  { key: "conflicts", label: "Conflicts", color: "#dc2626" },
  { key: "ai", label: "AI", color: "#8b5cf6" },
  { key: "cyber", label: "Cyber", color: "#10b981" },
  { key: "historical", label: "Historical", color: "#d97706" },
];

const PILLAR_COLORS: Record<string, string> = {
  intelligence: "#2563eb",
  conflicts: "#dc2626",
  ai: "#8b5cf6",
  cyber: "#10b981",
  historical: "#d97706",
};

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

function GapScoreBadge({ score }: { score: number }) {
  const color = score >= 6 ? "#dc2626" : score >= 4 ? "#d97706" : "#10b981";

  return (
    <span
      style={{
        background: `${color}20`,
        color: color,
        border: `1px solid ${color}40`,
        padding: "2px 10px",
        borderRadius: "4px",
        fontFamily: "'JetBrains Mono', monospace",
        fontSize: "0.75rem",
        fontWeight: 700,
      }}
    >
      GAP {score.toFixed(1)}
    </span>
  );
}

function StoryCard({ story }: { story: Story }) {
  const pillarColor = PILLAR_COLORS[story.pillar] || "#94a3b8";

  return (
    <Link href={`/archive/${story.id}`} style={{ textDecoration: "none" }}>
      <article
        style={{
          background: "rgba(255,255,255,0.02)",
          border: "1px solid rgba(255,255,255,0.06)",
          borderRadius: "12px",
          padding: "28px",
          transition: "all 0.3s ease",
          cursor: "pointer",
        }}
        className="story-card"
      >
        {/* Header: pillar + gap score */}
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            marginBottom: "16px",
          }}
        >
          <span
            style={{
              background: `${pillarColor}20`,
              color: pillarColor,
              border: `1px solid ${pillarColor}40`,
              padding: "3px 12px",
              borderRadius: "4px",
              fontSize: "0.7rem",
              fontWeight: 700,
              textTransform: "uppercase",
              letterSpacing: "0.1em",
              fontFamily: "'JetBrains Mono', monospace",
            }}
          >
            {story.pillar}
          </span>
          <GapScoreBadge score={story.gap_score} />
        </div>

        {/* Title */}
        <h3
          style={{
            fontSize: "1.15rem",
            fontWeight: 700,
            letterSpacing: "-0.02em",
            lineHeight: 1.35,
            marginBottom: "12px",
            color: "#f5f5f5",
          }}
        >
          {story.title}
        </h3>

        {/* Summary */}
        <p
          style={{
            color: "#94a3b8",
            fontSize: "0.88rem",
            lineHeight: 1.6,
            marginBottom: "16px",
          }}
        >
          {story.summary}
        </p>

        {/* Footer: scores + date */}
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            borderTop: "1px solid rgba(255,255,255,0.06)",
            paddingTop: "12px",
            fontSize: "0.75rem",
            color: "#64748b",
          }}
        >
          <div style={{ display: "flex", gap: "16px" }}>
            <span>
              SIG{" "}
              <strong style={{ color: "#f5f5f5" }}>
                {story.significance_score.toFixed(1)}
              </strong>
            </span>
            <span>
              COV{" "}
              <strong style={{ color: "#f5f5f5" }}>
                {story.coverage_score.toFixed(1)}
              </strong>
            </span>
          </div>
          <span>{formatDate(story.published_at)}</span>
        </div>
      </article>
    </Link>
  );
}

export default function ArchivePage() {
  const [stories, setStories] = useState<Story[]>([]);
  const [activePillar, setActivePillar] = useState("all");
  const [loading, setLoading] = useState(true);
  const [total, setTotal] = useState(0);

  useEffect(() => {
    setLoading(true);
    fetch(`/api/stories?pillar=${activePillar}&limit=20`)
      .then((res) => res.json())
      .then((data) => {
        setStories(data.stories);
        setTotal(data.total);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, [activePillar]);

  return (
    <div
      style={{
        minHeight: "100vh",
        backgroundColor: "#0a0a0a",
        color: "#f5f5f5",
      }}
    >
      {/* Navigation */}
      <nav
        style={{
          position: "fixed",
          top: 0,
          left: 0,
          right: 0,
          zIndex: 1000,
          padding: "16px 0",
          background: "rgba(10,10,10,0.95)",
          borderBottom: "1px solid rgba(255,255,255,0.06)",
          backdropFilter: "blur(16px)",
        }}
      >
        <div
          style={{
            maxWidth: "1200px",
            margin: "0 auto",
            padding: "0 24px",
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
          }}
        >
          <Link
            href="/"
            style={{
              textDecoration: "none",
              display: "flex",
              alignItems: "center",
              gap: "12px",
            }}
          >
            <span
              style={{
                fontFamily: "'JetBrains Mono', monospace",
                fontWeight: 800,
                fontSize: "1.1rem",
                color: "#f5f5f5",
                letterSpacing: "0.15em",
              }}
            >
              DEAD DROP
            </span>
            <span
              style={{
                background: "#dc2626",
                color: "#fff",
                padding: "2px 8px",
                fontSize: "0.6rem",
                fontWeight: 700,
                borderRadius: "3px",
                letterSpacing: "0.1em",
                fontFamily: "'JetBrains Mono', monospace",
              }}
            >
              ARCHIVE
            </span>
          </Link>
          <Link
            href="/"
            style={{
              color: "#94a3b8",
              textDecoration: "none",
              fontSize: "0.85rem",
              transition: "color 0.2s",
            }}
          >
            ← Back to Home
          </Link>
        </div>
      </nav>

      {/* Hero */}
      <section
        style={{
          paddingTop: "120px",
          paddingBottom: "40px",
          textAlign: "center",
          borderBottom: "1px solid rgba(255,255,255,0.06)",
        }}
      >
        <div style={{ maxWidth: "800px", margin: "0 auto", padding: "0 24px" }}>
          <h1
            style={{
              fontFamily: "'JetBrains Mono', monospace",
              fontSize: "clamp(1.8rem, 4vw, 2.5rem)",
              fontWeight: 800,
              letterSpacing: "0.05em",
              marginBottom: "16px",
            }}
          >
            INTELLIGENCE ARCHIVE
          </h1>
          <p
            style={{
              color: "#94a3b8",
              fontSize: "1rem",
              lineHeight: 1.6,
              maxWidth: "600px",
              margin: "0 auto",
            }}
          >
            Stories scored by our AI intelligence pipeline. Ranked by{" "}
            <strong style={{ color: "#dc2626" }}>Gap Score</strong> — the
            difference between what matters and what&apos;s covered.
          </p>

          {/* Stats */}
          <div
            style={{
              display: "flex",
              justifyContent: "center",
              gap: "40px",
              marginTop: "24px",
              fontFamily: "'JetBrains Mono', monospace",
              fontSize: "0.8rem",
            }}
          >
            <div>
              <span
                style={{
                  color: "#dc2626",
                  fontWeight: 700,
                  fontSize: "1.2rem",
                }}
              >
                {total}
              </span>
              <br />
              <span style={{ color: "#64748b" }}>Stories</span>
            </div>
            <div>
              <span
                style={{
                  color: "#dc2626",
                  fontWeight: 700,
                  fontSize: "1.2rem",
                }}
              >
                5
              </span>
              <br />
              <span style={{ color: "#64748b" }}>Pillars</span>
            </div>
            <div>
              <span
                style={{
                  color: "#dc2626",
                  fontWeight: 700,
                  fontSize: "1.2rem",
                }}
              >
                22
              </span>
              <br />
              <span style={{ color: "#64748b" }}>Sources</span>
            </div>
          </div>
        </div>
      </section>

      {/* Pillar Filters */}
      <section
        style={{
          position: "sticky",
          top: "61px",
          zIndex: 100,
          background: "rgba(10,10,10,0.95)",
          backdropFilter: "blur(16px)",
          borderBottom: "1px solid rgba(255,255,255,0.06)",
          padding: "16px 0",
        }}
      >
        <div
          style={{
            maxWidth: "1200px",
            margin: "0 auto",
            padding: "0 24px",
            display: "flex",
            gap: "8px",
            flexWrap: "wrap",
          }}
        >
          {PILLARS.map((p) => (
            <button
              key={p.key}
              onClick={() => setActivePillar(p.key)}
              style={{
                background:
                  activePillar === p.key ? `${p.color}20` : "transparent",
                border: `1px solid ${
                  activePillar === p.key
                    ? `${p.color}60`
                    : "rgba(255,255,255,0.1)"
                }`,
                color: activePillar === p.key ? p.color : "#94a3b8",
                padding: "6px 16px",
                borderRadius: "6px",
                cursor: "pointer",
                fontSize: "0.78rem",
                fontWeight: 600,
                fontFamily: "'JetBrains Mono', monospace",
                transition: "all 0.2s",
                letterSpacing: "0.05em",
              }}
            >
              {p.label}
            </button>
          ))}
        </div>
      </section>

      {/* Stories Grid */}
      <section
        style={{
          maxWidth: "1200px",
          margin: "0 auto",
          padding: "32px 24px 80px",
        }}
      >
        {loading ? (
          <div
            style={{
              textAlign: "center",
              padding: "80px 0",
              color: "#64748b",
              fontFamily: "'JetBrains Mono', monospace",
            }}
          >
            <div
              style={{
                width: "40px",
                height: "40px",
                border: "3px solid rgba(220,38,38,0.2)",
                borderTop: "3px solid #dc2626",
                borderRadius: "50%",
                margin: "0 auto 16px",
                animation: "spin 1s linear infinite",
              }}
            />
            SCANNING INTELLIGENCE...
          </div>
        ) : stories.length === 0 ? (
          <div
            style={{
              textAlign: "center",
              padding: "80px 0",
              color: "#64748b",
            }}
          >
            No stories found for this pillar.
          </div>
        ) : (
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fill, minmax(360px, 1fr))",
              gap: "20px",
            }}
          >
            {stories.map((story) => (
              <StoryCard key={story.id} story={story} />
            ))}
          </div>
        )}
      </section>

      {/* Footer */}
      <footer
        style={{
          borderTop: "1px solid rgba(255,255,255,0.06)",
          padding: "32px 24px",
          textAlign: "center",
          color: "#64748b",
          fontSize: "0.8rem",
        }}
      >
        <span
          style={{
            fontFamily: "'JetBrains Mono', monospace",
            letterSpacing: "0.1em",
          }}
        >
          DEAD DROP
        </span>{" "}
        © {new Date().getFullYear()} — AI-Powered Intelligence Media
      </footer>

      <style jsx>{`
        .story-card:hover {
          background: rgba(255, 255, 255, 0.04) !important;
          border-color: rgba(220, 38, 38, 0.2) !important;
          transform: translateY(-2px);
        }
        @keyframes spin {
          to {
            transform: rotate(360deg);
          }
        }
      `}</style>
    </div>
  );
}
