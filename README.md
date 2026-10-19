# ao-pylori

Name-taking: `ao-pylori` is an AO family repository (cloud-itonami `ao-*` bound
agent repos, cf. `ao-hiraku`) for the global H. pylori (Helicobacter pylori)
control programme. It holds the durable source of the `pylori-*` Hermes bot
profiles under `hermes/profiles/<name>/` (registry index:
`com-junkawasaki/root/manifest/agent-registry.edn`).

## Family

| profile | domain | cadence |
|---|---|---|
| pylori-program | programme coordination, cross-domain gaps | daily |
| pylori-formulary | 製剤: eradication formulary catalog (regimens, dosage forms, resistance context) | weekly |
| pylori-pharmacy | 薬剤師管理: pharmacist workflow assets (dispensing SOP, medication review, adherence, pharmacovigilance schemas) | weekly |
| pylori-distribution | 配布: demand estimation, allocation plans, stock ledger schema, direct-first procurement candidates | weekly |
| pylori-testing | 検査: diagnostics catalog (UBT, stool antigen, serology, rapid urease, culture/AST, molecular), test-and-treat algorithms, QC | weekly |

## Boundary (this is a design invariant)

These bots organise knowledge and plans only. They do not prescribe, dispense,
diagnose, order or run tests, manufacture, purchase, pay, ship goods, handle
patient-identifiable data, or contact patients or providers. Clinical and
regulatory acts are licensed human work. Every capability decision is in each
profile's `yakuwari.edn` (unlisted = blocked); `SOUL.md` only points at it.

## Source of truth

- `hermes/profiles/<name>/` here is the durable source. The running copy on the
  host is `~/.hermes/profiles/<name>/` (Hermes runtime).
- `.env` (API keys) exists on the host only and is never committed
  (secret policy: ADR-2609241900, secrets live in kagi; repo holds references).
- Catalogs start empty on purpose: entries require a quoted source with URL and
  retrieved date (`workspace/sources.edn`). `:url :unverified` is UNVERIFIED,
  not valid.
- Measurement of record: `scripts/<name>_evidence.py` (read-only, local files,
  no network). `workspace/ledger.jsonl` is append-only.

## Regenerating profiles

`scripts/gen-profiles.py` writes both the repo copy and the host copy from one
spec table. Edit the spec, re-run, then re-register cron jobs if prompts changed.
