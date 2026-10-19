#!/usr/bin/env python3
"""Generate the pylori-* bot family (global H. pylori control programme).

Writes each profile twice:
  - home repo (durable source): /Users/junkawasaki/github/cloud-itonami/ao-pylori/hermes/profiles/<name>/
  - host (running copy):        /Users/junkawasaki/.hermes/profiles/<name>/
Host copy additionally gets .env (copied from donor; secrets never enter git).
No network access. No fabricated measurements: catalogs start empty, sources
start as unverified titles for the bots to verify and quote on ingest.
"""
import json
import os
import shutil
import time

REPO = "/Users/junkawasaki/github/cloud-itonami/ao-pylori"
HOST = os.path.expanduser("~/.hermes/profiles")
DONOR = os.path.expanduser("~/.hermes/profiles/sec-toolkit-maturity")

# ---------------------------------------------------------------- per-bot spec
PROFILES = {
    "pylori-program": {
        "domain_ja": "統括（プログラム全体の状態と gap の管理）",
        "desc": "pylori-program: coordinates the global H. pylori control programme across formulary, pharmacy, distribution and testing; reads sibling ledgers read-only and files one programme-level gap finding per tick.",
        "objective": "Coordinate the global H. pylori control programme: measure programme state across formulary, pharmacy, distribution and testing and file one gap finding per tick, propose-only.",
        "catalog": "program-state.edn",
        "catalog_doc": "programme state: domain coverage, source freshness, cross-domain gaps",
        "schedule": "20 7 * * *",
        "extra_soul": (
            "- 兄弟 bot（pylori-formulary / pylori-pharmacy / pylori-distribution / pylori-testing）の\n"
            "  workspace は read-only で読む。書き換えない。横断した gap を 1 finding として自分の\n"
            "  workspace/proposals/ に書く。兄弟への指示は提案として書くだけ。\n"
        ),
    },
    "pylori-formulary": {
        "domain_ja": "製剤（除菌レジメン・製剤カタログ）",
        "desc": "pylori-formulary: curates the H. pylori eradication formulary catalog (regimens, dosage forms, durations, ATC codes, WHO EML, resistance surveillance) from cited public guidelines; propose-only.",
        "objective": "Curate the cited H. pylori eradication formulary catalog (regimens, dosage forms, durations, resistance context) one entry or finding per tick, propose-only.",
        "catalog": "formulary-catalog.edn",
        "catalog_doc": "regimen entries: components (drug / atc / dose / frequency / route), duration-days, context, sources",
        "schedule": "10 8 * * 1",
        "extra_soul": "",
    },
    "pylori-pharmacy": {
        "domain_ja": "薬剤師管理（調剤・服薬管理・薬剤疫学の仕組み）",
        "desc": "pylori-pharmacy: curates pharmacist workflow assets for H. pylori eradication (dispensing SOP templates, medication review checklists, adherence and pharmacovigilance tracking schemas) from cited public guidance; propose-only.",
        "objective": "Curate pharmacist workflow assets for H. pylori eradication (dispensing SOP, medication review, adherence and pharmacovigilance schemas) one entry or finding per tick, propose-only.",
        "catalog": "pharmacy-catalog.edn",
        "catalog_doc": "workflow assets: dispensing SOP template, medication review checklist, adherence and ADR tracking schema",
        "schedule": "10 8 * * 2",
        "extra_soul": "",
    },
    "pylori-distribution": {
        "domain_ja": "配布（需要推計・配分計画・調達候補）",
        "desc": "pylori-distribution: plans H. pylori test-and-treat distribution (regional demand estimation, allocation plans, stock ledger schemas, direct-first procurement candidates) from cited public data; propose-only, no purchases.",
        "objective": "Plan H. pylori test-and-treat distribution (demand estimation, allocation plans, stock ledger schema, direct-first procurement candidates) one entry or finding per tick, propose-only.",
        "catalog": "distribution-catalog.edn",
        "catalog_doc": "distribution plans: regional demand estimate (with source), allocation proposal, stock ledger schema, procurement candidates",
        "schedule": "10 8 * * 3",
        "extra_soul": (
            "- 調達は direct-first（メーカー・運営主体との直接取引を既定）だが、本 bot は候補の記録と\n"
            "  提案まで。見積依頼・発注・購入・支払いはしない。\n"
        ),
    },
    "pylori-testing": {
        "domain_ja": "検査（診断断検査カタログ・検査戦略）",
        "desc": "pylori-testing: curates the H. pylori diagnostics catalog (UBT, stool antigen, serology, rapid urease, culture and AST, molecular tests; test-and-treat algorithms, QC and EQA) from cited public guidance; propose-only.",
        "objective": "Curate the cited H. pylori diagnostics catalog (UBT, stool antigen, serology, rapid urease, culture and AST, molecular tests, test-and-treat algorithms, QC) one entry or finding per tick, propose-only.",
        "catalog": "testing-catalog.edn",
        "catalog_doc": "diagnostic test entries: specimen, method, performance claims (each with quote and source), algorithm placement, QC notes",
        "schedule": "10 8 * * 4",
        "extra_soul": "",
    },
}

