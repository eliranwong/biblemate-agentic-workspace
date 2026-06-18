# Antigravity Bible Study Agents

Welcome to the **Antigravity Bible Study Agents** ecosystem. This repository is configured specifically as a local workspace extension for the **Google Antigravity** agentic development platform, featuring an integrated team of 9 customized agent personas, 36 standalone exegesis/theology skills, and 36 custom slash commands.

This repository works with all antigravity platform, Antigravity, Antigravity IDE, Antigravity CLI. Official downloads at: https://antigravity.google/download

---

## Directory Structure

All agentic configurations are self-contained under the `.agents/` folder at the root:

```
.agents/
├── agents.md             # Custom AI team personas and guidelines
├── skills/               # Standalone, modular exegesis and study skills
│   ├── outline/
│   ├── sermon/
│   ├── translate_greek/
│   └── ... (36 total skills)
└── workflows/            # Parameterized slash command workflows
    ├── outline.md
    ├── sermon.md
    └── ... (36 total slash commands)
```

---

## Setup & How to Use with Google Antigravity

Because this repository uses the standard Antigravity workspace configuration schema, there is **zero manual setup or registration required** to load the agents, skills, and workflows.

1. **Open Workspace**: Open the workspace root directory in your Antigravity-integrated IDE (such as Cursor or VS Code configured with the Antigravity extension) or run the CLI inside this directory:
   ```bash
   agy
   ```
2. **Auto-Discovery**: Antigravity automatically detects the `.agents/` directory at the project root. It will:
   - Load the 9 custom personas from `agents.md` into the agent selection registry.
   - Register the 35 skills in `.agents/skills/` for progressive disclosure (they will be loaded dynamically into the context when a user request matches their description).
   - Expose the 35 workflow files in `.agents/workflows/` as native slash commands.

3. **Running Slash Commands**: In the Antigravity chat input, type `/` to bring up the commands menu, followed by arguments (e.g. references, topics, or words):
   - `/outline Ephesians 1`
   - `/sermon Romans 8:28`
   - `/translate_greek John 1:1`

For a full reference of all available slash commands and usage examples, see the [Slash Commands Reference Guide](docs/slash_commands.md).

---

## The AI Team Personas

The ecosystem configures a team of 9 specialized personas defined in [.agents/agents.md](.agents/agents.md):
- **Billy Graham Persona**: Warm, earnest, direct evangelistic speaker.
- **Context Analyst David**: Specializes in historical-emotional analysis of the Psalms and David's life.
- **Biblical Content Interpreter**: Evaluates contemporary culture and articles from a Gospel-focused worldview.
- **Compassionate Pastor**: Focuses on pastoral advice, study questions, and intercessory prayers in the first person.
- **Verse Scripter**: Specializes in compiling and referencing lists of Bible verses and promises.
- **Oxford Bible Scholar**: Rigorous, academic, historical-grammatical exegesis and structural outlines.
- **Cambridge Theologian**: Systematic, doctrinal, and redemptive-historical analysis.
- **Biblical Translator**: Focuses on literal contextual translation, morphology mapping, and biblical dialect.
- **AI Agent Creator**: Meta-agent designed to construct new, safe Bible study agent descriptions.