# Note Format Reference

Load this file when generating a full note draft or revising note structure and formatting.

## Obsidian Vault Workflow

When the user is working inside an Obsidian vault:

- ask for the target save path or note name before generating the final note unless it is already specified;
- write the note directly to that target file;
- preserve existing vault conventions if they are visible from nearby notes;
- use Obsidian wikilinks such as `[[笔记名]]` for internal note references.

If the note is related to existing notes, establish bidirectional links when it is useful and low-risk:

- add outgoing wikilinks in the new note;
- do not edit related notes to add backlinks unless the user explicitly instructs you to do so.

## Output Language And Tone

- Use simplified Chinese by default.
- Maintain an academic, professional, and objective tone.
- Keep explanations precise, compact, and logically connected.

## Formula Rules

- Use LaTeX only for mathematics, statistics, physics, engineering, or other concepts that benefit from formal notation.
- Use `$...$` for inline formulas.
- Use `$$...$$` for display formulas.
- Do not wrap ordinary non-technical phrases in LaTeX.

## Required Metadata

The note must begin with exactly these two lines:

```text
建议标题：[简明扼要的标题]
Tags: [标签1] [标签2] [标签3]
```

Choose tags that cover both the core concept and nearby related domains.

If the vault already uses frontmatter properties and the surrounding notes make that convention clear, preserve the local convention. Otherwise keep the required title and `Tags:` lines as the default.

## Heading Structure

- Start the main body with a level-1 heading.
- Follow heading levels strictly without skipping levels.
- Do not add numbering to headings.
- Do not bold headings.
- Do not use horizontal rules.
- Make the first section establish background, macro framework, and why the topic matters.

## Writing Style For Body Content

- Prefer substantial explanatory paragraphs over fragmented bullet lists.
- Add transition paragraphs between sections so the logic feels cumulative rather than assembled.
- Make each section readable by a third party without relying on chat context.
- Combine macro framing with micro-level detail.

## Internal Linking

For links inside the vault:

- use `[[Note Name]]` by default;
- use `[[Note Name|显示文本]]` when the displayed wording should read more naturally;
- link to existing concept notes, prerequisite notes, or application notes when those relationships help navigation.

Only create backlinks in other notes when the relationship is specific enough that a human maintainer would likely keep that link.

## Callouts

Use Obsidian callouts sparingly for definitions, best practices, common pitfalls, or examples.

Supported pattern:

```text
> [!type]+ 标题
> 内容
```

Common `type` values: `note`, `info`, `tip`, `important`, `warning`, `example`.

Aim to include at least one practical guidance block or pitfall reminder in each major section when it adds value.

## Long Responses

If the note is too long to finish in one response, end with:

```text
[内容未完，请回复'继续'以获取剩余部分]
```

## Final References Section

The last section must be:

```markdown
# 参考
```

List sources as unordered bullets.

- For papers, use a compact Nature-like style and include a DOI link when available.
- For webpages, provide the page title and access date.

## Revision Output Rules

When revising an existing note:

- output only the changed block unless the user explicitly requests full regeneration;
- state the exact insertion or replacement location before the content;
- keep the rest of the note untouched unless the change logically propagates.

If the revision is requested as a file edit inside the vault, apply the change directly to the target note and only summarize the edit in chat.
