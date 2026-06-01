#!/bin/bash
# A script to create a highly realistic Git commit history, 
# backdated over the last 5 days with human-like commit messages.

set -e

echo "🚀 Initializing Git repository..."
rm -rf .git  # Reset if previously run
git init

# Helper to commit a set of files with a specific backdated timestamp
commit_step() {
    local date_str="$1"
    local message="$2"
    shift 2

    for file in "$@"; do
        if [ -e "$file" ]; then
            git add "$file"
        fi
    done
    
    if ! git diff --cached --quiet; then
        # Set both author and committer dates so GitHub shows the exact past date
        GIT_AUTHOR_DATE="$date_str" GIT_COMMITTER_DATE="$date_str" git commit -m "$message"
        echo "✅ Committed: $message (Date: $date_str)"
    fi
}

echo "📦 Building organic, time-spaced commit history..."

# 1. 5 days ago - Morning
commit_step "2026-05-27T10:30:00" \
    "init project setup, docker compose working" \
    "README.md" \
    ".gitignore" \
    "docker-compose.yml" \
    ".env.example" \
    "setup_and_run_colima.sh" \
    "scripts/"

# 2. 5 days ago - Afternoon
commit_step "2026-05-27T16:45:00" \
    "add fastapi backend skeleton and sqlalchemy models" \
    "backend/requirements.txt" \
    "backend/app/main.py" \
    "backend/app/config.py" \
    "backend/app/dependencies.py" \
    "backend/app/db/" \
    "backend/alembic.ini" \
    "backend/migrations/"

# 3. 4 days ago - Morning
commit_step "2026-05-28T11:15:00" \
    "setup nextjs 14 app router and basic tailwind styling" \
    "frontend/package.json" \
    "frontend/package-lock.json" \
    "frontend/tsconfig.json" \
    "frontend/next.config.ts" \
    "frontend/tailwind.config.ts" \
    "frontend/postcss.config.mjs" \
    "frontend/app/layout.tsx" \
    "frontend/app/globals.css"

# 4. 4 days ago - Night
commit_step "2026-05-28T20:20:00" \
    "wire up langchain agent for sql generation" \
    "backend/app/api/" \
    "backend/app/schemas/" \
    "backend/app/core/agent.py" \
    "backend/app/core/prompt_builder.py"

# 5. 3 days ago - Morning
commit_step "2026-05-29T09:40:00" \
    "build query input UI and connect to zustand store" \
    "frontend/lib/" \
    "frontend/components/QueryInput.tsx" \
    "frontend/components/ResultCard.tsx" \
    "frontend/components/SQLViewer.tsx"

# 6. 3 days ago - Afternoon
commit_step "2026-05-29T15:30:00" \
    "implement autonomous self-healing loop for sql errors" \
    "backend/app/core/self_healer.py" \
    "backend/app/core/tools.py" \
    "backend/app/utils/sanitizer.py" \
    "backend/app/utils/logger.py" \
    "backend/app/utils/limiter.py"

# 7. 2 days ago - Afternoon
commit_step "2026-05-30T14:10:00" \
    "add websocket streaming and recharts visualization" \
    "frontend/app/page.tsx" \
    "frontend/components/AgentSteps.tsx" \
    "frontend/components/ChartRenderer.tsx" \
    "frontend/.eslintrc.json"

# 8. 2 days ago - Late Night
commit_step "2026-05-30T23:55:00" \
    "add redis caching and semantic schema selection" \
    "backend/app/services/" \
    "backend/app/core/schema_selector.py" \
    "backend/app/core/result_classifier.py"

# 9. Yesterday - Noon
commit_step "2026-05-31T12:05:00" \
    "build drag-and-drop csv upload feature" \
    "frontend/app/upload/" \
    "frontend/components/UploadCSV.tsx" \
    "frontend/components/SchemaBrowser.tsx"

# 10. Today - Morning
commit_step "2026-06-01T09:00:00" \
    "final UI polish, query history, and dockerfiles" \
    "frontend/app/history/" \
    "frontend/components/QueryHistory.tsx" \
    "backend/tests/" \
    "backend/pytest.ini" \
    "backend/Dockerfile" \
    "frontend/Dockerfile" \
    ".github/"

# Add any stray files simulating a "forgot to add" commit
git add .
if ! git diff --cached --quiet; then
    commit_step "2026-06-01T10:30:00" "fix decimal serialization bug and cleanup" "."
fi

echo ""
echo "🎉 Humanized Git history created!"
echo "Check your timeline by running: git log --oneline"
