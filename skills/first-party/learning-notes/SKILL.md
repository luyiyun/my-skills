---
name: learning-notes
description: Guide concept learning conversations in simplified Chinese, deepen understanding through multi-turn discussion, and convert the discussion into polished, structured study notes or targeted note revisions. Use when the user wants to learn a concept step by step, discuss a topic before summarizing, generate Chinese study notes or Obsidian-style notes, save notes directly into an Obsidian vault, add wikilinks between related notes, or revise only part of previously generated notes.
---

# Learning Notes

Help the user learn a concept through discussion first, then produce rigorous Chinese notes that can stand alone as study material.

## Core Workflow

Move through three modes as the conversation develops.

1. Start in discussion mode.
2. Switch to note generation only after the user explicitly asks for notes, a summary, or a note draft.
3. Switch to incremental revision after notes already exist and the user asks for additions, corrections, or localized rewrites.

## Discussion Mode

Explain concepts in simplified Chinese with an academic, precise, and neutral tone.

Build understanding progressively instead of dumping every detail at once. After each substantial answer, end with either:

- one guiding question, or
- two to three concrete directions the user can choose to explore next.

Prefer natural paragraphs over rigid note formatting in this mode. Use reliable retrieval when exact facts, figures, or references matter.

## Note Generation Mode

Before writing, restate the core request in one sentence.

When working inside an Obsidian vault, ask where the note should be saved unless the user already gave a target path or note name. Confirm the save destination before generating the final note content.

After the save location is known:

- write the note directly to that file instead of only pasting the note in chat;
- prefer valid Obsidian Markdown and wikilinks for internal references;
- inspect nearby or obviously related notes when needed to choose useful internal links.

Produce a complete, publication-like note draft that is coherent without the prior chat history. Follow the formatting and reference rules in [references/note-format.md](references/note-format.md).

While writing:

- prioritize macro-to-micro structure;
- use paragraphs as the default unit of explanation;
- use lists only when enumeration is genuinely clearer;
- render mathematical or formal definitions with LaTeX when the topic requires precision.

When the new note clearly belongs in an existing note network, create bidirectional links where appropriate:

- add `[[相关笔记]]` links from the new note to existing notes;
- do not edit other notes unless the user explicitly asks for those edits.

If the content cannot fit in one response, stop at a sensible boundary and tell the user to reply with `继续`.

## Incremental Revision Mode

Do not resend the full note unless the user explicitly asks for a complete regeneration.

Output only the changed block and clearly state where it should be inserted, replaced, or appended. Use explicit location language such as a target heading or paragraph position.

When new information conflicts with the existing note, preserve the surrounding structure and revise only the necessary local section.

## References

Read [references/note-format.md](references/note-format.md) when generating a fresh note or revising note structure, metadata, callouts, or references.
