#!/usr/bin/env python3
"""
MCP Note-Taking Server
A Model Context Protocol server for managing personal notes with structured tagging.
"""

import json
import os
import tempfile
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from mcp.server import Server
from mcp.types import Tool, TextContent
import mcp.server.stdio


# Storage path
NOTES_FILE = Path(__file__).parent / "notes.json"


class NotesStorage:
    """Handles note storage and retrieval with atomic writes."""

    def __init__(self, file_path: Path):
        self.file_path = file_path
        self.data = self._load()

    def _load(self) -> dict:
        """Load notes from file."""
        if not self.file_path.exists():
            return {
                "tag_schema": {
                    "category": ["work", "personal", "learning"],
                    "type": ["project", "idea", "reference", "todo", "note"],
                    "priority": ["active", "soon", "someday", "eventually", "maybe", "not-actionable"],
                    "topics": ["mcp", "ai", "coding", "design"]
                },
                "notes": []
            }

        with open(self.file_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _save(self):
        """Atomically save notes to file."""
        # Write to temp file first
        temp_fd, temp_path = tempfile.mkstemp(
            dir=self.file_path.parent,
            prefix='.notes_',
            suffix='.json.tmp'
        )

        try:
            with os.fdopen(temp_fd, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)

            # Atomic rename
            os.replace(temp_path, self.file_path)
        except Exception:
            # Clean up temp file on error
            try:
                os.unlink(temp_path)
            except OSError:
                pass
            raise

    def get_schema(self) -> dict:
        """Get the tag schema."""
        return self.data["tag_schema"]

    def add_tags_to_schema(self, dimension: str, tags: list[str]) -> dict:
        """Add new tags to a schema dimension."""
        valid_dimensions = ["category", "type", "priority", "topics"]
        if dimension not in valid_dimensions:
            raise ValueError(f"Invalid dimension '{dimension}'. Must be one of: {', '.join(valid_dimensions)}")

        schema = self.data["tag_schema"]
        for tag in tags:
            if tag not in schema[dimension]:
                schema[dimension].append(tag)

        self._save()
        return schema

    def validate_tags(self, category: Optional[str] = None,
                     type_tag: Optional[str] = None,
                     priority: Optional[str] = None,
                     topics: Optional[list[str]] = None) -> tuple[bool, str]:
        """Validate tags against schema. Returns (is_valid, error_message)."""
        schema = self.data["tag_schema"]

        # Validate category
        if category is not None and category not in schema["category"]:
            return False, f"Invalid category '{category}'. Must be one of: {', '.join(schema['category'])}"

        # Validate type
        if type_tag is not None and type_tag not in schema["type"]:
            return False, f"Invalid type '{type_tag}'. Must be one of: {', '.join(schema['type'])}"

        # Validate priority
        if priority is not None and priority not in schema["priority"]:
            return False, f"Invalid priority '{priority}'. Must be one of: {', '.join(schema['priority'])}"

        # Validate topics
        if topics is not None:
            for topic in topics:
                if topic not in schema["topics"]:
                    return False, f"Invalid topic '{topic}'. Must be one of: {', '.join(schema['topics'])}"

        return True, ""

    def create_note(self, title: str, content: str, category: str,
                   type_tag: str, priority: str, topics: Optional[list[str]] = None) -> dict:
        """Create a new note."""
        # Validate required tags
        is_valid, error = self.validate_tags(category, type_tag, priority, topics)
        if not is_valid:
            raise ValueError(error)

        # Create note
        now = datetime.utcnow().isoformat() + 'Z'
        note = {
            "id": str(uuid.uuid4()),
            "title": title,
            "content": content,
            "tags": {
                "category": category,
                "type": type_tag,
                "priority": priority,
                "topics": topics or []
            },
            "created": now,
            "updated": now
        }

        self.data["notes"].append(note)
        self._save()
        return note

    def read_note(self, note_id: str) -> dict:
        """Read a note by ID."""
        for note in self.data["notes"]:
            if note["id"] == note_id:
                return note
        raise ValueError(f"Note with ID '{note_id}' not found")

    def update_note(self, note_id: str, title: Optional[str] = None,
                   content: Optional[str] = None, category: Optional[str] = None,
                   type_tag: Optional[str] = None, priority: Optional[str] = None,
                   topics: Optional[list[str]] = None) -> dict:
        """Update an existing note."""
        # Find note
        note = None
        for n in self.data["notes"]:
            if n["id"] == note_id:
                note = n
                break

        if note is None:
            raise ValueError(f"Note with ID '{note_id}' not found")

        # Validate any provided tags
        is_valid, error = self.validate_tags(category, type_tag, priority, topics)
        if not is_valid:
            raise ValueError(error)

        # Update fields
        if title is not None:
            note["title"] = title
        if content is not None:
            note["content"] = content
        if category is not None:
            note["tags"]["category"] = category
        if type_tag is not None:
            note["tags"]["type"] = type_tag
        if priority is not None:
            note["tags"]["priority"] = priority
        if topics is not None:
            note["tags"]["topics"] = topics

        # Update timestamp
        note["updated"] = datetime.utcnow().isoformat() + 'Z'

        self._save()
        return note

    def delete_note(self, note_id: str) -> bool:
        """Delete a note by ID."""
        for i, note in enumerate(self.data["notes"]):
            if note["id"] == note_id:
                self.data["notes"].pop(i)
                self._save()
                return True
        raise ValueError(f"Note with ID '{note_id}' not found")

    def find_notes(self, category: Optional[str] = None,
                  type_tag: Optional[str] = None,
                  priority: Optional[str] = None,
                  topics: Optional[list[str]] = None,
                  title_contains: Optional[str] = None,
                  created_after: Optional[str] = None,
                  created_before: Optional[str] = None,
                  updated_after: Optional[str] = None,
                  updated_before: Optional[str] = None) -> list[dict]:
        """Find notes matching the given filters."""
        results = []

        for note in self.data["notes"]:
            # Check category
            if category is not None and note["tags"]["category"] != category:
                continue

            # Check type
            if type_tag is not None and note["tags"]["type"] != type_tag:
                continue

            # Check priority
            if priority is not None and note["tags"]["priority"] != priority:
                continue

            # Check topics (OR logic - match any)
            if topics is not None:
                if not any(topic in note["tags"]["topics"] for topic in topics):
                    continue

            # Check title (case-insensitive substring match)
            if title_contains is not None:
                if title_contains.lower() not in note["title"].lower():
                    continue

            # Check created date filters
            if created_after is not None and note["created"] < created_after:
                continue
            if created_before is not None and note["created"] > created_before:
                continue

            # Check updated date filters
            if updated_after is not None and note["updated"] < updated_after:
                continue
            if updated_before is not None and note["updated"] > updated_before:
                continue

            results.append(note)

        return results

    def list_tags(self) -> dict:
        """List all tags currently in use with counts."""
        counts = {
            "category": {},
            "type": {},
            "priority": {},
            "topics": {}
        }

        for note in self.data["notes"]:
            # Count category
            cat = note["tags"]["category"]
            counts["category"][cat] = counts["category"].get(cat, 0) + 1

            # Count type
            typ = note["tags"]["type"]
            counts["type"][typ] = counts["type"].get(typ, 0) + 1

            # Count priority
            pri = note["tags"]["priority"]
            counts["priority"][pri] = counts["priority"].get(pri, 0) + 1

            # Count topics
            for topic in note["tags"]["topics"]:
                counts["topics"][topic] = counts["topics"].get(topic, 0) + 1

        return counts

    def export_note_to_markdown(self, note_id: str, output_path: Optional[str] = None) -> str:
        """Export a single note to a markdown file."""
        note = self.read_note(note_id)

        # Generate filename if not provided
        if output_path is None:
            safe_title = "".join(c if c.isalnum() or c in (' ', '-', '_') else '_' for c in note["title"])
            safe_title = safe_title.strip().replace(' ', '_')
            output_path = str(self.file_path.parent / f"{safe_title}_{note_id[:8]}.md")

        # Build markdown content
        md_content = f"# {note['title']}\n\n"
        md_content += f"**ID**: {note['id']}\n"
        md_content += f"**Created**: {note['created']}\n"
        md_content += f"**Updated**: {note['updated']}\n\n"
        md_content += f"**Tags**:\n"
        md_content += f"- Category: {note['tags']['category']}\n"
        md_content += f"- Type: {note['tags']['type']}\n"
        md_content += f"- Priority: {note['tags']['priority']}\n"
        if note['tags']['topics']:
            md_content += f"- Topics: {', '.join(note['tags']['topics'])}\n"
        md_content += f"\n---\n\n{note['content']}\n"

        # Write file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(md_content)

        return output_path

    def export_all_notes_to_markdown(self, output_dir: Optional[str] = None) -> list[str]:
        """Export all notes to markdown files in a directory."""
        if output_dir is None:
            output_dir = str(self.file_path.parent / "exported_notes")

        # Create directory if it doesn't exist
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        exported_files = []
        for note in self.data["notes"]:
            safe_title = "".join(c if c.isalnum() or c in (' ', '-', '_') else '_' for c in note["title"])
            safe_title = safe_title.strip().replace(' ', '_')
            file_path = str(output_path / f"{safe_title}_{note['id'][:8]}.md")

            # Build markdown content
            md_content = f"# {note['title']}\n\n"
            md_content += f"**ID**: {note['id']}\n"
            md_content += f"**Created**: {note['created']}\n"
            md_content += f"**Updated**: {note['updated']}\n\n"
            md_content += f"**Tags**:\n"
            md_content += f"- Category: {note['tags']['category']}\n"
            md_content += f"- Type: {note['tags']['type']}\n"
            md_content += f"- Priority: {note['tags']['priority']}\n"
            if note['tags']['topics']:
                md_content += f"- Topics: {', '.join(note['tags']['topics'])}\n"
            md_content += f"\n---\n\n{note['content']}\n"

            # Write file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(md_content)

            exported_files.append(file_path)

        return exported_files


# Initialize storage
storage = NotesStorage(NOTES_FILE)

# Initialize MCP server
app = Server("mcp-notes")


@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available tools."""
    return [
        Tool(
            name="get_tag_schema",
            description="Get the complete tag schema showing all valid tags for categories, types, priorities, and topics",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="create_note",
            description="Create a new note with title, content, and structured tags",
            inputSchema={
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "Note title"},
                    "content": {"type": "string", "description": "Markdown-formatted content"},
                    "category": {"type": "string", "description": "Category tag (must be from schema)"},
                    "type": {"type": "string", "description": "Type tag (must be from schema)"},
                    "priority": {"type": "string", "description": "Priority tag (must be from schema)"},
                    "topics": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Optional array of topic tags (each must be from schema)"
                    }
                },
                "required": ["title", "content", "category", "type", "priority"]
            }
        ),
        Tool(
            name="update_note",
            description="Update an existing note (partial updates supported)",
            inputSchema={
                "type": "object",
                "properties": {
                    "id": {"type": "string", "description": "Note UUID"},
                    "title": {"type": "string", "description": "New title"},
                    "content": {"type": "string", "description": "New content"},
                    "category": {"type": "string", "description": "New category"},
                    "type": {"type": "string", "description": "New type"},
                    "priority": {"type": "string", "description": "New priority"},
                    "topics": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "New topics (replaces existing)"
                    }
                },
                "required": ["id"]
            }
        ),
        Tool(
            name="delete_note",
            description="Delete a note by ID",
            inputSchema={
                "type": "object",
                "properties": {
                    "id": {"type": "string", "description": "Note UUID to delete"}
                },
                "required": ["id"]
            }
        ),
        Tool(
            name="read_note",
            description="Read the full content of a specific note by ID",
            inputSchema={
                "type": "object",
                "properties": {
                    "id": {"type": "string", "description": "Note UUID to read"}
                },
                "required": ["id"]
            }
        ),
        Tool(
            name="find_notes_by_tags",
            description="Search notes using tag filtering, title search, and date filters (AND logic across all filters, OR within topics)",
            inputSchema={
                "type": "object",
                "properties": {
                    "category": {"type": "string", "description": "Filter by category"},
                    "type": {"type": "string", "description": "Filter by type"},
                    "priority": {"type": "string", "description": "Filter by priority"},
                    "topics": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Filter by topics (match ANY)"
                    },
                    "title_contains": {"type": "string", "description": "Filter by title substring (case-insensitive)"},
                    "created_after": {"type": "string", "description": "Filter notes created after this ISO-8601 timestamp"},
                    "created_before": {"type": "string", "description": "Filter notes created before this ISO-8601 timestamp"},
                    "updated_after": {"type": "string", "description": "Filter notes updated after this ISO-8601 timestamp"},
                    "updated_before": {"type": "string", "description": "Filter notes updated before this ISO-8601 timestamp"}
                },
                "required": []
            }
        ),
        Tool(
            name="list_tags",
            description="List all tags currently in use across all notes with counts",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="add_tags_to_schema",
            description="Add new tags to a schema dimension (category, type, priority, or topics)",
            inputSchema={
                "type": "object",
                "properties": {
                    "dimension": {
                        "type": "string",
                        "description": "The schema dimension to add tags to (category, type, priority, or topics)"
                    },
                    "tags": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Array of tag values to add to the dimension"
                    }
                },
                "required": ["dimension", "tags"]
            }
        ),
        Tool(
            name="export_note_to_markdown",
            description="Export a single note to a markdown file",
            inputSchema={
                "type": "object",
                "properties": {
                    "id": {"type": "string", "description": "Note UUID to export"},
                    "output_path": {
                        "type": "string",
                        "description": "Optional custom output file path (auto-generated if not provided)"
                    }
                },
                "required": ["id"]
            }
        ),
        Tool(
            name="export_all_notes_to_markdown",
            description="Export all notes to markdown files in a directory",
            inputSchema={
                "type": "object",
                "properties": {
                    "output_dir": {
                        "type": "string",
                        "description": "Optional output directory path (defaults to 'exported_notes' in the notes directory)"
                    }
                },
                "required": []
            }
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent]:
    """Handle tool calls."""
    try:
        if name == "get_tag_schema":
            schema = storage.get_schema()
            return [TextContent(
                type="text",
                text=json.dumps(schema, indent=2)
            )]

        elif name == "create_note":
            note = storage.create_note(
                title=arguments["title"],
                content=arguments["content"],
                category=arguments["category"],
                type_tag=arguments["type"],
                priority=arguments["priority"],
                topics=arguments.get("topics")
            )
            return [TextContent(
                type="text",
                text=f"Note created successfully!\n\n{json.dumps(note, indent=2)}"
            )]

        elif name == "update_note":
            note = storage.update_note(
                note_id=arguments["id"],
                title=arguments.get("title"),
                content=arguments.get("content"),
                category=arguments.get("category"),
                type_tag=arguments.get("type"),
                priority=arguments.get("priority"),
                topics=arguments.get("topics")
            )
            return [TextContent(
                type="text",
                text=f"Note updated successfully!\n\n{json.dumps(note, indent=2)}"
            )]

        elif name == "delete_note":
            storage.delete_note(arguments["id"])
            return [TextContent(
                type="text",
                text=f"Note '{arguments['id']}' deleted successfully"
            )]

        elif name == "read_note":
            note = storage.read_note(arguments["id"])
            return [TextContent(
                type="text",
                text=json.dumps(note, indent=2)
            )]

        elif name == "find_notes_by_tags":
            notes = storage.find_notes(
                category=arguments.get("category"),
                type_tag=arguments.get("type"),
                priority=arguments.get("priority"),
                topics=arguments.get("topics"),
                title_contains=arguments.get("title_contains"),
                created_after=arguments.get("created_after"),
                created_before=arguments.get("created_before"),
                updated_after=arguments.get("updated_after"),
                updated_before=arguments.get("updated_before")
            )

            if not notes:
                return [TextContent(
                    type="text",
                    text="No notes found matching the criteria"
                )]

            return [TextContent(
                type="text",
                text=f"Found {len(notes)} note(s):\n\n{json.dumps(notes, indent=2)}"
            )]

        elif name == "list_tags":
            tag_counts = storage.list_tags()
            return [TextContent(
                type="text",
                text=json.dumps(tag_counts, indent=2)
            )]

        elif name == "add_tags_to_schema":
            schema = storage.add_tags_to_schema(
                dimension=arguments["dimension"],
                tags=arguments["tags"]
            )
            return [TextContent(
                type="text",
                text=f"Tags added successfully to '{arguments['dimension']}' dimension!\n\n{json.dumps(schema, indent=2)}"
            )]

        elif name == "export_note_to_markdown":
            file_path = storage.export_note_to_markdown(
                note_id=arguments["id"],
                output_path=arguments.get("output_path")
            )
            return [TextContent(
                type="text",
                text=f"Note exported successfully to: {file_path}"
            )]

        elif name == "export_all_notes_to_markdown":
            files = storage.export_all_notes_to_markdown(
                output_dir=arguments.get("output_dir")
            )
            return [TextContent(
                type="text",
                text=f"Exported {len(files)} note(s) to markdown files:\n\n" + "\n".join(files)
            )]

        else:
            return [TextContent(
                type="text",
                text=f"Unknown tool: {name}"
            )]

    except Exception as e:
        return [TextContent(
            type="text",
            text=f"Error: {str(e)}"
        )]


async def main():
    """Run the MCP server."""
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
