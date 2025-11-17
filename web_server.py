#!/usr/bin/env python3
"""
Flask-based Wiki Frontend for MCP Notes
A simple web interface to view and navigate your notes.
"""

from flask import Flask, render_template, request, redirect, url_for
from datetime import datetime
from pathlib import Path
import json
import re
from collections import defaultdict

# Reuse the storage path from server.py
NOTES_FILE = Path(__file__).parent / "notes.json"

app = Flask(__name__)


def load_notes():
    """Load notes from JSON file."""
    if not NOTES_FILE.exists():
        return {"tag_schema": {}, "notes": []}

    with open(NOTES_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)


def find_wikilinks(content):
    """Extract [[wiki links]] from content."""
    pattern = r'\[\[([^\]]+)\]\]'
    return re.findall(pattern, content)


def render_wikilinks(content, all_notes):
    """Convert [[Note Title]] to clickable links."""
    # Create a map of titles to IDs
    title_to_id = {note['title']: note['id'] for note in all_notes}

    def replace_link(match):
        title = match.group(1)
        if title in title_to_id:
            note_id = title_to_id[title]
            return f'<a href="/note/{note_id}" class="wikilink">{title}</a>'
        else:
            return f'<span class="wikilink-missing">{title}</span>'

    pattern = r'\[\[([^\]]+)\]\]'
    return re.sub(pattern, replace_link, content)


def get_backlinks(note_id, all_notes):
    """Find all notes that link to this note."""
    target_note = next((n for n in all_notes if n['id'] == note_id), None)
    if not target_note:
        return []

    target_title = target_note['title']
    backlinks = []

    for note in all_notes:
        if note['id'] != note_id:
            links = find_wikilinks(note['content'])
            if target_title in links:
                backlinks.append(note)

    return backlinks


def get_tag_counts(notes):
    """Count usage of each tag."""
    counts = {
        'category': defaultdict(int),
        'type': defaultdict(int),
        'priority': defaultdict(int),
        'topics': defaultdict(int)
    }

    for note in notes:
        tags = note.get('tags', {})
        if 'category' in tags:
            counts['category'][tags['category']] += 1
        if 'type' in tags:
            counts['type'][tags['type']] += 1
        if 'priority' in tags:
            counts['priority'][tags['priority']] += 1
        for topic in tags.get('topics', []):
            counts['topics'][topic] += 1

    return counts


@app.route('/')
def index():
    """Home page with recent notes and tag cloud."""
    data = load_notes()
    notes = data['notes']

    # Sort by most recently updated
    notes_sorted = sorted(notes, key=lambda n: n['updated'], reverse=True)

    tag_counts = get_tag_counts(notes)

    return render_template('index.html',
                         notes=notes_sorted[:20],  # Show 20 most recent
                         tag_counts=tag_counts,
                         total_notes=len(notes))


@app.route('/note/<note_id>')
def view_note(note_id):
    """View a single note with backlinks."""
    data = load_notes()
    notes = data['notes']

    note = next((n for n in notes if n['id'] == note_id), None)
    if not note:
        return "Note not found", 404

    # Convert markdown to HTML (basic implementation)
    import markdown
    content_html = markdown.markdown(note['content'], extensions=['fenced_code', 'tables'])

    # Add wikilinks
    content_html = render_wikilinks(content_html, notes)

    # Get backlinks
    backlinks = get_backlinks(note_id, notes)

    # Get outgoing links
    outgoing = find_wikilinks(note['content'])

    return render_template('note.html',
                         note=note,
                         content_html=content_html,
                         backlinks=backlinks,
                         outgoing_links=outgoing)


@app.route('/tag/<dimension>/<value>')
def view_tag(dimension, value):
    """View all notes with a specific tag."""
    data = load_notes()
    notes = data['notes']

    # Filter notes by tag
    filtered = []
    for note in notes:
        tags = note.get('tags', {})
        if dimension == 'topics':
            if value in tags.get('topics', []):
                filtered.append(note)
        elif tags.get(dimension) == value:
            filtered.append(note)

    # Sort by most recently updated
    filtered_sorted = sorted(filtered, key=lambda n: n['updated'], reverse=True)

    return render_template('tag.html',
                         dimension=dimension,
                         value=value,
                         notes=filtered_sorted)


@app.route('/search')
def search():
    """Search notes by title or content."""
    query = request.args.get('q', '').lower()

    if not query:
        return redirect(url_for('index'))

    data = load_notes()
    notes = data['notes']

    # Simple text search
    results = []
    for note in notes:
        if (query in note['title'].lower() or
            query in note['content'].lower()):
            results.append(note)

    results_sorted = sorted(results, key=lambda n: n['updated'], reverse=True)

    return render_template('search.html',
                         query=query,
                         results=results_sorted)


@app.route('/all')
def all_notes():
    """View all notes alphabetically."""
    data = load_notes()
    notes = sorted(data['notes'], key=lambda n: n['title'].lower())

    return render_template('all.html', notes=notes)


@app.template_filter('datetime')
def format_datetime(value):
    """Format ISO datetime for display."""
    try:
        dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
        return dt.strftime('%Y-%m-%d %H:%M')
    except:
        return value


if __name__ == '__main__':
    print("Starting MCP Notes Wiki Frontend...")
    print("Visit http://localhost:5000")
    app.run(debug=True, port=5000)
