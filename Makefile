.DEFAULT_GOAL := help

# This repository is a book: Markdown chapters and SVG figures. There is nothing
# to compile, so the lifecycle targets below do the honest equivalent for a
# documentation repo and say so when they are no-ops. The one exception is the
# optional PDF edition (make pdf), whose Node and Python tools are pinned in
# package.json / package-lock.json and requirements-pdf.txt.

.PHONY: help install update uninstall build test lint dev clean pdf \
	check-book check-book-no-mermaid check-doc-standards check-manifest-declares

help: ## Show this help
	@awk 'match($$0, /^[a-zA-Z_\\:-]+:/) && /## / { \
	  name = substr($$0, 1, RLENGTH - 1); gsub(/\\/, "", name); \
	  desc = $$0; sub(/^.*## /, "", desc); \
	  printf "  \033[36m%-36s\033[0m %s\n", name, desc }' $(MAKEFILE_LIST)

install: ## Check the tools the checks need (python3, jq, git); installs nothing
	@missing=0; \
	for tool in python3 jq git; do \
	  if command -v $$tool >/dev/null 2>&1; then \
	    echo "  ok       $$tool ($$(command -v $$tool))"; \
	  else \
	    echo "  MISSING  $$tool (required)"; missing=1; \
	  fi; \
	done; \
	if command -v mmdc >/dev/null 2>&1; then \
	  echo "  ok       mmdc ($$(command -v mmdc)) - make check-book renders Mermaid diagrams"; \
	else \
	  echo "  absent   mmdc (optional) - Mermaid diagrams are skipped by make check-book"; \
	  echo "           to get it: npm install -g @mermaid-js/mermaid-cli"; \
	fi; \
	if [ $$missing -ne 0 ]; then \
	  echo "Install the missing tools above, then re-run make install."; exit 1; \
	fi; \
	echo "Nothing to install: the book is plain Markdown and SVG."

update: ## Fast-forward this checkout to the latest published edition
	git pull --ff-only

uninstall: clean ## Remove generated scratch output (nothing else is ever installed)
	@echo "Nothing else to uninstall: make install only checks tools."

build: ## No-op: the book is read as Markdown, there is nothing to compile
	@echo "Nothing to build: the book is plain Markdown and SVG, read as-is."

test: check-book ## Check the book (length, fences, links, images, Mermaid)

lint: check-doc-standards check-action-pinning ## Check doc standards and workflow action pinning

dev: ## Print how to preview the book
	@echo "The book is plain Markdown: there is no dev server."
	@echo "  Start at      book/README.md (table of contents)"
	@echo "  On GitHub     open book/README.md in the repository; Mermaid and SVG render inline"
	@echo "  In an editor  open book/ and use the Markdown preview (VS Code: Cmd+Shift+V)"
	@echo "  Before a PR   make test && make lint"

clean: ## Remove scratch render output, the built PDF and interpreter caches
	rm -rf tmp dist
	find . \( -path ./.git -o -path ./book -o -path ./assets -o -path ./node_modules \) -prune \
	  -o -type f \( -name '*.mmd.svg' -o -name '*.pyc' \) -exec rm -f {} +
	find . \( -path ./.git -o -path ./book -o -path ./assets -o -path ./node_modules \) -prune \
	  -o -type d -name __pycache__ -exec rm -rf {} +

# --- PDF edition --------------------------------------------------------------

PDF := dist/AI-Native Development.pdf

# npm ci runs only when node_modules is missing; it downloads a headless Chrome
# for puppeteer on first use. pypdf comes from requirements-pdf.txt.
pdf: ## Build the whole book as one PDF: dist/AI-Native Development.pdf
	@command -v node >/dev/null 2>&1 || { echo "node is required (Node.js 22.12 or later)"; exit 1; }
	@test -d node_modules/pagedjs || npm ci
	@python3 -c 'import pypdf' 2>/dev/null || { \
	  echo "pypdf is missing: python3 -m pip install -r requirements-pdf.txt"; exit 1; }
	node scripts/pdf/build.mjs
	python3 scripts/pdf/metadata.py --check "$(PDF)"

