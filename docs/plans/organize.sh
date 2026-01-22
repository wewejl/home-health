#!/bin/bash

# 已完成的计划
completed=(
  "2026-01-16-advice-diagnosis-display-fix.md"
  "2026-01-16-diagnosis-card-debug-plan.md"
  "2026-01-16-diagnosis-display-bugfix-implementation.md"
  "2026-01-16-diagnosis-display-bugfix.md"
  "2026-01-16-diagnosis-display-enhancement.md"
  "2026-01-16-diagnosis-display-implementation.md"
  "2026-01-16-intermediate-advice-tooling-design.md"
  "2026-01-16-intermediate-advice-tooling-implementation.md"
  "2026-01-17-multi-agent-architecture-refactor.md"
  "2026-01-18-conversation-pdf-export-implementation.md"
  "2026-01-18-medical-dossier-export-redesign.md"
  "2026-01-18-voice-call-agent-design.md"
  "2026-01-18-voice-call-implementation-plan.md"
  "2026-01-18-voice-mode-professional.md"
  "2026-01-19-sms-verification-engineering-upgrade.md"
  "2026-01-19-sms-verification-test-report.md"
  "2026-01-20-langgraph-agent-architecture-refactor.md"
  "2026-01-20-react-agent-design.md"
  "2026-01-20-streaming-response-design.md"
  "2026-01-21-code-review-report.md"
  "2026-01-21-doctor-avatar-system-improvement.md"
  "2026-01-21-persona-chat-ui-design.md"
)

cd "$(dirname "$0")"

for file in "${completed[@]}"; do
  if [ -f "$file" ]; then
    # 添加完成标记
    echo "# 状态: ✅ 已完成" | cat - "$file" > temp && mv temp "$file"
    # 移动到 completed
    mv "$file" completed/
    echo "✓ $file"
  fi
done

echo ""
echo "归档完成！"
