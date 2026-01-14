# Frontend Service

Modern, responsive web UI for the AI RAG system with real-time streaming.

## Features

### 🎨 Modern Design
- Dark/Light mode with smooth transitions
- Responsive (mobile, tablet, desktop)
- Glassmorphism effects
- Smooth animations

### 💬 Real-Time Streaming
- Server-Sent Events (SSE)
- Live AI thinking display
- Step-by-step reasoning visualization
- Progress indicators

### 🎯 User Experience
- Welcome screen with examples
- Clean chat interface
- Auto-resizing input
- Source citations
- Character counter
- Keyboard shortcuts

## Tech Stack

- **HTML5** - Semantic, accessible markup
- **CSS3** - Modern features, CSS variables
- **Vanilla JavaScript** - No frameworks, lightweight
- **nginx** - Static file serving and API proxy

## Architecture

```
Components:
├── App (main controller)
├── StreamingClient (SSE handling)
├── ThinkingDisplay (thinking visualization)
└── Utils (helpers)

Files:
├── index.html (157 lines)
├── css/styles.css (742 lines)
├── js/app.js (156 lines)
├── js/streaming.js (221 lines)
├── js/thinking_display.js (197 lines)
└── js/utils.js (178 lines)
```

## Usage

### Via Docker Compose

```bash
# From project root
docker compose up frontend

# Access at http://localhost:8080
```

### Local Development

```bash
cd services/frontend

# Serve with any static server
python -m http.server 8080

# Or with nginx
nginx -c nginx.conf
```

## API Integration

Frontend proxies API requests through nginx:

```
/api/ask → http://orchestrator-api:8000/ask
```

SSE configuration in nginx.conf:
- `proxy_buffering off` (required!)
- `proxy_cache off`
- Long timeout for streams

## Theming

### Light Mode (Default)
- Clean, professional
- High contrast
- Blue accent (#3b82f6)

### Dark Mode
- Eye-friendly
- Reduced eye strain
- Auto-detection support

### CSS Variables

All colors defined as CSS variables:
```css
:root {
  --bg-primary: #ffffff;
  --text-primary: #1a202c;
  --accent-color: #3b82f6;
}

[data-theme="dark"] {
  --bg-primary: #1a202c;
  --text-primary: #f7fafc;
}
```

## Streaming Events

Frontend handles these SSE events:

- `thought` - AI thinking step
- `action` - About to do something
- `observation` - Learned something
- `validation` - Checking quality
- `final_answer` - The answer
- `error` - Error occurred

Example:
```javascript
event: thought
data: {"content": "Analyzing question...", "timestamp": "..."}

event: final_answer
data: {"content": "Answer text", "data": {"citations": [...]}}
```

## Keyboard Shortcuts

- `Enter` - Send message
- `Shift+Enter` - New line
- `Tab` - Navigate elements

## Responsive Breakpoints

- Mobile: < 768px
- Tablet: 768px - 1024px
- Desktop: > 1024px

## Browser Support

- Chrome/Edge 90+
- Firefox 88+
- Safari 14+

Modern features used:
- CSS Grid
- CSS Variables
- Fetch API
- ES6+ JavaScript

## Configuration

Set in nginx.conf:
- Port: 8080
- API proxy: orchestrator-api:8000
- Gzip: enabled
- Caching: 1 year for static assets

## Accessibility

- Semantic HTML
- ARIA labels
- Keyboard navigation
- High contrast
- Screen reader friendly

---

**Part of AI RAG Batch 5**  
**Status**: Complete ✅  
**Next**: Tools (Batch 6)
