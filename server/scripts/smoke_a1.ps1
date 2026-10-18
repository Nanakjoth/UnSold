# Live smoke of the Stage A1 advice endpoints.
$Base = "http://127.0.0.1:8082"

# 1. Public mentors (no auth).
$m = Invoke-WebRequest "$Base/api/mentors?limit=3" -UseBasicParsing
$mt = ($m.Content | ConvertFrom-Json)
Write-Host "mentors: $($m.StatusCode) total=$($mt.total) source=$($mt.retrieval_source)"

# 2. Sign in.
$login = Invoke-WebRequest "$Base/api/dev/demo-login" -Method POST `
    -ContentType "application/json" -Body '{"label":"smoke-a1"}' -UseBasicParsing
$token = ($login.Content | ConvertFrom-Json).token
Write-Host "login: $($login.StatusCode)"

# 3. Needs: burnout case.
$body = @{
    text = "I am burned out from overwork and want to set boundaries with my manager about workload."
    money_involved = $false
} | ConvertTo-Json
$needs = Invoke-WebRequest "$Base/api/needs" -Method POST -ContentType "application/json" `
    -Headers @{Authorization = "Bearer $token"} -Body $body -UseBasicParsing
$p = $needs.Content | ConvertFrom-Json
Write-Host "needs: $($needs.StatusCode) goal=$($p.interpretation.intent.goal_type) distress=$($p.interpretation.intent.distress_level) matches=$($p.matches.Count) src=$($p.retrieval_source)"
$p.matches | ForEach-Object { Write-Host ("  {0} {1} {2}" -f $_.fit_score, $_.match_type, $_.mentor.pseudonym) }

# 4. Needs: unauth is 401.
try {
    Invoke-WebRequest "$Base/api/needs" -Method POST -ContentType "application/json" `
        -Body '{"text":"I need help deciding about a job offer and money negotiation."}' -UseBasicParsing | Out-Null
    Write-Host "unauth needs: unexpectedly OK (BUG)"
} catch {
    Write-Host "unauth needs: $([int]$_.Exception.Response.StatusCode) (expect 401)"
}
