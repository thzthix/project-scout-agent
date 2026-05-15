## Core Rules

- Keep the code understandable for a junior developer.
- Prefer small composable functions.
- Avoid large monolithic functions.
- Split functions when they start mixing multiple responsibilities.
- Do not hardcode secrets, model keys, or absolute file paths.
- Fail clearly if required config is missing.

## Agent Boundary Rules

- Keep search logic, evaluation logic, and workflow control separate.
- Let the model interpret evidence, but let code enforce policy, limits, and branching.
- Prefer deterministic pre-filtering before model-based evaluation.
- Do not let free-form model text directly decide workflow actions.

## Output and Tool Rules

- All model outputs used by the workflow must be schema-validated.
- Tools must return bounded, predictable data rather than large unstructured payloads.

