// Dead Drop — RSS Feed API
// Generates an RSS feed of published stories

import { NextResponse } from "next/server";

export async function GET() {
  // Fetch stories from the stories API
  const baseUrl = process.env.NEXT_PUBLIC_BASE_URL || "https://dead-drop.co";

  // In production, this would fetch from the database
  const storiesRes = await fetch(`${baseUrl}/api/stories?limit=20`, {
    cache: "no-store",
  }).catch(() => null);

  let stories: any[] = [];
  if (storiesRes?.ok) {
    const data = await storiesRes.json();
    stories = data.stories || [];
  }

  const rssItems = stories
    .map(
      (story: any) => `
    <item>
      <title><![CDATA[${story.title}]]></title>
      <description><![CDATA[${story.summary}]]></description>
      <link>${baseUrl}/archive/${story.id}</link>
      <guid isPermaLink="true">${baseUrl}/archive/${story.id}</guid>
      <pubDate>${new Date(story.published_at).toUTCString()}</pubDate>
      <category>${story.pillar}</category>
    </item>`,
    )
    .join("\n");

  const rss = `<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <title>Dead Drop — Intelligence Briefings</title>
    <link>${baseUrl}</link>
    <description>AI-Powered Intelligence &amp; Geopolitics. The stories that fell through the cracks.</description>
    <language>en-us</language>
    <lastBuildDate>${new Date().toUTCString()}</lastBuildDate>
    <atom:link href="${baseUrl}/api/feed" rel="self" type="application/rss+xml"/>
    <image>
      <url>${baseUrl}/favicon.ico</url>
      <title>Dead Drop</title>
      <link>${baseUrl}</link>
    </image>
    ${rssItems}
  </channel>
</rss>`;

  return new NextResponse(rss, {
    headers: {
      "Content-Type": "application/rss+xml; charset=utf-8",
      "Cache-Control": "s-maxage=3600, stale-while-revalidate=86400",
    },
  });
}
