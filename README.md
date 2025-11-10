# MCP Note-Taking Server

A Model Context Protocol (MCP) server for managing personal notes with structured tagging and markdown support. This server integrates with Claude Desktop to provide seamless note-taking capabilities during AI conversations.

## Features

- **Structured Tagging**: Controlled vocabulary for categories, types, priorities, and topics with dynamic schema management
- **Markdown Support**: Write rich notes with markdown formatting
- **Advanced Search**: Find notes using tag filters, title search, and date range filtering
- **Export Capabilities**: Export individual notes or entire collections to markdown files
- **Dynamic Schema**: Add new tags to any dimension programmatically
- **JSON Storage**: Simple file-based persistence with atomic writes
- **MCP Integration**: Works natively with Claude Desktop via stdio transport

## Installation

### Prerequisites

- **Python 3.10 or higher** (required by MCP SDK)
- Claude Desktop application

**Check your Python version**:
```bash
python3 --version
```

If you have Python 3.9 or older, install a newer version:
- **macOS**: `brew install python@3.11` (requires [Homebrew](https://brew.sh))
- **Alternative**: Download from [python.org](https://www.python.org/downloads/macos/)

### Setup

1. **Clone or download this repository**

2. **Install dependencies**:
   ```bash
   # If you installed Python 3.11 via Homebrew, use:
   python3.11 -m pip install -r requirements.txt

   # Or use whichever Python 3.10+ you have installed
   ```

3. **Configure Claude Desktop**:

   Edit your Claude Desktop configuration file:
   - **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

   Add the following configuration:
   ```json
   {
     "mcpServers": {
       "notes": {
         "command": "python3.11",
         "args": ["/absolute/path/to/MCPNotes/server.py"]
       }
     }
   }
   ```

   **Important**:
   - Replace `python3.11` with your Python 3.10+ command (use `which python3.11` to verify)
   - Replace `/absolute/path/to/MCPNotes/server.py` with the actual path to your `server.py` file

4. **Restart Claude Desktop** to load the server

5. **Verify installation**:
   Open Claude Desktop and ask: "What tools do you have available?"
   You should see the note-taking tools listed.

## Data Model

### Note Structure

Each note contains:
- **id**: Unique UUID
- **title**: Note title
- **content**: Markdown-formatted content
- **tags**: Structured tags (category, type, priority, topics)
- **created**: ISO-8601 timestamp
- **updated**: ISO-8601 timestamp

### Tag Schema

The default tag schema includes:

- **category** (required, exactly one): `work`, `personal`, `learning`
- **type** (required, exactly one): `project`, `idea`, `reference`, `todo`, `note`
- **priority** (required, exactly one): `active`, `soon`, `someday`, `eventually`, `maybe`, `not-actionable`
- **topics** (optional, zero or more): `mcp`, `ai`, `coding`, `design`

You can dynamically add new tags to any dimension using the `add_tags_to_schema` tool, or manually edit `notes.json`.

## Available Tools

### 1. `get_tag_schema`
Get the complete tag schema showing all valid tags.

**Example**: "Show me the tag schema"

### 2. `create_note`
Create a new note with validated tags.

**Example**: "Create a note titled 'MCP Server Ideas' with content 'Build a notes server using MCP', category: learning, type: project, priority: active, topics: mcp, coding"

### 3. `update_note`
Update an existing note (partial updates supported).

**Example**: "Update note [id] and change the priority to 'soon'"

### 4. `delete_note`
Delete a note by ID.

**Example**: "Delete note [id]"

### 5. `read_note`
Read the full content of a specific note.

**Example**: "Show me note [id]"

### 6. `find_notes_by_tags`
Search notes using tag filtering, title search, and date filters (AND logic across all filters, OR within topics).

**Parameters**:
- Tag filters: `category`, `type`, `priority`, `topics`
- Title search: `title_contains` (case-insensitive substring match)
- Date filters: `created_after`, `created_before`, `updated_after`, `updated_before` (ISO-8601 timestamps)

**Examples**:
- "Find all notes with category 'work' and priority 'active'"
- "Find all notes about mcp or ai topics"
- "Find notes with 'MCP' in the title"
- "Find notes created after 2025-01-01"
- "Show me notes updated in the last week"
- "Show me all notes" (no filters = return all)

### 7. `list_tags`
List all tags currently in use with counts.

**Example**: "What tags am I using in my notes?"

### 8. `add_tags_to_schema`
Add new tags to a schema dimension dynamically.

**Parameters**:
- `dimension`: One of `category`, `type`, `priority`, or `topics`
- `tags`: Array of tag values to add

**Examples**:
- "Add a new category called 'research'"
- "Add 'urgent' and 'backlog' to the priority dimension"
- "Add topics: python, javascript, rust"

### 9. `export_note_to_markdown`
Export a single note to a markdown file.

**Parameters**:
- `id`: Note UUID to export
- `output_path`: Optional custom output file path (auto-generated if not provided)

**Examples**:
- "Export note [id] to markdown"
- "Export this note to /Users/me/Desktop/note.md"

### 10. `export_all_notes_to_markdown`
Export all notes to markdown files in a directory.

**Parameters**:
- `output_dir`: Optional output directory path (defaults to `exported_notes/`)

**Examples**:
- "Export all my notes to markdown"
- "Export all notes to /Users/me/Desktop/my_notes"

## Usage Examples

Here are some natural ways to interact with your notes in Claude Desktop:

**Creating notes**:
- "I want to take a note about the MCP protocol I'm learning"
- "Create a note for my project idea"

**Finding notes**:
- "Show me all my active work projects"
- "What learning notes do I have?"
- "Find notes about ai or coding"
- "Find notes with 'Python' in the title"
- "Show me notes I created this week"
- "Find notes updated after January 1st"

**Managing notes**:
- "Change the priority of note [id] to 'soon'"
- "Update the content of my MCP note"
- "Delete that old note"

**Organizing**:
- "What tags am I using?"
- "Show me the tag schema"
- "List all my active todos"
- "Add a new category called 'health'"
- "Add 'python' and 'rust' to my topics"

**Exporting**:
- "Export all my notes to markdown"
- "Export note [id] to a markdown file"
- "Export all notes to my Desktop"

## File Structure

```
mcp-notes/
├── notes.json          # Data storage (auto-created)
├── server.py           # Main MCP server
├── README.md           # This file
└── requirements.txt    # Python dependencies
```

## Data Storage

- All notes are stored in `notes.json` in the same directory as `server.py`
- The file is automatically created on first run with the default schema
- Atomic writes prevent data corruption
- All data persists across server restarts

## Troubleshooting

**Server not appearing in Claude Desktop**:
- Verify the path in `claude_desktop_config.json` is absolute and correct
- Check that Python is in your PATH
- Restart Claude Desktop completely

**Tag validation errors**:
- Use `get_tag_schema` to see valid tags
- Ensure required tags (category, type, priority) are provided
- Check that all tags match the schema exactly (case-sensitive)

**Notes not persisting**:
- Verify `notes.json` exists and is writable
- Check file permissions on the directory

## Future Enhancements

Potential improvements for future versions:
- Full-text search within note content (search across markdown)
- Import existing markdown files as notes
- SQLite backend for better performance with large note collections
- Note linking and backlinks
- Note archiving/soft delete
- Tag aliases and synonyms
- Bulk operations (bulk update, bulk export with filters)
- Note templates

## License

MIT License - feel free to modify and extend this server for your needs.
