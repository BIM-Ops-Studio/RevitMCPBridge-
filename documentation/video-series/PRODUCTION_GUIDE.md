# Video Production Guide
## RevitMCPBridge Documentary Series

---

## Overview

This guide explains how to transform the episode markdown documents into professional video content.

---

## Option 1: PowerPoint + Voice Recording (Recommended)

### Step 1: Create PowerPoint Slides

For each episode, create a PowerPoint presentation following the slide descriptions in the markdown files.

**Slide Design Guidelines:**
- Use **16:9 aspect ratio** (1920x1080)
- Background: Deep blue (#1E3A5F) or dark gradient
- Text: White or light gray (#F4F4F4)
- Accents: Orange (#FF6B35) for highlights
- Fonts: Montserrat (headers), Inter (body)

**Animation Guidelines:**
- Use "Appear" or "Fade" for text reveals
- Use "Wipe" (left to right) for progress elements
- Use "Grow/Shrink" for emphasis
- Keep transitions to "Fade" or "Push" (professional, not flashy)

### Step 2: Record Voice Narration

**Option A: Use the Voice MCP**
```bash
# For each episode, the script can be read in chunks
mcp__voice__speak(text="Your narration text here", voice="andrew")
```

**Option B: Record manually**
- Use a quiet room with minimal echo
- Speak at natural pace (~150-180 words/minute)
- Pause 1-2 seconds between slides
- Record in 16-bit, 44.1kHz WAV format

**Option C: Use professional TTS**
- ElevenLabs, Azure TTS, or Google Cloud TTS
- Use a natural male voice (matches "Andrew" character)
- Post-process for consistent volume

### Step 3: Combine in Video Editor

**Recommended Software:**
- **Free:** DaVinci Resolve, Shotcut, OpenShot
- **Paid:** Adobe Premiere Pro, Final Cut Pro, Camtasia

**Process:**
1. Export PowerPoint slides as images (PNG, high-res)
2. Import slides into video editor
3. Add audio narration track
4. Time slides to match narration (use slide timing notes)
5. Add transitions between slides
6. Export as MP4 (H.264, 1080p, 30fps)

---

## Option 2: AI Video Generation

### Using AI Presentation Tools

**Gamma.app:**
1. Copy slide content from markdown
2. Paste into Gamma
3. Use "Generate presentation" feature
4. Add voice via Gamma's narration tools
5. Export as video

**Beautiful.ai:**
1. Create slides from markdown descriptions
2. Use built-in design templates
3. Record voiceover in-app
4. Export as video

**Canva:**
1. Use Canva Presentations
2. Build slides from markdown
3. Add animations in Canva
4. Use Canva's video export with narration

### Using AI Video Generators

**Synthesia or HeyGen:**
1. Create AI avatar presenter
2. Input narration scripts
3. Generate video with avatar
4. Add slide backgrounds as virtual sets

**Pictory or Lumen5:**
1. Input narration text
2. AI generates matching visuals
3. Customize with brand colors
4. Export final video

---

## Option 3: Screen Recording Approach

### Animated Presentation Recording

1. Create slides in PowerPoint/Google Slides
2. Set up screen recording (OBS Studio, Loom, Camtasia)
3. Present slides while recording
4. Record voice live OR add voiceover in post
5. Edit out mistakes, add intro/outro

---

## File Deliverables per Episode

```
EP01_Vision/
├── EP01_Vision_v1.pptx          # PowerPoint slides
├── EP01_Vision_narration.wav    # Voice recording
├── EP01_Vision_FINAL.mp4        # Final video
└── EP01_Vision_thumbnail.png    # YouTube thumbnail
```

---

## Branding Assets Needed

### Logo
- BIM Ops Studio logo (PNG, SVG)
- RevitMCPBridge wordmark

### Colors
```css
--primary-blue: #1E3A5F;
--accent-orange: #FF6B35;
--light-gray: #F4F4F4;
--highlight-cyan: #00D4FF;
--dark-bg: #0D1B2A;
```

### Fonts
- **Montserrat Bold** - Headlines
- **Inter Regular** - Body text
- **JetBrains Mono** - Code snippets

### Music
- Subtle tech ambient track (royalty-free)
- Suggestions: Artlist, Epidemic Sound, YouTube Audio Library
- Keep volume at 10-20% under narration

---

## Quality Checklist

Before publishing each episode:

- [ ] Audio levels consistent (-6dB to -3dB peaks)
- [ ] No background noise or echo
- [ ] Text readable at 1080p
- [ ] Animations smooth (30fps minimum)
- [ ] Branding consistent across all slides
- [ ] Spelling and grammar checked
- [ ] Total runtime within target (2:30-3:00)
- [ ] End card includes call-to-action
- [ ] Thumbnail is compelling

---

## Publishing Strategy

### Platform Recommendations

**Primary: YouTube**
- Upload as unlisted first for review
- Add timestamps in description
- Include links to GitHub, website
- Add end screen cards to next episode

**Secondary: LinkedIn**
- Native upload (better reach than links)
- Shorter format may need editing for LinkedIn
- Tag relevant industry hashtags

**Tertiary: Website/Portfolio**
- Embed YouTube videos
- Add download option for presentations
- Include transcript for accessibility

### Metadata Template

```
Title: RevitMCPBridge: [Episode Title] | Teaching AI to Build (Ep X/6)

Description:
[Episode summary - 2-3 sentences]

In this episode:
- [Key point 1]
- [Key point 2]
- [Key point 3]

🔗 Links:
- GitHub: [link]
- Website: www.bimopsstudio.com
- Documentation: [link]

⏱️ Timestamps:
0:00 - Intro
[timestamps for each section]

#RevitMCPBridge #BIM #Revit #AI #Architecture #ConstructionDocuments

Tags: revit, bim, ai, architecture, construction documents, automation, mcp, claude, anthropic
```

---

## Production Timeline Estimate

| Task | Time per Episode |
|------|------------------|
| PowerPoint creation | 2-3 hours |
| Voice recording | 30-45 minutes |
| Video editing | 1-2 hours |
| Review and fixes | 30 minutes |
| **Total** | **4-6 hours/episode** |

**Full series:** 24-36 hours of production work

---

## Quick Start: Minimum Viable Video

If you want to produce videos quickly:

1. **Use Canva or Google Slides** - pre-built templates
2. **Use Voice MCP or free TTS** - auto-generate narration
3. **Screen record the presentation** - simple, fast
4. **Add intro/outro cards** - brand consistency
5. **Export and publish** - done

This approach can produce an episode in 2-3 hours.

---

## Support

For questions about content:
- Review the markdown episode files for exact wording
- Check memory database for additional context
- Reference RevitMCPBridge documentation for technical accuracy

For video production help:
- YouTube tutorials for your chosen editing software
- AI tools documentation (Gamma, Canva, etc.)
- Professional voiceover services if needed
