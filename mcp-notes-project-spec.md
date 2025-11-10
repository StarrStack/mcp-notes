# MCP Note-Taking Server - Project Specification

## Overview
A Model Context Protocol (MCP) server for managing personal notes with structured tagging and markdown support. This server will integrate with Claude Desktop via stdio transport to provide note-taking capabilities during AI conversations.

## Technical Requirements

### Language & Transport
- **Language**: Python
- **Transport**: stdio (for Claude Desktop integration)
- **Storage**: JSON file-based persistence

### MCP Protocol
- Implement standard MCP server using stdio communication
- Support tool calls for note management operations
- Handle JSON-RPC message format

## Data Model

### Note Structure
```json
{
  "id": "uuid-string",
  "title": "Note title",
  "content": "Markdown formatted content",
  "tags": {
    "category": "work",
    "type": "project",
    "priority": "active",
    "topics": ["mcp", "python"]
  },
  "created": "ISO-8601 timestamp",
  "updated": "ISO-8601 timestamp"
}
```

### Tag Schema (Controlled Vocabulary)
```json
{
  "tag_schema": {
    "category": ["work", "personal", "learning"],
    "type": ["project", "idea", "reference", "todo", "note"],
    "priority": ["active", "soon", "someday", "eventually", "maybe", "not-actionable"],
    "topic": ["mcp", "ai", "coding", "design"]
  }
}
```

### Tag Validation Rules
- **category**: Exactly one required
- **type**: Exactly one required
- **priority**: Exactly one required
- **topics**: Zero or more allowed (optional array)

## Tools to Implement

### 1. `get_tag_schema`
Returns the complete tag schema showing all valid tags.

**Parameters**: None

**Returns**: Complete tag schema object

**Purpose**: Allows Claude to know what tags are valid before creating/updating notes

---

### 2. `create_note`
Creates a new note with validated tags.

**Parameters**:
- `title` (string, required): Note title
- `content` (string, required): Markdown-formatted content
- `category` (string, required): Must be from schema
- `type` (string, required): Must be from schema
- `priority` (string, required): Must be from schema
- `topics` (array of strings, optional): Each must be from schema

**Returns**: Created note object with generated ID and timestamps

**Validation**: 
- All tags must exist in schema
- Required tags must be present
- Generate UUID for ID
- Set created/updated timestamps

---

### 3. `update_note`
Updates an existing note (partial updates supported).

**Parameters**:
- `id` (string, required): Note UUID
- `title` (string, optional): New title
- `content` (string, optional): New content
- `category` (string, optional): New category
- `type` (string, optional): New type
- `priority` (string, optional): New priority
- `topics` (array of strings, optional): New topics (replaces existing)

**Returns**: Updated note object

**Validation**:
- Note ID must exist
- Any provided tags must be in schema
- Update timestamp on modification

---

### 4. `delete_note`
Deletes a note by ID.

**Parameters**:
- `id` (string, required): Note UUID

**Returns**: Success confirmation

**Validation**: Note ID must exist

---

### 5. `read_note`
Retrieves full content of a specific note.

**Parameters**:
- `id` (string, required): Note UUID

**Returns**: Complete note object

**Purpose**: Explicit read operation to get note content

---

### 6. `find_notes_by_tags`
Search notes using structured tag filtering.

**Parameters** (all optional, acts as AND filter):
- `category` (string, optional): Filter by category
- `type` (string, optional): Filter by type
- `priority` (string, optional): Filter by priority
- `topics` (array of strings, optional): Filter by topics (match ANY)

**Returns**: Array of matching notes (full objects)

**Behavior**:
- No parameters = return all notes
- Multiple parameters = AND logic (must match all)
- Topics use OR logic (match any of the provided topics)

---

### 7. `list_tags`
Shows all tags currently in use across all notes.

**Parameters**: None

**Returns**: Object with counts for each tag dimension
```json
{
  "category": {"work": 5, "personal": 3},
  "type": {"project": 4, "idea": 2, "note": 2},
  "priority": {"active": 3, "soon": 2, "someday": 3},
  "topics": {"mcp": 4, "ai": 2, "python": 1}
}
```

**Purpose**: Shows what tags are actually being used and how often

## Storage Implementation

### File Format
Single JSON file: `notes.json`

```json
{
  "tag_schema": { ... },
  "notes": [ ... ]
}
```

### Operations
- Load entire file into memory on startup
- Keep in-memory representation during operation
- Write back to file after any modification
- Use atomic writes (write to temp file, then rename) to prevent corruption

## Project Structure (Suggested)
```
mcp-notes/
├── notes.json          # Data storage
├── server.py           # Main MCP server implementation
├── README.md           # Setup and usage instructions
└── requirements.txt    # Python dependencies
```

## Integration with Claude Desktop

### Configuration
Add to `claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "notes": {
      "command": "python",
      "args": ["/path/to/mcp-notes/server.py"]
    }
  }
}
```

## Success Criteria
- Server starts successfully and communicates via stdio
- All 7 tools are properly exposed to Claude Desktop
- Tag validation works correctly
- Notes persist across server restarts
- Claude can create, read, update, delete, and search notes naturally in conversation

## Future Enhancements (Out of Scope for V1)
- Add new tags to schema via tool
- Export notes to markdown files
- Import existing markdown files
- Full-text search within note content
- SQLite backend for better performance
- Note linking/backlinks
