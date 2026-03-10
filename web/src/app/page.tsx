"use client";

import { useState, useEffect, useRef } from "react";

const PILLARS = [
  {
    id: "intelligence",
    name: "Intelligence & Espionage",
    icon: "🔍",
    description:
      "Declassified operations, exposed intelligence programs, and spy stories that surfaced quietly.",
    className: "pillar-intelligence",
    example:
      "A Mossad officer's memoir was published last month. 200 people read it.",
  },
  {
    id: "conflicts",
    name: "Wars & Conflicts",
    icon: "⚔️",
    description:
      "Active conflicts the media stopped covering, proxy wars, and forgotten battlegrounds.",
    className: "pillar-conflicts",
    example:
      "Sudan's war has killed more people than Ukraine. Here's why no one talks about it.",
  },
  {
    id: "ai",
    name: "AI — The Elephant in the Room",
    icon: "🤖",
    description:
      "AI capabilities that exist today but aren't widely known. The gap between public and private.",
    className: "pillar-ai",
    example:
      "This Pentagon document describes AI weapons on page 847 of a 1,200-page budget request.",
  },
  {
    id: "cyber",
    name: "Cyber — The Invisible War",
    icon: "🛡️",
    description:
      "Nation-state cyberattacks, zero-day markets, surveillance tech, and buried data breaches.",
    className: "pillar-cyber",
    example:
      "This spyware company changed its name. Again. Here's what they're selling now.",
  },
  {
    id: "historical",
    name: "Historical Revelations",
    icon: "📜",
    description:
      "Newly declassified documents and archival discoveries that rewrite what we thought we knew.",
    className: "pillar-historical",
    example:
      "Germany declassified 10,000 pages of Stasi files. Here's what's in the first 500.",
  },
];

const STATS = [
  { value: "100+", label: "Sources Monitored Daily" },
  { value: "5", label: "Content Pillars" },
  { value: "3x", label: "Weekly Newsletter" },
  { value: "99%+", label: "Accuracy Rate" },
];