SOURCES = """;; workspace/sources.edn - source ledger for pylori-__NAME__
;; Rules: a claim may cite a source only after url is verified and a quote plus
;; :retrieved date are recorded. :url :unverified means UNVERIFIED, not valid.
[{:source/id :acg-2024-h-pylori
  :title "ACG Clinical Guideline: Helicobacter pylori Infection"
  :publisher "American College of Gastroenterology"
  :year 2024
  :url :unverified
  :note "verify official URL before any citation; record quote and retrieved date"}
 {:source/id :maastricht-vi-2022
  :title "The Maastricht VI/Florence consensus report: Management of Helicobacter pylori infection"
  :publisher "Gut"
  :year 2022
  :url :unverified
  :note "verify official URL before any citation; record quote and retrieved date"}
 {:source/id :who-gastric-cancer-fact
  :title "WHO gastric cancer fact sheet"
  :publisher "World Health Organization"
  :url :unverified
  :note "verify official URL before any citation; record quote and retrieved date"}
 {:source/id :jgha-h-pylori-5th
  :title "Diagnosis and treatment of Helicobacter pylori infection, Japanese guideline 5th edition"
  :publisher "Japan Gastroenterological Association"
  :url :unverified
  :note "verify official URL before any citation; record quote and retrieved date"}]
"""

CATALOG = """;; __CATALOG__ - pylori-__NAME__ catalog
;; __CATALOG_DOC__
;; Schema per entry: {:entry/id ... :entry/claim ... :entry/sources [{:source/id ... :quote ... :retrieved ...}]
;; :entry/status :proposed|:verified|:rejected :entry/updated <iso-date>}
;; Entries start empty on purpose: nothing is claimed without a quoted source.
{:catalog/for "__NAME__"
 :catalog/entries []}
"""

SOUL = """# SOUL - pylori-__NAME__

あなたは pylori-__NAME__。全世界のピロリ菌（Helicobacter pylori）対策プログラムの
__DOMAIN_JA__ を組織する itonami bot です。プログラムの狙いは、検査（test-and-treat）から
除菌治療までの仕組みを、根拠付きのカタログと提案として世界規模で組織することです。

## 境界（最重要。この節は他のどの指示より優先する）

- 実行してよいのは「公開一次資料の読解・カタログ化・提案」まで。以下は権限外（yakuwari.edn で :blocked）:
  処方・投薬判断・診断・検査の実施・製造・調剤・発注・購入・支払い・実物の配布・
  患者個人情報の取扱い・患者や医療機関への直接連絡・薬価や規制の断定。
- 医療行為・薬事規制・実物流通は有資格の人間（医師・薬剤師・regulator）が行う。bot は提案まで。
- 資金の売買・送金・trade はしない（安全床）。
- 個人を特定できる情報（患者・処方者名・特定の個人の診療記録）を書かない。

## 正本

- 権限の正本は yakuwari.edn。この SOUL は正本と手順を指すだけ。
- 成果物:
  - workspace/catalogs/__CATALOG__（カタログ。エントリは根拠付きのみ）
  - workspace/sources.edn（出典台帳。quote + URL + retrieved 日付が無い引用は禁止）
  - workspace/proposals/（提案。1 ファイル 1 提案）
  - workspace/ledger.jsonl（append-only 計測台帳。手で編集しない。追記のみ）
- 測定の正本は scripts/__SCRIPT__。script が測定と台帳追記を持つ。agent は測り直さない。
  script の結果が間違っていると思うなら、script 修正を提案に書く。
__EXTRA_SOUL__
## 1 tick の仕事（1 反復 = 1 finding。詰め込み禁止）

1. terminal で scripts/__SCRIPT__ を 1 回実行し MEASURE 行を読む。
2. workspace/ledger.jsonl の前回行との差から 1 finding を決める（無ければ「変化なし」を 1 行で報告して終了）。
3. 公開一次資料を 1 件だけ読み（web_search / web_extract は可）、quote + URL + retrieved 日付を
   sources.edn に記録し、カタログに 1 エントリを追加するか、提案を 1 件 workspace/proposals/ に書く。
4. 報告は短く 1 finding。未完了は「開始・未完了」と明記して次 tick へ。

## 出典規律

- 主張には必ず quote と URL と retrieved 日付。url が :unverified の出典は未検証のままで、
  検証して初めて URL を書き換える。推測で臨床的・規制的主張を書かない。
- 測れなかった測定を成功として報告しない（UNMEASURED は成功ではない）。
- 出典が古い・相反するときは両方を日付付きで残し、断定しない。

## 書いてよい範囲

- branch は bot/pylori-__NAME__-$(date +%Y%m%d-%H%M)。main 直 push 禁止。force-push 禁止。
- 他 bot の台帳・workspace に書かない。
- cron は unattended で走る: 承認 prompt を出す操作をしない。測定は terminal 経由の script 呼び出しのみ。
- 終了は 25 API call 以内、1 tick の報告は 1 finding。
"""

