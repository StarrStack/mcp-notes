# MCP Notes Wiki Frontend

A Flask-based web interface for browsing and navigating your MCP notes in a wiki-style format.

## Features

### Core Functionality
- **Home Page**: View recent notes with tag cloud navigation
- **Note Detail View**: Read individual notes with full markdown rendering
- **Tag Navigation**: Browse notes by category, type, priority, and topics
- **Search**: Full-text search across titles and content
- **All Notes**: Alphabetical listing of all notes

### Wiki Features
- **Wiki Links**: Use `[[Note Title]]` syntax to create links between notes
- **Backlinks**: See which notes link to the current note
- **Outgoing Links**: Track links from the current note
- **Tag Cloud**: Visual overview of all tags with usage counts
- **Timestamps**: Created and updated dates for each note

### Design
- Clean, modern interface with responsive design
- Syntax highlighting for code blocks
- Color-coded tags by dimension
- Mobile-friendly layout

## Installation

1. **Install dependencies**:
   ```bash
   python3.11 -m pip install -r requirements.txt
   ```

2. **Run the server**:
   ```bash
   python3.11 web_server.py
   ```

3. **Open your browser**:
   Visit http://localhost:5000

## Usage

### Creating Wiki Links

In your note content, create links to other notes using double brackets:

```markdown
I'm learning about [[MCP Protocol]] and want to build a [[Flask Application]].
```

When viewing the note in the wiki:
- Existing notes will be clickable links
- Missing notes will be styled differently (showing what doesn't exist yet)

### Navigation

**By Tags:**
- Click any tag badge to see all notes with that tag
- Use the sidebar tag cloud on the home page

**By Search:**
- Use the search box in the navigation bar
- Searches both titles and content

**By Recency:**
- Home page shows 20 most recently updated notes
- All Notes page shows everything alphabetically

### Backlinks

At the bottom of each note, you'll see:
- **Links from this note**: Other notes referenced in this note
- **Backlinks**: Notes that reference this note

This creates a web of interconnected knowledge!

## File Structure

```
MCPNotes/
├── web_server.py       # Flask application
├── templates/          # HTML templates
│   ├── base.html      # Base layout with navigation
│   ├── index.html     # Home page
│   ├── note.html      # Individual note view
│   ├── tag.html       # Tag filter view
│   ├── search.html    # Search results
│   └── all.html       # All notes listing
└── static/
    └── style.css      # Styling
```

## Technical Details

### Markdown Rendering
- Uses Python `markdown` library with extensions:
  - Fenced code blocks
  - Tables
  - Custom wiki link processing

### Data Access
- Reads directly from `notes.json` (same file as MCP server)
- No database required
- Changes from Claude Desktop appear immediately on page refresh

### Performance
- Loads all notes into memory (fine for thousands of notes)
- No caching (simple refresh to see updates)
- Could be optimized with caching for larger collections

## Future Enhancements

Potential additions:
- **Graph visualization**: Interactive network of note connections
- **Live editing**: Edit notes directly in the web interface
- **Markdown preview**: Side-by-side editing
- **Export**: Batch export with wiki link preservation
- **Dark mode**: Theme toggle
- **Advanced search**: Regex, tag combinations, date ranges
- **Note templates**: Quick start templates for common note types
- **Auto-complete**: Suggest existing note titles when typing `[[`
- **Tag management**: Rename/merge tags through the UI

## Development

Run in debug mode (auto-reloads on changes):
```bash
python3.11 web_server.py
```

The server runs on port 5000 by default. Edit `web_server.py` to change the port.

## License

GPL-3.0 License (same as main project)
