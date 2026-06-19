# Operational

Commands, tool quirks, environment facts.

<!--
Example entry (copy, fill, uncomment):
---
type: operational
key: short-kebab-key
insight: one sentence, fact not opinion
confidence: 8
source: observed
files: []
ts: 2026-06-18
scope: harness
---
-->

---
type: operational
key: new-skill-needs-link-sh
insight: Навык, добавленный в agent-knowledge/skills/, невидим в Claude Code, пока не запущен link.sh — он симлинкает skills/* в ~/.claude/skills/. Запускать ./link.sh после каждого нового навыка.
confidence: 9
source: observed
files: ["link.sh", "README.md"]
ts: 2026-06-18
scope: harness
---

---
type: operational
key: link-sh-not-executable
insight: link.sh не имеет +x — `./link.sh` падает с "permission denied". Запускать `bash link.sh` (или `chmod +x link.sh` один раз). Уточняет запись new-skill-needs-link-sh.
confidence: 9
source: observed
files: ["link.sh"]
ts: 2026-06-19
scope: harness
---

---
type: operational
key: astra-meta-push-needs-vpn
insight: Astra meta-repo remote — приватный GitLab (gitlab.158-160-60-159.sslip.io); `git push` падает с SSL_ERROR_SYSCALL без VPN/доступа. agent-knowledge (GitHub) пушится штатно.
confidence: 9
source: observed
files: []
ts: 2026-06-19
scope: harness
---