export default function Home() {
  const [email, setEmail] = useState("");
  const [submitted, setSubmitted] = useState(false);
  const [isVisible, setIsVisible] = useState(false);
  const heroRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    setIsVisible(true);
  }, []);

  const handleSubscribe = (e: React.FormEvent) => {
    e.preventDefault();
    if (email) {
      setSubmitted(true);
      // TODO: Connect to beehiiv API
      setTimeout(() => setSubmitted(false), 3000);
    }
  };

  return (
    <>
      {/* Grid overlay */}
      <div className="grid-overlay" />
      {/* Scan line */}
      <div className="scan-line" />

      {/* ===== NAVIGATION ===== */}
      <nav
        style={{
          position: "fixed",
          top: 0,
          left: 0,
          right: 0,
          zIndex: 50,
          background: "rgba(26, 26, 26, 0.9)",
          backdropFilter: "blur(12px)",
          borderBottom: "1px solid var(--dd-border)",
        }}
      >
        <div
          className="container"
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            height: 64,
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
            <span
              style={{
                fontFamily: "var(--font-jetbrains), monospace",
                fontSize: "1.1rem",
                fontWeight: 700,
                color: "var(--dd-red)",
                letterSpacing: "0.05em",
              }}
            >
              DEAD DROP
            </span>
            <span className="classified-stamp" style={{ fontSize: "0.55rem" }}>
              CLASSIFIED
            </span>
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: 24 }}>
            <a
              href="#pillars"
              style={{
                color: "var(--dd-gray)",
                textDecoration: "none",
                fontSize: "0.85rem",
                fontFamily: "var(--font-jetbrains), monospace",
                transition: "color 0.3s",
              }}
              onMouseEnter={(e) =>
                (e.currentTarget.style.color = "var(--dd-off-white)")
              }
              onMouseLeave={(e) =>
                (e.currentTarget.style.color = "var(--dd-gray)")
              }
            >
              PILLARS
            </a>
            <a
              href="#about"
              style={{
                color: "var(--dd-gray)",
                textDecoration: "none",
                fontSize: "0.85rem",
                fontFamily: "var(--font-jetbrains), monospace",
                transition: "color 0.3s",
              }}
              onMouseEnter={(e) =>
                (e.currentTarget.style.color = "var(--dd-off-white)")
              }
              onMouseLeave={(e) =>
                (e.currentTarget.style.color = "var(--dd-gray)")
              }
            >
              ABOUT
            </a>
            <a
              href="#subscribe"
              className="btn-primary"
              style={{ padding: "8px 20px", fontSize: "0.75rem" }}
            >
              SUBSCRIBE
            </a>
          </div>
        </div>
      </nav>

      {/* ===== HERO SECTION ===== */}
      <section
        ref={heroRef}
        className="section"
        style={{
          minHeight: "100vh",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          paddingTop: 120,
          position: "relative",
          overflow: "hidden",
        }}
      >
        {/* Background glow */}
        <div
          style={{
            position: "absolute",
            top: "20%",
            left: "50%",
            transform: "translateX(-50%)",
            width: 600,
            height: 600,
            background:
              "radial-gradient(circle, rgba(192,57,43,0.08) 0%, transparent 70%)",
            pointerEvents: "none",
          }}
        />

        <div
          className="container"
          style={{ textAlign: "center", position: "relative", zIndex: 2 }}
        >
          <div
            className={isVisible ? "animate-slide-down" : ""}
            style={{ opacity: isVisible ? 1 : 0, marginBottom: 24 }}
          >
            <span className="classified-stamp">TOP SECRET // EYES ONLY</span>
          </div>

          <h1
            className={isVisible ? "animate-fade-in-up" : ""}
            style={{
              fontSize: "clamp(2.5rem, 6vw, 5rem)",
              fontWeight: 800,
              marginBottom: 24,
              opacity: isVisible ? 1 : 0,
              animationDelay: "0.2s",
              background:
                "linear-gradient(180deg, var(--dd-off-white) 0%, var(--dd-gray) 100%)",
              WebkitBackgroundClip: "text",
              WebkitTextFillColor: "transparent",
              backgroundClip: "text",
            }}
          >
            The Stories That Fell
            <br />
            <span
              style={{
                WebkitTextFillColor: "var(--dd-red)",
                color: "var(--dd-red)",
              }}
            >
              Through the Cracks
            </span>
          </h1>

          <p
            className={isVisible ? "animate-fade-in-up" : ""}
            style={{
              fontSize: "clamp(1rem, 2vw, 1.25rem)",
              color: "var(--dd-gray)",
              maxWidth: 700,
              margin: "0 auto 48px",
              lineHeight: 1.7,
              opacity: isVisible ? 1 : 0,
              animationDelay: "0.4s",
            }}
          >
            Buried in 500-page UN reports. Hidden in declassified intelligence
            documents. Lost in court filings and FOIA releases. We find them,
            verify them, and make them impossible to ignore.
          </p>

          <div
            className={isVisible ? "animate-fade-in-up" : ""}
            style={{
              opacity: isVisible ? 1 : 0,
              animationDelay: "0.6s",
            }}
          >
            <p
              style={{
                fontFamily: "var(--font-jetbrains), monospace",
                fontSize: "0.75rem",
                color: "var(--dd-red)",
                letterSpacing: "0.15em",
                textTransform: "uppercase",
                marginBottom: 16,
              }}
            >
              Intelligence. Verified. Sourced. No tinfoil.
            </p>

            <form
              onSubmit={handleSubscribe}
              style={{
                display: "flex",
                gap: 0,
                maxWidth: 500,
                margin: "0 auto",
              }}
            >
              <input
                type="email"
                placeholder="your@email.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="input-field"
                required
                style={{ borderRight: "none", flex: 1 }}
              />
              <button
                type="submit"
                className="btn-primary"
                style={{
                  whiteSpace: "nowrap",
                  ...(submitted ? { background: "#27AE60" } : {}),
                }}
              >
                {submitted ? "✓ RECEIVED" : "GET BRIEFED"}
              </button>
            </form>

            <p
              style={{
                fontSize: "0.75rem",
                color: "var(--dd-gray)",
                marginTop: 12,
                opacity: 0.6,
              }}
            >
              Free intelligence briefing · 3x per week · No spam · Unsubscribe
              anytime
            </p>
          </div>

          {/* Stats bar */}
          <div
            className={isVisible ? "animate-fade-in-up" : ""}
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(4, 1fr)",
              gap: 24,
              maxWidth: 700,
              margin: "80px auto 0",
              opacity: isVisible ? 1 : 0,
              animationDelay: "0.8s",
            }}
          >
            {STATS.map((stat) => (
              <div key={stat.label} style={{ textAlign: "center" }}>
                <div
                  style={{
                    fontFamily: "var(--font-jetbrains), monospace",
                    fontSize: "1.8rem",
                    fontWeight: 800,
                    color: "var(--dd-red)",
                    lineHeight: 1,
                    marginBottom: 6,
                  }}
                >
                  {stat.value}
                </div>
                <div
                  style={{
                    fontSize: "0.7rem",
                    color: "var(--dd-gray)",
                    fontFamily: "var(--font-jetbrains), monospace",
                    letterSpacing: "0.05em",
                    textTransform: "uppercase",
                  }}
                >
                  {stat.label}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Scroll indicator */}
        <div
          style={{
            position: "absolute",
            bottom: 40,
            left: "50%",
            transform: "translateX(-50%)",
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            gap: 8,
            opacity: 0.4,
          }}
        >
          <span
            style={{
              fontFamily: "var(--font-jetbrains), monospace",
              fontSize: "0.6rem",
              letterSpacing: "0.2em",
              textTransform: "uppercase",
              color: "var(--dd-gray)",
            }}
          >
            SCROLL
          </span>
          <div
            style={{
              width: 1,
              height: 30,
              background:
                "linear-gradient(180deg, var(--dd-gray), transparent)",
            }}
          />
        </div>
      </section>

      {/* ===== PILLARS SECTION ===== */}
      <section id="pillars" className="section">
        <div className="container">
          <div style={{ textAlign: "center", marginBottom: 60 }}>
            <span
              style={{
                fontFamily: "var(--font-jetbrains), monospace",
                fontSize: "0.7rem",
                letterSpacing: "0.2em",
                textTransform: "uppercase",
                color: "var(--dd-red)",
              }}
            >
              CONTENT PILLARS
            </span>
            <h2
              style={{
                fontSize: "clamp(1.8rem, 4vw, 2.8rem)",
                fontWeight: 700,
                marginTop: 12,
              }}
            >
              Five Verticals.{" "}
              <span style={{ color: "var(--dd-gray)" }}>Zero Fluff.</span>
            </h2>
          </div>

          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))",
              gap: 20,
            }}
          >
            {PILLARS.map((pillar) => (
              <div
                key={pillar.id}
                className="card"
                style={{ display: "flex", flexDirection: "column", gap: 16 }}
              >
                <div
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "flex-start",
                  }}
                >
                  <span style={{ fontSize: "2rem" }}>{pillar.icon}</span>
                  <span className={`pillar-tag ${pillar.className}`}>
                    {pillar.id}
                  </span>
                </div>
                <h3
                  style={{
                    fontSize: "1.15rem",
                    fontWeight: 700,
                  }}
                >
                  {pillar.name}
                </h3>
                <p
                  style={{
                    color: "var(--dd-gray)",
                    fontSize: "0.9rem",
                    lineHeight: 1.6,
                  }}
                >
                  {pillar.description}
                </p>
                <div
                  style={{
                    marginTop: "auto",
                    padding: "12px 16px",
                    background: "rgba(192, 57, 43, 0.05)",
                    border: "1px solid rgba(192, 57, 43, 0.1)",
                    fontSize: "0.8rem",
                    fontStyle: "italic",
                    color: "var(--dd-off-white)",
                    lineHeight: 1.5,
                  }}
                >
                  &ldquo;{pillar.example}&rdquo;
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      <hr className="separator" />

      {/* ===== ABOUT / HOW IT WORKS ===== */}
      <section id="about" className="section">
        <div className="container">
          <div style={{ textAlign: "center", marginBottom: 60 }}>
            <span
              style={{
                fontFamily: "var(--font-jetbrains), monospace",
                fontSize: "0.7rem",
                letterSpacing: "0.2em",
                textTransform: "uppercase",
                color: "var(--dd-red)",
              }}
            >
              HOW IT WORKS
            </span>
            <h2
              style={{
                fontSize: "clamp(1.8rem, 4vw, 2.8rem)",
                fontWeight: 700,
                marginTop: 12,
              }}
            >
              AI-Powered Discovery.{" "}
              <span style={{ color: "var(--dd-gray)" }}>
                Human-Verified Truth.
              </span>
            </h2>
          </div>

          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))",
              gap: 32,
              maxWidth: 1000,
              margin: "0 auto",
            }}
          >
            {[
              {
                step: "01",
                title: "MONITOR",
                description:
                  "Our AI pipeline monitors 100+ sources: RSS feeds, government databases, court filings, FOIA releases, and academic papers.",
              },
              {
                step: "02",
                title: "DETECT",
                description:
                  "The Gap Detection engine scores every piece: high significance + low media coverage = Dead Drop material.",
              },
              {
                step: "03",
                title: "VERIFY",
                description:
                  "5-point verification protocol. Primary source check. Cross-reference. Bias detection. Human editorial review on everything.",
              },
              {
                step: "04",
                title: "DELIVER",
                description:
                  "Newsletter, YouTube documentary, Twitter thread, Reddit deep dive — all generated, all verified, all yours.",
              },
            ].map((item) => (
              <div key={item.step} style={{ position: "relative" }}>
                <div
                  style={{
                    fontFamily: "var(--font-jetbrains), monospace",
                    fontSize: "3rem",
                    fontWeight: 900,
                    color: "rgba(192, 57, 43, 0.15)",
                    lineHeight: 1,
                    marginBottom: 8,
                  }}
                >
                  {item.step}
                </div>
                <h3
                  style={{
                    fontFamily: "var(--font-jetbrains), monospace",
                    fontSize: "0.9rem",
                    fontWeight: 700,
                    letterSpacing: "0.1em",
                    marginBottom: 12,
                    color: "var(--dd-red)",
                  }}
                >
                  {item.title}
                </h3>
                <p
                  style={{
                    fontSize: "0.85rem",
                    color: "var(--dd-gray)",
                    lineHeight: 1.6,
                  }}
                >
                  {item.description}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <hr className="separator" />

      {/* ===== SUBSCRIBE SECTION ===== */}
      <section id="subscribe" className="section">
        <div
          className="container"
          style={{ maxWidth: 700, textAlign: "center" }}
        >
          <span
            className="classified-stamp"
            style={{ marginBottom: 24, display: "inline-block" }}
          >
            DISPATCH READY
          </span>
          <h2
            style={{
              fontSize: "clamp(1.8rem, 4vw, 2.8rem)",
              fontWeight: 700,
              marginBottom: 16,
              marginTop: 24,
            }}
          >
            Get the Briefing
          </h2>
          <p
            style={{
              color: "var(--dd-gray)",
              fontSize: "1rem",
              marginBottom: 40,
              lineHeight: 1.7,
            }}
          >
            Three times a week, the stories that matter — verified, sourced, and
            impossible to find anywhere else. Join the intelligence community
            that doesn&apos;t need clearance.
          </p>

          <form
            onSubmit={handleSubscribe}
            style={{
              display: "flex",
              gap: 0,
              maxWidth: 500,
              margin: "0 auto 32px",
            }}
          >
            <input
              type="email"
              placeholder="your@email.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="input-field"
              required
              style={{ borderRight: "none", flex: 1 }}
            />
            <button
              type="submit"
              className="btn-primary animate-pulse-glow"
              style={{
                whiteSpace: "nowrap",
                ...(submitted
                  ? { background: "#27AE60", animation: "none" }
                  : {}),
              }}
            >
              {submitted ? "✓ RECEIVED" : "SUBSCRIBE"}
            </button>
          </form>

          <div
            style={{
              display: "flex",
              justifyContent: "center",
              gap: 32,
              flexWrap: "wrap",
            }}
          >
            {[
              "Free forever",
              "No spam",
              "Unsubscribe anytime",
              "Sources always cited",
            ].map((item) => (
              <span
                key={item}
                style={{
                  fontSize: "0.75rem",
                  color: "var(--dd-gray)",
                  fontFamily: "var(--font-jetbrains), monospace",
                  display: "flex",
                  alignItems: "center",
                  gap: 6,
                }}
              >
                <span style={{ color: "var(--dd-red)" }}>✓</span> {item}
              </span>
            ))}
          </div>
        </div>
      </section>

      {/* ===== FOOTER ===== */}
      <footer
        style={{
          borderTop: "1px solid var(--dd-border)",
          padding: "40px 0",
          position: "relative",
          zIndex: 2,
        }}
      >
        <div
          className="container"
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            flexWrap: "wrap",
            gap: 20,
          }}
        >
          <div>
            <span
              style={{
                fontFamily: "var(--font-jetbrains), monospace",
                fontSize: "0.9rem",
                fontWeight: 700,
                color: "var(--dd-red)",
              }}
            >
              DEAD DROP
            </span>
            <p
              style={{
                fontSize: "0.75rem",
                color: "var(--dd-gray)",
                marginTop: 4,
              }}
            >
              The stories that fell through the cracks.
            </p>
          </div>

          <div style={{ display: "flex", gap: 24 }}>
            {[
              { label: "Twitter/X", url: "https://twitter.com/DeadDropIntel" },
              { label: "YouTube", url: "https://youtube.com/@DeadDropIntel" },
              { label: "Telegram", url: "https://t.me/DeadDropIntel" },
              { label: "Reddit", url: "https://reddit.com/u/DeadDropIntel" },
            ].map((link) => (
              <a
                key={link.label}
                href={link.url}
                target="_blank"
                rel="noopener noreferrer"
                style={{
                  fontFamily: "var(--font-jetbrains), monospace",
                  fontSize: "0.7rem",
                  color: "var(--dd-gray)",
                  textDecoration: "none",
                  letterSpacing: "0.05em",
                  transition: "color 0.3s",
                }}
                onMouseEnter={(e) =>
                  (e.currentTarget.style.color = "var(--dd-red)")
                }
                onMouseLeave={(e) =>
                  (e.currentTarget.style.color = "var(--dd-gray)")
                }
              >
                {link.label}
              </a>
            ))}
          </div>

          <p
            style={{
              fontSize: "0.65rem",
              color: "var(--dd-gray)",
              opacity: 0.5,
              fontFamily: "var(--font-jetbrains), monospace",
            }}
          >
            © {new Date().getFullYear()} DEAD DROP. ALL RIGHTS RESERVED.
          </p>
        </div>
      </footer>
    </>
  );
}
