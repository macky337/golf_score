# 実行: .\cleanup.ps1
$patterns = @(
  '.venv',
  '__pycache__',
  '*.py[cod]',
  '*.log',
  '*.tmp',
  '.DS_Store',
  'Thumbs.db'
)
foreach ($pattern in $patterns) {
    Get-ChildItem -Path . -Include $pattern -Recurse -Force |
      Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
}
Write-Host "Cleanup completed."
