# Stage P3 live smoke: the offline Guardian evaluation is real and served.
# Run:  powershell -ExecutionPolicy Bypass -File scripts\smoke_eval.ps1
$ErrorActionPreference = "Stop"
$base = "http://localhost:8081"
$failed = @()

function Check($name, $cond, $detail = "") {
    if ($cond) { Write-Host "  PASS  $name" }
    else { Write-Host "  FAIL  $name  $detail"; $script:failed += $name }
}

# 1. Ensure a run exists (writes eval/last_run.json).
Write-Host "Running the eval over the gold set (test split)..."
Push-Location S:\AI_cup_prj
server\.venv\Scripts\python scripts\run_eval.py --split test | Out-Null
Pop-Location

# 2. Health + login
$health = Invoke-RestMethod "$base/healthz"
Check "backend healthy" ($health.ok -eq $true)
$login = Invoke-RestMethod -Method Post -Uri "$base/api/dev/demo-login" `
    -ContentType "application/json" -Body '{"label":"smoke-eval"}'
$h = @{ Authorization = "Bearer $($login.token)" }
Check "demo login" ([bool]$login.token)

# 3. The eval endpoint serves the run with its sample size + review status.
$ev = Invoke-RestMethod "$base/api/dev/metrics/eval" -Headers $h
Check "eval run present" ([bool]$ev.run.run_id)
Check "eval n is 40 (test split)" ($ev.run.n -eq 40) "n=$($ev.run.n)"
Check "eval split is test" ($ev.run.split -eq "test")
Check "eval has precision/recall/f1" ($null -ne $ev.run.precision -and $null -ne $ev.run.recall -and $null -ne $ev.run.f1)
Check "eval has confusion matrix" ($null -ne $ev.run.confusion)
Check "eval tracks hard-negative FPR" ($null -ne $ev.run.hard_negative_fpr)
Check "eval labels are unreviewed (honest)" ($ev.run.review_status -eq "unreviewed")
Check "hard-negative FPR is 0.0 (clean advice never blocked)" ([math]::Abs($ev.run.hard_negative_fpr - 0.0) -lt 0.001) "fpr=$($ev.run.hard_negative_fpr)"
Write-Host "  precision=$($ev.run.precision) recall=$($ev.run.recall) f1=$($ev.run.f1) hardnegFPR=$($ev.run.hard_negative_fpr)"

# 4. Tuning closed the recall gap without adding false positives.
Check "recall improved to >= 0.9" ($ev.run.recall -ge 0.9) "recall=$($ev.run.recall)"
Check "precision stays 1.0" ([math]::Abs($ev.run.precision - 1.0) -lt 0.001) "precision=$($ev.run.precision)"

Write-Host ""
if ($failed.Count -eq 0) {
    Write-Host "SMOKE EVAL PASSED - all checks green"
} else {
    Write-Host "SMOKE EVAL FAILED - $($failed.Count) failing: $($failed -join ', ')"
    exit 1
}
