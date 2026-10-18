# Live demo of the A1 advice endpoints for manual checking.
$Base = "http://127.0.0.1:8081"

Write-Host "=== 1. Public mentor directory (no sign-in) ==="
$m = Invoke-WebRequest "$Base/api/mentors?domain=career&limit=3" -UseBasicParsing
$mt = $m.Content | ConvertFrom-Json
Write-Host "GET /api/mentors?domain=career -> $($m.StatusCode), total=$($mt.total)"
$mt.items | ForEach-Object { Write-Host ("  - {0} | {1} | langs={2}" -f $_.pseudonym, $_.public_card.role_band, ($_.public_card.languages -join ',')) }

Write-Host ""
Write-Host "=== 2. Sign in (demo identity) ==="
$login = Invoke-WebRequest "$Base/api/dev/demo-login" -Method POST -ContentType "application/json" `
    -Body '{"label":"you-checking"}' -UseBasicParsing
$tok = ($login.Content | ConvertFrom-Json).token
Write-Host "demo-login -> $($login.StatusCode)"

function Ask-Need($text, $money, $label) {
    $body = @{ text = $text; money_involved = $money } | ConvertTo-Json
    $r = Invoke-WebRequest "$Base/api/needs" -Method POST -ContentType "application/json" `
        -Headers @{Authorization = "Bearer $script:tok"} -Body $body -UseBasicParsing
    $p = $r.Content | ConvertFrom-Json
    Write-Host ""
    Write-Host "=== $label -> $($r.StatusCode) ==="
    Write-Host "  goal=$($p.interpretation.intent.goal_type)  domains=$($p.interpretation.intent.domains -join ',')  distress=$($p.interpretation.intent.distress_level)  money=$($p.interpretation.intent.money_involved)"
    Write-Host "  interpretation_source=$($p.interpretation.interpretation_source)  retrieval_source=$($p.retrieval_source)  no_strong_match=$($p.no_strong_match)"
    Write-Host "  summary: $($p.interpretation.summary)"
    foreach ($match in $p.matches) {
        Write-Host ("  MATCH {0} fit={1} {2} pseudonym={3}" -f $match.match_type, $match.fit_score, $match.mentor.public_card.role_band, $match.mentor.pseudonym)
        Write-Host ("        why: {0}" -f $match.explanation)
    }
}

Ask-Need "I am deciding whether to negotiate a job offer in fintech. I code backends and feel nervous about asking for more money." $true "Negotiation need (money involved)"
Ask-Need "I am burned out and exhausted from overwork. I dread Mondays and cannot sleep. I want to set boundaries with my manager." $false "Burnout need"
Ask-Need "Something entirely unrelated to any listed domain altogether." $false "Un-matchable need (should flag no_strong_match)"
