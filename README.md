# Content Creation Workspace

A structured workspace for creating, planning, and managing social media content with Claude Code as your AI content creation partner.

## What This Does

- **Creates LinkedIn posts** using viral replication, trend surfing, and pain point methods
- **Generates visuals** — AI infographics (via Kie.ai), carousels (PDF), personal photos
- **Maintains brand consistency** across all content with your visual style
- **Tracks everything** in an HTML dashboard
- **Scales content** — generate 10 ready-to-publish posts in a single run

## Quick Start

### 1. Install Dependencies

```bash
pip install Pillow requests
```

### 2. Set Up API Keys

```bash
cp .env.example .env
# Edit .env and add your API keys
```

You'll need:

- **Apify API key** — for scraping social media data ([apify.com](https://apify.com))
- **Kie.ai API key** — for AI image generation ([kie.ai](https://kie.ai))

### 3. Initialize Your Context

Run the init command with your social profile URLs:

```
/init https://www.linkedin.com/in/YOUR-PROFILE/ https://www.youtube.com/@YOUR-CHANNEL Any additional context about you
```

This scrapes your profiles and builds all context files automatically.

### 4. Add Your Assets

- **Personal photos** — Add to `context/images/` with descriptive filenames (e.g., `at-desk.jpg`, `headshot.jpg`, `casual-outdoor.jpg`)
- **Visual style references** — Add 3 infographic reference images to `reference/` as `infographic-ref-1.jpeg`, `infographic-ref-2.jpeg`, `infographic-ref-3.jpeg` (see `reference/README.md` for details)
- **Carousel references** — Add example carousel slides to `reference/carousel-ref/`

### 5. Start Creating

```
/prime              # Load context at start of every session
/create-10-posts    # Generate 10 LinkedIn posts with visuals
/create-plan        # Plan a content campaign
/implement          # Execute a plan
```

## Workspace Structure

```
.
├── CLAUDE.md              # Core instructions for Claude (always loaded)
├── .claude/
│   ├── commands/          # Slash commands: /init, /prime, /create-10-posts, /create-plan, /implement
│   └── skills/            # Skills: viral-replication, content-ideation, carousel-creation
├── .env                   # API keys (not committed)
├── context/               # Everything about YOU
│   ├── profile.md         #   Who you are
│   ├── business.md        #   What you do
│   ├── strategy.md        #   Where you're going
│   ├── metrics.md         #   Current numbers
│   ├── images/            #   Personal photos for posts
│   └── data/              #   Scraped social data
├── posts/                 # Final content — one folder per post
├── outputs/               # Working files, dashboards, drafts
├── reference/             # Style guides, visual refs, copywriting examples
├── scripts/               # Automation (dashboard builder, carousel generator)
└── plans/                 # Implementation plans
```

## Customization

### Brand Colors

Edit `CLAUDE.md` and `scripts/generate-carousel.py` to change:

- Background color (default: cream `#F5F3EE`)
- Accent color (default: lime green `#C8E64A`)
- Banner text (default: `YOUR BRAND`)

### Writing Style

The default writing style reference is Adam Robinson's LinkedIn style. You can:

- Replace `reference/adam-robinson-writing-style.md` with your own style guide
- Update `reference/adam-robinson-top-posts.md` with examples from your preferred writer
- Or keep them as-is — they're excellent templates for engaging LinkedIn content

### Visual Style

Add your own infographic reference images to establish your visual brand. The system uses these as style references when generating AI images, ensuring consistency across all posts.
