# PowerShell script to install git hooks for vibey-bootstrap
# Run this with: powershell -ExecutionPolicy Bypass -File .githooks\install-hooks.ps1

Write-Host "🔧 Installing git hooks..." -ForegroundColor Yellow

# Configure git to use .githooks directory
git config core.hooksPath .githooks

Write-Host "✅ Git hooks installed successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "The following hooks are now active:"
Write-Host "  - pre-commit: Runs quality checks before each commit"
Write-Host "  - pre-push: Runs comprehensive tests before push"
Write-Host ""
Write-Host "To skip hooks (not recommended):"
Write-Host "  git commit --no-verify"
Write-Host "  git push --no-verify"
