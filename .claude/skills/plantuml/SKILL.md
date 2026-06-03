---
name: plantuml
description: "Use when: generating UML diagrams, creating visual documentation, or rendering PlantUML code. Provides templates, syntax guides, and rendering helpers for class, object, use-case, sequence, state, and deployment diagrams."
trigger: "TRIGGER when: user asks for UML diagrams, visualization, or PlantUML; code includes plantuml/uml generation; user wants to document architecture"
---

# PlantUML Skill

Professional diagram generation for software architecture, data models, workflows, and system design. PlantUML converts plain-text specifications into publication-quality UML diagrams.

## Quick Start

### 1. Choose Diagram Type
- **Class Diagram**: Object-oriented structure, relationships, inheritance
- **Object Diagram**: Runtime instances and relationships
- **Use-Case Diagram**: System boundaries, actors, interactions
- **Sequence Diagram**: Message flows and interactions over time
- **State Diagram**: State machines and transitions
- **Deployment Diagram**: Infrastructure and deployment

### 2. Write PlantUML Code
Create a `.puml` file with your diagram definition.

### 3. Render
```bash
plantuml -Tpng diagram.puml -o output.png
plantuml -Tsvg diagram.puml -o output.svg
```

---

## Diagram Templates

### Class Diagram
Best for: OOP architecture, data models, API design

```plantuml
@startuml
!theme plain

class Entity {
  - id: int
  - createdAt: datetime
  --
  + getId(): int
  + setId(id): void
}

class Report {
  - title: String
  - content: String
  --
  + getTitle(): String
  + getContent(): String
}

class DataProcessor {
  - {abstract} process(): void
}

Entity <|-- Report : extends
DataProcessor o-- Report : processes
@enduml
```

**Key symbols**:
- `-` private, `+` public, `#` protected, `~` package
- `<|--` inheritance
- `--` association
- `o--` aggregation
- `*--` composition
- `<|..` interface implementation

### Object Diagram
Best for: Runtime instances, concrete states, relationships

```plantuml
@startuml
object user1 {
  name = "Alice"
  id = 101
  role = "Admin"
}

object report1 {
  title = "Q1 Report"
  status = "published"
}

object processor1 {
  type = "DataProcessor"
  status = "idle"
}

user1 --> report1 : creates
processor1 --> report1 : processes
@enduml
```

### Use-Case Diagram
Best for: System boundaries, user interactions, feature scope

```plantuml
@startuml
left to right direction

actor User
actor Admin
usecase UC1 as "Extract Data"
usecase UC2 as "Transform Data"
usecase UC3 as "Export Report"
usecase UC4 as "Manage Access"

User --> UC1
UC1 --> UC2
UC2 --> UC3
Admin --> UC4
User --> UC4 : (optional)

UC2 .> UC3 : includes
@enduml
```

**Relationships**:
- `-->` basic association
- `.>` extends
- `--|>` includes

### Sequence Diagram
Best for: Message flows, interactions, API calls

```plantuml
@startuml
participant Client
participant API
participant Database

Client -> API: POST /extract
activate API
API -> Database: query(report_id)
activate Database
Database --> API: data[]
deactivate Database
API --> Client: 200 OK
deactivate API
@enduml
```

### State Diagram
Best for: Workflows, state machines, process flows

```plantuml
@startuml
[*] --> Idle
Idle --> Processing : start()
Processing --> Validating : validate()
Validating --> Success : pass
Validating --> Failed : fail
Success --> [*]
Failed --> Idle : retry()
@enduml
```

---

## Workflow: From Code to Diagram

### Step 1: Analyze Architecture
Read the codebase, identify classes, relationships, responsibilities.

### Step 2: Create `.puml` File
```bash
mkdir -p docs/diagrams
touch docs/diagrams/architecture.puml
```

### Step 3: Write PlantUML Syntax
Document your design in plain text.

### Step 4: Render
```bash
plantuml -Tsvg docs/diagrams/architecture.puml -o docs/diagrams/architecture.svg
```

### Step 5: Embed in Documentation
Link diagrams in `README.md` or documentation files:
```markdown
## Architecture

![Class Diagram](docs/diagrams/architecture.svg)
```

---

## PlantUML Features

### Styling
```plantuml
@startuml
skinparam backgroundColor #FEFEFE
skinparam classBackgroundColor #F0F0F0
skinparam classBorderColor #333333

class MyClass {
  data: String
}
@enduml
```

### Namespaces
```plantuml
@startuml
package "com.myapp.models" {
  class User
  class Report
}

package "com.myapp.services" {
  class UserService
}
@enduml
```

### Multiplicity
```plantuml
@startuml
class User
class Report

User "1" --> "*" Report : creates
@enduml
```

---

## Rendering Options

```bash
# PNG (raster, smaller file)
plantuml -Tpng file.puml -o output.png

# SVG (vector, scalable, interactive)
plantuml -Tsvg file.puml -o output.svg

# PDF
plantuml -Tpdf file.puml -o output.pdf

# ASCII art (terminal)
plantuml -Ttxt file.puml -o output.txt

# Batch render all diagrams
for f in *.puml; do plantuml -Tsvg "$f"; done
```

---

## Best Practices

✅ **DO**:
- Keep diagrams focused (one responsibility per diagram)
- Use consistent naming conventions
- Include legends or notes for complex diagrams
- Version control `.puml` files (small, text-based)
- Embed diagrams in documentation

❌ **DON'T**:
- Create monolithic diagrams showing everything
- Forget to document what the diagram represents
- Use confusing color schemes
- Commit rendered images without source `.puml`

---

## Common Tasks

### Task: Generate class diagram for Python module
1. Read Python source files
2. Extract classes, methods, relationships
3. Create `.puml` with class definitions
4. Render to `docs/diagrams/`

### Task: Create use-case diagram from requirements
1. Identify actors (User, Admin, External System)
2. List use cases (what the system does)
3. Draw relationships and boundaries
4. Render for stakeholder review

### Task: Document data model
1. Identify entities and fields
2. Define relationships (1:1, 1:N, M:N)
3. Create class diagram with attributes
4. Render as architecture reference

---

## Integration with OOP Expert

Use PlantUML skill alongside `/oop-expert` agent:
1. **oop-expert reviews** your architecture
2. **plantuml skill generates** diagrams
3. **Both contribute** to documentation and validation

---

## Resources

- **Official**: https://plantuml.com/
- **Syntax Guide**: https://plantuml.com/guide
- **Real-world Examples**: https://plantuml.com/en/example

---

You're ready to create professional UML diagrams for documentation and architecture communication.