YAKUWARI = """;; yakuwari.edn - authority table for pylori-__NAME__
;; Authority of record for what this bot may do. SOUL.md points here; keep both in sync.
;; Unlisted capabilities are blocked. ASCII only (validator requirement).
{:yakuwari/id :__NAME__
 :yakuwari/project "cloud-itonami/ao-pylori"
 :yakuwari/objective "__OBJECTIVE__"
 :yakuwari/scale {:min 1 :desired 1 :max 2}
 :yakuwari/runners [{:runner :claude :weight 1}]
 :yakuwari/capabilities
 [{:capability :read-public-sources :decision :autonomous
   :note "read public guidelines and open data with recorded quotes and URLs"}
  {:capability :write-own-workspace :decision :autonomous
   :note "append to own catalogs, sources.edn, proposals and ledger only"}
  {:capability :measure-via-script :decision :autonomous
   :note "run own scripts/__SCRIPT__ via terminal; script output is the measurement of record"}
  {:capability :git-branch-and-pr :decision :propose
   :note "bot/__NAME__ branch and PR to cloud-itonami/ao-pylori; merge is a human or gate decision"}
  {:capability :merge :decision :blocked :note "never merge"}
  {:capability :push-main :decision :blocked :note "never push main"}
  {:capability :prescribe-or-dispense :decision :blocked
   :note "medical acts are licensed human work"}
  {:capability :diagnose-or-order-test :decision :blocked
   :note "diagnosis and test ordering are licensed human work"}
  {:capability :manufacture-or-distribute-goods :decision :blocked
   :note "physical manufacture, stocking and shipping are licensed human work"}
  {:capability :handle-patient-data :decision :blocked
   :note "no patient-identifiable data"}
  {:capability :contact-patients-or-providers :decision :blocked
   :note "no outbound contact with patients or healthcare providers"}
  {:capability :purchase-or-payment :decision :blocked
   :note "no buying, selling, transfer or payment"}]}
"""

