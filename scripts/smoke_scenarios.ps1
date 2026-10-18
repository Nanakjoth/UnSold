# Live smoke: sample scenarios (spec §14) are served and actually surface the
# focus mentor they were built around, through the real /api/needs path.
# Run:  powershell -ExecutionPolicy Bypass -File scripts\smoke_scenarios.ps1
$ErrorActionPreference = "Stop"
$base = "http://localhost:8081"
$failed = @()

function Check($name, $cond, $detail = "") {
    if ($cond) { Write-Host "  PASS  $name" }
    else { Write-Host "  FAIL  $name  $detail"; $script:failed += $name }
}

# 1. Health
$health = Invoke-RestMethod "$base/healthz"
Check "backend healthy" ($health.ok -eq $true)

# 2. Scenarios endpoint is public (no auth) and serves 10.
$scenarios = Invoke-RestMethod "$base/api/needs/scenarios"
Check "10 sample scenarios served (public)" ($scenarios.Count -eq 10) "got $($scenarios.Count)"
Check "all flagged sample content" (@($scenarios | Where-Object { $_.is_sample_content -eq $true }).Count -eq 10)

# 3. Five distinct focus mentors are covered.
$mentors = @($scenarios | Select-Object -ExpandProperty intended_mentor_id -Unique)
Check "scenarios cover 5 distinct focus mentors" ($mentors.Count -eq 5) "got $($mentors.Count)"
Write-Host "  focus mentors: $($mentors -join ', ')"

# 4. Each focus mentor actually exists in the public directory.
$login = Invoke-RestMethod -Method Post -Uri "$base/api/dev/demo-login" -ContentType "application/json" -Body '{"label":"smoke-scn"}'
$h = @{ Authorization = "Bearer $($login.token)" }
$directory = (Invoke-RestMethod "$base/api/mentors?limit=100" -Headers $h).items | ForEach-Object { $_.id }
foreach ($mid in $mentors) {
    Check "mentor $mid is in the directory" ($directory -contains $mid)
}

# 5. Push a representative scenario through the real /api/needs path: its
#    intended mentor must be the top match. Use the meditation + startup ones.
$picked = $scenarios | Where-Object { $_.intended_mentor_id -eq "m-meditation-quiet-wren" } | Select-Object -First 1
$need = Invoke-RestMethod -Method Post -Uri "$base/api/needs" -Headers $h -ContentType "application/json" `
    -Body (@{ text = $picked.text; money_involved = $picked.money_involved } | ConvertTo-Json)
Check "meditation scenario matched its mentor #1" ($need.matches[0].mentor.id -eq "m-meditation-quiet-wren") "got $($need.matches[0].mentor.id)"

$picked2 = $scenarios | Where-Object { $_.intended_mentor_id -eq "m-founder-nontech-grounded-quail" } | Select-Object -First 1
$need2 = Invoke-RestMethod -Method Post -Uri "$base/api/needs" -Headers $h -ContentType "application/json" `
    -Body (@{ text = $picked2.text; money_involved = $picked2.money_involved } | ConvertTo-Json)
Check "non-tech business scenario matched its mentor #1" ($need2.matches[0].mentor.id -eq "m-founder-nontech-grounded-quail") "got $($need2.matches[0].mentor.id)"

Write-Host ""
if ($failed.Count -eq 0) {
    Write-Host "SMOKE SCENARIOS PASSED - all checks green"
} else {
    Write-Host "SMOKE SCENARIOS FAILED - $($failed.Count) failing: $($failed -join ', ')"
    exit 1
}
