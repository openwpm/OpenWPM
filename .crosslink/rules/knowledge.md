## Knowledge Management

The project has a shared knowledge repository for saving and retrieving research, codebase patterns, and reference material across agent sessions.

### Before Researching

Before performing web research or deep codebase exploration on a topic, check if knowledge already exists:

```bash
crosslink knowledge search '<query>'
```

If relevant pages exist, read them first to avoid duplicating work.

### After Performing Web Research

When you use WebSearch, WebFetch, or similar tools to research a topic, save a summary to the knowledge repo:

```bash
crosslink knowledge add <slug> --title '<descriptive title>' --tag <category> --source '<url>' --content '<summary of findings>'
```

- Use a short, descriptive slug (e.g., `rust-async-patterns`, `jwt-refresh-tokens`)
- Include the source URL so future agents can verify or update the information
- Write the content as a concise, actionable summary — not a raw dump

### Updating Existing Knowledge

If a knowledge page already exists on a topic, update it rather than creating a duplicate:

```bash
crosslink knowledge edit <slug> --append '<new information>'
```

Add new sources when updating:

```bash
crosslink knowledge edit <slug> --append '<new findings>' --source '<new-url>'
```

### Documenting Codebase Knowledge

When you discover important facts about the project's own codebase, architecture, or tooling, save them as knowledge pages for future agents:

- Build and test processes
- Architecture patterns and conventions
- External API integration details and gotchas
- Deployment and infrastructure notes
- Common debugging techniques for the project

```bash
crosslink knowledge add <slug> --title '<topic>' --tag codebase --content '<what you learned>'
```