# --- Book and documentation checks --------------------------------------------

check-book: ## Check every chapter; renders Mermaid when mmdc is on PATH
	python3 scripts/check-book.py

# The CI form: the Mermaid CLI is not installed on the runner.
check-book-no-mermaid: ## Check every chapter without rendering Mermaid (CI)
	python3 scripts/check-book.py --no-mermaid

check-doc-standards: ## Check the footer and Mermaid theme on human-facing docs
	bash scripts/check-doc-standards.sh .

# Called with arguments by the capability registry's validation commands; this
# target is the make-side entry point for running one by hand.
check-manifest-declares: ## Assert a manifest declares keys: MANIFEST=<file> KEYS="<key> ..."
	@if [ -z "$(MANIFEST)" ] || [ -z "$(KEYS)" ]; then \
	  echo 'usage: make check-manifest-declares MANIFEST=<manifest.json> KEYS="<key> [<key>...]"'; exit 2; \
	fi
	bash scripts/check-manifest-declares.sh $(MANIFEST) $(KEYS)

# --- Multi-agent + platform-target validation ----------------------------------
# Rendered from the contract's makefile-agent-targets.mk.tmpl.
# Agents run these targets — users should not run bash scripts directly.

.PHONY: check-agent-drift check-feature-equivalence check-platform-targets \
	check-action-pinning check-capability-registry platform-targets-sync platform-targets-sync-capabilities \
	platform-targets-assert platform-targets-cochange \
	agent\:check agent-polish-gate

check-agent-drift: ## Check the thin agent adapters point at AGENTS.md
	bash scripts/check-agent-drift.sh .

check-feature-equivalence: ## Check cross-platform parity against the capability registry
	bash scripts/check-feature-equivalence.sh .

check-platform-targets: ## Check platform versions and README badges
	bash scripts/check-platform-targets.sh .

# A movable action ref (`@v7`, `@main`) is a third party's write access to this
# repo's CI. Shipped here, not left for each scaffolded repo to reinvent, after
# the same detector bugs (unrecursed file walk, YAML read as prose) were
# independently found and fixed in six separate personal repos.
check-action-pinning: ## Fail on a mutable uses:/container: ref in any workflow
	bash scripts/check-action-pinning.sh .

# Optional: present once the repo ships a capability registry checker. Degrades rather
# than failing so a repo can adopt core/capabilities/platforms.json before the checker.
check-capability-registry: ## Check the capability registry (skipped when the checker is absent)
	@if [ -f scripts/check-capability-registry.sh ]; then \
	  bash scripts/check-capability-registry.sh .; \
	else \
	  echo "  scripts/check-capability-registry.sh absent — registry agreement still enforced by check-feature-equivalence"; \
	fi

platform-targets-sync: ## Refresh platform-targets.json
	bash scripts/check-platform-targets.sh . --sync

# Regenerate the derived capability mirror in platform-targets.json from
# core/capabilities/platforms.json. Never hand-edit those two fields.
platform-targets-sync-capabilities: ## Regenerate the derived capability mirror
	bash scripts/check-platform-targets.sh . --sync-capabilities

platform-targets-assert: ## Assert platform targets are current
	bash scripts/check-platform-targets.sh . --assert-current

platform-targets-cochange: ## Require platform targets and badges to change together
	bash scripts/check-platform-targets.sh . --require-co-change

# The template's four checks plus the book check in its CI form (--no-mermaid),
# so this passes on a runner where mmdc is absent.
agent\:check: check-agent-drift check-feature-equivalence check-platform-targets check-action-pinning check-book-no-mermaid ## The gate: agent checks plus the book check (no Mermaid render)

# Polish exit gate — agent runs after updating platform-targets.json + README badges
agent-polish-gate: platform-targets-sync platform-targets-assert agent\:check check-doc-standards ## Polish exit gate: sync and assert platform targets, then every check
