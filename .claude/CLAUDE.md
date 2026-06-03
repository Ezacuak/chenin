# Data Mining from Génie200 Reports

Instructions here apply to this project and are shared with team members.

## Project Goal

Extract structured data from **Génie200** reports → transform into **pandas DataFrames** → format for downstream R analysis.

---

## Workflow Phases

### Phase 1: Prototyping (Jupyter Notebooks)
**Goal**: Manual exploration and validation. Understand what data you have.

**Your preferences**:
- Minimal AI assistance—you drive discovery
- Focus: hands-on testing, pattern recognition, data inspection
- Output: validated extraction logic + DataFrame schemas

**Claude's role** (only if you ask):
- Answer "why" questions about pandas/regex patterns you're trying
- Debug specific extraction failures when you're stuck
- Never refactor or redesign without your explicit request

**Checkpoints**:
- [ ] Can consistently extract key fields from Génie200 reports
- [ ] DataFrame schema is stable and documented
- [ ] Test coverage includes edge cases you've found

### Phase 2: Architecture & Design Patterns
**Goal**: Build production-ready code foundations.

**Triggers architecture work when**:
- Prototyping phase is complete (schema + logic proven)
- You're ready to move beyond notebooks
- Complexity warrants object design

**What we'll design**:
- Data model (classes/dataclasses for extracted entities)
- Extraction pipeline (modular, testable)
- DataFrame validation & type safety
- Error handling for malformed reports

**Claude's role** (on request):
- Propose design patterns suited to your extraction needs
- Review architecture decisions
- Help refactor notebook code into maintainable modules

### Phase 3: Output Formatting (R Integration)
**Goal**: Format DataFrames for R consumption.

**Scope**: TBD—coordinate when Phase 1 is complete.

---

## Data Extraction Pipeline

### Step 1: Report Parsing (Regex-Expert Agent)
Extract structured fields from Génie200 format using regex patterns.

**Use `/regex-expert` when you need to**:
- Analyze Génie200 report structure
- Build or debug regex patterns
- Extract lists of matches or complex nested patterns
- Combine regex with Python for stateful extraction

**Output**: List of dicts/tuples with named captures (e.g., `{'field_name': value, ...}`)

### Step 2: DataFrame Construction (Data-Transform Agent)
Convert extracted data → pandas DataFrame with proper types and validation.

**Use `/data-transform` when you need to**:
- Build DataFrames from regex match results
- Handle type conversions and missing values
- Validate data quality and constraints
- Optimize memory usage for large extractions

**Output**: Validated pandas DataFrame ready for analysis or export

---

## During Prototyping

**Notebook workflow**:
```python
# In Jupyter: manual extraction, testing, schema design
import pandas as pd
import re

# Your iterative exploration here
# Once stable → promote to Phase 2 architecture
```

**Keep notebooks focused**:
- One notebook per report section or extraction task
- Document what you learned (why this pattern, edge cases found)
- Save stable schemas and test cases as comments

**When to ask for help**:
- "This regex pattern isn't matching edge case X"
- "How do I handle this data type in pandas efficiently?"
- "I'm seeing inconsistencies in the report format—should I..."
- NOT: "Refactor this for me" (save that for Phase 2)

---

## Architecture Phase Checklist

When you're ready to design (triggered by Phase 1 completion):

- [ ] Define data entities (classes for Report, Section, Field, etc.)
- [ ] Design extraction pipeline (modular stages)
- [ ] Plan DataFrame validation (schema, constraints, type checks)
- [ ] Organize code structure (extraction/, processing/, validation/)
- [ ] Add unit tests (test fixtures with real/sample reports)
- [ ] Document assumptions (field formats, optional fields, edge cases)

---

## Key Files & Patterns

**Phase 1** (Prototyping):
- `notebooks/extraction_*.ipynb` — exploration & validation
- `data/sample_reports/` — test data

**Phase 2** (Architecture):
- `src/extraction/` — regex patterns + parsing logic
- `src/models/` — dataclasses/Pydantic for entities
- `src/processing/` — DataFrame construction & validation
- `tests/` — unit tests for extraction & transformation
- `docs/schema.md` — DataFrame schema documentation

---

## CS Student Workflow Note

Your approach (prototype → design) is professional best practice:
1. **Prototyping** = understand the problem
2. **Design** = solve it sustainably

Avoid the trap of over-engineering before you understand what you're extracting. Phase 1 informs Phase 2. This makes your code more robust and your designs simpler.

---

## Agents Available

- **`/regex-expert`**: Regex pattern design, text extraction, parsing
- **`/data-transform`**: pandas DataFrames, data cleaning, type handling

Use them strategically—they're tools for when you're ready to accelerate, not for doing the thinking.

