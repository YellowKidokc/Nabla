# Consilience Atlas Local Workbench

This is the first React shell over the existing Nabla / method-comparison / Atlas rails.
It is intentionally a **Candidate sandbox**. Running a paper here does not admit claims,
promote grades, or create accepted bridges.

## Start it

Terminal 1, from the repository root:

```bash
python -m meta.workbench_server
```

Terminal 2:

```bash
cd gui
npm install
npm run dev
```

Open `http://localhost:5173`.

## What v0.1 does

1. Load or paste Markdown, text, HTML, or JSON.
2. Choose DeepSeek, OpenAI, or local-only analysis.
3. The Python bridge runs the existing `method_comparison` pipeline.
4. Local NLP and external API lanes receive the same frozen source/contract and execute independently.
5. The UI shows the run receipt and method comparison.
6. A human review remains an independent overlay and can be exported as JSON.
7. Gold-001 can be opened directly from the existing canonical AtlasRecord fixture.

## What v0.1 deliberately does not claim

- It does not yet convert arbitrary method-comparison stage output into a full AtlasRecord atom stack.
- It does not promote Candidate objects to Admitted.
- It does not compute a new native grade.
- It does not create or admit Phi bridges.
- It does not persist human review into the canon ledger automatically.

Those are separate gates. The next adapter should map the existing lane output into the existing
`AtlasRecord v1` contract rather than inventing another claim schema.

## Environment

For external lanes set one of:

```text
DEEPSEEK_API_KEY
OPENAI_API_KEY
```

No secret is stored by the React app or committed to the repository.
