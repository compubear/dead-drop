"use client";

import { useState, useEffect } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";

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
    month: "long",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export default function StoryDetailPage() {
  const params = useParams();
  const [story, setStory] = useState<Story | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`/api/stories`)
      .then((res) => res.json())
      .then((data) => {
        const found = data.stories.find(
          (s: Story) => s.id === parseInt(params.id as string),
        );
        setStory(found || null);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, [params.id]);

  if (loading) {
    return (
      <div
        style={{
          minHeight: "100vh",
          backgroundColor: "#0a0a0a",
          color: "#f5f5f5",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          fontFamily: "'JetBrains Mono', monospace",
        }}
      >
        DECRYPTING BRIEFING...
      </div>
    );
  }

  if (!story) {
    return (
      <div
        style={{
          minHeight: "100vh",
          backgroundColor: "#0a0a0a",
          color: "#f5f5f5",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          flexDirection: "column",
          gap: "20px",
        }}
      >
        <h2 style={{ fontFamily: "'JetBrains Mono', monospace" }}>
          BRIEFING NOT FOUND
        </h2>
        <Link href="/archive" style={{ color: "#dc2626" }}>
          ← Return to Archive
        </Link>
      </div>
    );
  }

  const pillarColor = PILLAR_COLORS[story.pillar] || "#94a3b8";

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
            maxWidth: "800px",
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
              fontFamily: "'JetBrains Mono', monospace",
              fontWeight: 800,
              fontSize: "1.1rem",
              color: "#f5f5f5",
              letterSpacing: "0.15em",
            }}
          >
            DEAD DROP
          </Link>
          <Link
            href="/archive"
            style={{
              color: "#94a3b8",
              textDecoration: "none",
              fontSize: "0.85rem",
            }}
          >
            ← Archive
          </Link>
        </div>
      </nav>

      {/* Story Content */}
      <article
        style={{
          maxWidth: "800px",
          margin: "0 auto",
          padding: "120px 24px 80px",
        }}
      >
        {/* Metadata bar */}
        <div
          style={{
            display: "flex",
            gap: "12px",
            alignItems: "center",
            marginBottom: "24px",
            flexWrap: "wrap",
          }}
        >
          <span
            style={{
              background: `${pillarColor}20`,
              color: pillarColor,
              border: `1px solid ${pillarColor}40`,
              padding: "4px 14px",
              borderRadius: "4px",
              fontSize: "0.72rem",
              fontWeight: 700,
              textTransform: "uppercase",
              letterSpacing: "0.1em",
              fontFamily: "'JetBrains Mono', monospace",
            }}
          >
            {story.pillar}
          </span>
          <span
            style={{
              color: "#64748b",
              fontSize: "0.8rem",
            }}
          >
            {formatDate(story.published_at)}
          </span>
        </div>

        {/* Title */}
        <h1
          style={{
            fontFamily: "'JetBrains Mono', monospace",
            fontSize: "clamp(1.5rem, 4vw, 2.2rem)",
            fontWeight: 800,
            lineHeight: 1.25,
            letterSpacing: "-0.02em",
            marginBottom: "32px",
          }}
        >
          {story.title}
        </h1>

        {/* Gap Score Panel */}
        <div
          style={{
            background: "rgba(255,255,255,0.03)",
            border: "1px solid rgba(255,255,255,0.08)",
            borderRadius: "12px",
            padding: "24px",
            marginBottom: "40px",
            display: "grid",
            gridTemplateColumns: "repeat(3, 1fr)",
            gap: "20px",
            textAlign: "center",
          }}
        >
          <div>
            <div
              style={{
                fontFamily: "'JetBrains Mono', monospace",
                fontSize: "0.65rem",
                color: "#64748b",
                textTransform: "uppercase",
                letterSpacing: "0.15em",
                marginBottom: "6px",
              }}
            >
              Significance
            </div>
            <div
              style={{
                fontFamily: "'JetBrains Mono', monospace",
                fontSize: "1.8rem",
                fontWeight: 800,
                color: "#f5f5f5",
              }}
            >
              {story.significance_score.toFixed(1)}
            </div>
          </div>
          <div>
            <div
              style={{
                fontFamily: "'JetBrains Mono', monospace",
                fontSize: "0.65rem",
                color: "#64748b",
                textTransform: "uppercase",
                letterSpacing: "0.15em",
                marginBottom: "6px",
              }}
            >
              Coverage
            </div>
            <div
              style={{
                fontFamily: "'JetBrains Mono', monospace",
                fontSize: "1.8rem",
                fontWeight: 800,
                color: "#f5f5f5",
              }}
            >
              {story.coverage_score.toFixed(1)}
            </div>
          </div>
          <div>
            <div
              style={{
                fontFamily: "'JetBrains Mono', monospace",
                fontSize: "0.65rem",
                color: "#dc2626",
                textTransform: "uppercase",
                letterSpacing: "0.15em",
                marginBottom: "6px",
              }}
            >
              Gap Score
            </div>
            <div
              style={{
                fontFamily: "'JetBrains Mono', monospace",
                fontSize: "1.8rem",
                fontWeight: 800,
                color: "#dc2626",
              }}
            >
              {story.gap_score.toFixed(1)}
            </div>
          </div>
        </div>

        {/* Classified stamp */}
        <div
          style={{
            position: "relative",
            padding: "24px",
            marginBottom: "40px",
            border: "1px solid rgba(220,38,38,0.2)",
            borderRadius: "8px",
            background: "rgba(220,38,38,0.03)",
          }}
        >
          <div
            style={{
              position: "absolute",
              top: "-10px",
              left: "20px",
              background: "#0a0a0a",
              padding: "0 10px",
              fontFamily: "'JetBrains Mono', monospace",
              fontSize: "0.65rem",
              color: "#dc2626",
              letterSpacing: "0.2em",
              fontWeight: 700,
            }}
          >
            INTELLIGENCE BRIEFING
          </div>
          <p
            style={{
              fontSize: "1.05rem",
              lineHeight: 1.8,
              color: "#e2e8f0",
            }}
          >
            {story.summary}
          </p>
        </div>

        {/* Sources */}
        {story.sources && story.sources.length > 0 && (
          <div style={{ marginBottom: "40px" }}>
            <h3
              style={{
                fontFamily: "'JetBrains Mono', monospace",
                fontSize: "0.75rem",
                color: "#64748b",
                letterSpacing: "0.15em",
                marginBottom: "12px",
                textTransform: "uppercase",
              }}
            >
              Sources ({story.sources.length})
            </h3>
            <ul
              style={{
                listStyle: "none",
                padding: 0,
                margin: 0,
                display: "flex",
                flexDirection: "column",
                gap: "8px",
              }}
            >
              {story.sources.map((source, i) => (
                <li
                  key={i}
                  style={{
                    color: "#94a3b8",
                    fontSize: "0.88rem",
                    paddingLeft: "16px",
                    borderLeft: "2px solid rgba(220,38,38,0.3)",
                  }}
                >
                  {source}
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Verification Badge */}
        <div
          style={{
            background: "rgba(16,185,129,0.05)",
            border: "1px solid rgba(16,185,129,0.2)",
            borderRadius: "8px",
            padding: "16px 20px",
            display: "flex",
            alignItems: "center",
            gap: "12px",
            marginBottom: "40px",
          }}
        >
          <span style={{ fontSize: "1.2rem" }}>✓</span>
          <div>
            <div
              style={{
                fontFamily: "'JetBrains Mono', monospace",
                fontSize: "0.72rem",
                color: "#10b981",
                fontWeight: 700,
                letterSpacing: "0.1em",
              }}
            >
              VERIFIED
            </div>
            <div style={{ fontSize: "0.8rem", color: "#94a3b8" }}>
              This story has passed our 5-point verification protocol.
            </div>
          </div>
        </div>

        {/* Subscribe CTA */}
        <div
          style={{
            textAlign: "center",
            padding: "40px",
            background: "rgba(255,255,255,0.02)",
            border: "1px solid rgba(255,255,255,0.06)",
            borderRadius: "12px",
          }}
        >
          <h3
            style={{
              fontFamily: "'JetBrains Mono', monospace",
              fontSize: "1rem",
              marginBottom: "8px",
              letterSpacing: "0.05em",
            }}
          >
            GET THE BRIEFING
          </h3>
          <p
            style={{
              color: "#94a3b8",
              fontSize: "0.85rem",
              marginBottom: "20px",
            }}
          >
            Stories like this, delivered to your inbox before they make the
            news.
          </p>
          <Link
            href="/"
            style={{
              display: "inline-block",
              background: "#dc2626",
              color: "#fff",
              padding: "12px 32px",
              borderRadius: "8px",
              textDecoration: "none",
              fontWeight: 700,
              fontSize: "0.85rem",
              fontFamily: "'JetBrains Mono', monospace",
              letterSpacing: "0.05em",
            }}
          >
            SUBSCRIBE
          </Link>
        </div>
      </article>
    </div>
  );
}