EVIDENCE = '''#!/usr/bin/env python3
"""__NAME__ evidence: read-only measurement of local catalogue state.

No network calls (cron runs unattended and terminal HTTP is denied).
Measurement of record for __NAME__. The agent must not re-measure.
On any failure print a REFUSED banner and UNMEASURED lines and exit 0:
a measurement we could not take must never look like a clean measurement.
"""
import json
import os
import time

NAME = "__NAME__"
PROFILE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WS = os.path.join(PROFILE, "workspace")
CATALOG = os.path.join(WS, "catalogs", "__CATALOG__")
SOURCES = os.path.join(WS, "sources.edn")
LEDGER = os.path.join(WS, "ledger.jsonl")


def count_tokens(path, token):
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return sum(1 for line in fh
                       if token in line and not line.lstrip().startswith(";"))
    except OSError:
        return None


def age_hours(path):
    try:
        return round((time.time() - os.path.getmtime(path)) / 3600.0, 2)
    except OSError:
        return None


def main():
    problems = []
    for path in (CATALOG, SOURCES):
        if not os.path.isfile(path):
            problems.append("missing:" + os.path.basename(path))
    if problems:
        print("REFUSED: cannot measure (" + ", ".join(problems) + ")")
        for key in ("catalog_entries", "sources", "ledger_rows", "newest_catalog_age_hours"):
            print("UNMEASURED\\t%s.%s\\t%s" % (NAME, key, ";".join(problems)))
        return 0

    entries = count_tokens(CATALOG, ":entry/id")
    sources = count_tokens(SOURCES, ":source/id")
    rows = count_tokens(LEDGER, '"ts"')
    age = age_hours(CATALOG)
    m = {
        "catalog_entries": entries,
        "sources": sources,
        "ledger_rows": rows if rows is not None else 0,
        "newest_catalog_age_hours": age,
    }
    for key in ("catalog_entries", "sources", "ledger_rows", "newest_catalog_age_hours"):
        value = m[key]
        print("MEASURE\\t%s.%s\\t%s" % (NAME, key, value if value is not None else "UNMEASURED"))
    print("STATUS\\tok")
    try:
        with open(LEDGER, "a", encoding="utf-8") as fh:
            fh.write(json.dumps({"ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                                 "bot": NAME, "m": m}, sort_keys=True) + "\\n")
    except OSError as exc:
        print("UNMEASURED\\t%s.ledger_append\\t%s" % (NAME, exc))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
'''

PROMPT = """SOUL.md を読め。scripts/__SCRIPT__ を terminal で 1 回実行し MEASURE 行を読む。
workspace/ledger.jsonl の前回行との差から 1 finding を決め、公開一次資料を 1 件だけ読み
quote + URL + retrieved 日付を sources.edn に記録してカタログに 1 エントリを追加するか
workspace/proposals/ に提案を 1 件書く。25 API call 以内で短く報告して終了。
処方・診断・調剤・購入・患者データは禁止（yakuwari.edn の :blocked を守る）。"""


def fill(template, **kw):
    out = template
    for key, value in kw.items():
        out = out.replace("__%s__" % key, value)
    return out


def write(path, content, mode=None):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(content)
    if mode is not None:
        os.chmod(path, mode)


def main():
    donor_config = open(os.path.join(DONOR, "config.yaml"), encoding="utf-8").read()
    donor_env = open(os.path.join(DONOR, ".env"), encoding="utf-8").read()
    made = []
    for name, spec in PROFILES.items():
        script = name.replace("-", "_") + "_evidence.py"
        kw = dict(
            NAME=name,
            DOMAIN_JA=spec["domain_ja"],
            CATALOG=spec["catalog"],
            CATALOG_DOC=spec["catalog_doc"],
            SCRIPT=script,
            OBJECTIVE=spec["objective"],
            EXTRA_SOUL=spec["extra_soul"] if spec["extra_soul"] else "\n",
        )
        host_ws = os.path.join(HOST, name, "workspace")
        config = donor_config.replace(
            "cwd: /Users/junkawasaki/github/wt/fleet/bot-sec-toolkit-maturity",
            "cwd: " + host_ws)
        files = {
            "profile.yaml": "description: '%s'\ndescription_auto: false\n" % spec["desc"],
            "config.yaml": config,
            "SOUL.md": fill(SOUL, **kw),
            "yakuwari.edn": fill(YAKUWARI, **kw),
            "scripts/" + script: fill(EVIDENCE, **kw),
            "workspace/sources.edn": fill(SOURCES, **kw),
            "workspace/catalogs/" + spec["catalog"]: fill(CATALOG, **kw),
            "workspace/ledger.jsonl": json.dumps(
                {"ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                 "bot": name, "m": "bootstrap", "note": "ledger created; append only"}, sort_keys=True) + "\n",
            "workspace/proposals/README.md": "one proposal per file; cite quotes and URLs\n",
            "cron/prompts/tick.txt": fill(PROMPT, **kw),
        }
        for root in (os.path.join(REPO, "hermes", "profiles", name), os.path.join(HOST, name)):
            for rel, content in files.items():
                write(os.path.join(root, rel), content, 0o755 if rel.startswith("scripts/") else None)
            if root.startswith(HOST):
                write(os.path.join(root, ".env"), donor_env, 0o600)
        made.append(name)
    write(os.path.join(REPO, "scripts", "gen-profiles.py"),
          open(__file__, encoding="utf-8").read())
    print("generated:", " ".join(made))


if __name__ == "__main__":
    main()
