# AI Agentic Software Testing Thesis

A LangGraph-based AI testing agent that autonomously generates, executes, and evaluates REST API tests. Compared against traditional testing frameworks (Robot Framework, Pytest + HTTPX, Schemathesis) as part of a master's thesis experiment.

---

## Repositories

| Repo | Description |
|---|---|
| `agentic-testing-thesis` | This repo AI agent, comparison frameworks, metrics |
| `fastapi-target-thesis` | Python FastAPI target application with seeded bugs |
| `springboot-targe-thesis` | Java Spring Boot target application with seeded bugs |

---



---

## Prerequisites

- Python 3.11+
- [uv](https://astral.sh/uv) package manager
- Docker Desktop
- Anthropic API key

---

## Setup

### 1. Clone the repo

```bash
git clone https://github.com/Tissinapa/agentic-testing-system-thesis.git
cd agentic-testing-system-thesis
```

### 2. Create virtual environment

```bash
uv venv .venv

# Activate Windows
.venv\Scripts\activate

# Activate Linux
source .venv/bin/activate
```

### 3. Install dependencies

```bash
uv pip install -e .
```

### 4. Configure environment

```bash
cp .env.example .env
```

Edit `.env` and add your Anthropic API key:

```
ANTHROPIC_API_KEY=your_key_here
```

---

## Running the Target Applications

Both target apps run via Docker Compose. Start them in separate terminals:

```bash
# FastAPI (Python) — http://localhost:8000
cd /path/to/fastapi-target-thesis
docker compose up

# Spring Boot (Java) — http://localhost:8080
cd /path/to/springboot-targe-thesis
docker compose up
```

Swagger UI:
- Python: `http://localhost:8000/docs`
- Java: `http://localhost:8080/swagger-ui.html`

---

## Running the Agent

### CLI for python target testing

```bash
# Black-box API testing only
python -m agent.run --target python --base-url http://localhost:8000 --spec-url http://localhost:8000/openapi.json --max-iterations 1 --token-budget 30000
# White-box source code analysis only
python -m agent.run --target python --base-url http://localhost:8000 --spec-url http://localhost:8000/openapi.json --mode white --requirements docs/requirements_python.md --source-code path\to\fastapi-target-thesis\app\routers\tasks.py --token-budget 10000
# Hybrid both
python -m agent.run --target python --base-url http://localhost:8000 --spec-url http://localhost:8000/openapi.json --mode hybrid --requirements docs/requirements_python.md --source-code path\to\fastapi-target-thesis\app\routers\tasks.py --token-budget 30000


```

### CLI for java target testing

``` bash
# Black-box API testing only
python -m agent.run --target java --base-url http://localhost:8080 --spec-url http://localhost:8080/v3/api-docs --mode black --requirements docs/requirements_java.md--token-budget 30000
# White-box source code analysis only
python -m agent.run --target java --base-url http://localhost:8080 --spec-url http://localhost:8080/v3/api-docs --mode white --requirements docs/requirements_java.md --source-code path\to\springboot-targe-thesis\src\main\java\com\example\springboottargethesis\controller\TaskController.java --token-budget 10000
# Hybrid both
python -m agent.run --target java --base-url http://localhost:8080 --spec-url http://localhost:8080/v3/api-docs --mode hybrid --requirements docs/requirements_java.md --source-code path\to\springboot-targe-thesis\src\main\java\com\example\springboottargethesis\controller\TaskController.java --token-budget 30000

```


### CLI arguments

| Argument | Required | Description |
|---|---|---|
| `--target` | Yes | `python`, `java`, `python_os`, `java_os` |
| `--base-url` | Yes | Base URL of the target application |
| `--spec-url` | Yes | OpenAPI spec URL |
| `--mode` | No | `black` (default), `white`, `hybrid` |
| `--max-iterations` | No | Max agent loop iterations (default: 1) |
| `--token-budget` | No | Max tokens per run (default: 10000) |
| `--requirements` | No | Path to requirements markdown file |
| `--source-code` | No | Path to source code file (white/hybrid) |

python_os and java_os are only for gathering results from open-source projects. Open source projects need separate requirements.md files
### Streamlit UI

```bash
streamlit run ui/app.py
```

---

## Running Comparison Frameworks

### Robot Framework

```bash
# Python app
uv run robot --outputdir results/robot/pythonAPI tests/robot/python_api.robot

# Java app
uv run robot --outputdir results/robot/javaAPI tests/robot/java_api.robot
```

### Pytest + HTTPX

```bash
pytest tests/pytest/test_python_api.py -v \
  --json-report \
  --json-report-file=results/pytest/python_results.json
```

### Schemathesis

```bash
# Python app
uv run schemathesis run http://localhost:8000/openapi.json \
  --checks all \
  -H "Authorization: Bearer Taman-ei-p1t1a1s-0lla-na1n-123" \
  --report junit \
  --report-dir results/schemathesis/python

# Java app
uv run schemathesis run http://localhost:8080/v3/api-docs \
  --checks all \
  -H "Authorization: Bearer validation-token-123" \
  --report junit \
  --report-dir results/schemathesis/java
```

---

## Metrics and Results

### Collect and compare all results

```bash
python metrics/collect.py
python metrics/compare.py
```

### Export to Excel

```bash
# Main comparison metrics
python metrics/export_excel.py
# Output: results/thesis_metrics.xlsx

# Agent evaluation details with LLM reasoning
python metrics/parse_agent_results.py
# Output: results/agent_evaluations.xlsx

# Seeded bug catalogue
python metrics/create_bug_tables.py
# Output: results/thesis_bugs_and_evaluations.xlsx
```

---

## Running Tests

```bash
pytest tests/ -v
```
If you get windows error 5 access denied, use this command to run all tests. Delete temp folder afterwards
```bash
pytest tests/ -v --basetemp=./tmp
```
---


### Testing modes

| Mode | What it does | Best for |
|---|---|---|
| Black | HTTP requests against running API | Functional and security testing |
| White | Static source code analysis | Code review, security audit |
| Hybrid | Both API testing and code analysis | Deepest coverage |

---

