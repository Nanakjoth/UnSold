# Stage A3 live smoke: full run need -> session -> end -> summary -> reveal ->
# feedback -> agreement number on metrics.
# Run:  powershell -ExecutionPolicy Bypass -File scripts\smoke_a3.ps1
$ErrorActionPreference = "Stop"
$base = "http://localhost:8081"
$failed = @()

function Check($name, $cond, $detail = "") {
    if ($cond) { Write-Host "  PASS  $name" }
    else { Write-Host "  FAIL  $name  $detail"; $script:failed += $name }
}

# 1. Health
$health = Invoke-RestMethod "$base/healthz"
Check "backend healthy" ($health.ok -eq $true) ($health | ConvertTo-Json -Compress)

# 2. Login
$login = Invoke-RestMethod -Method Post -Uri "$base/api/dev/demo-login" `
    -ContentType "application/json" -Body '{"label":"smoke-a3"}'
$h = @{ Authorization = "Bearer $($login.token)" }
Check "demo login" ([bool]$login.token)
Write-Host "  pseudonym: $($login.pseudonym)"

# 3. Need
$need = Invoke-RestMethod -Method Post -Uri "$base/api/needs" -Headers $h `
    -ContentType "application/json" `
    -Body '{"text":"I want honest advice about switching careers into design and whether to take a course.","money_involved":true}'
Check "need created" ([bool]$need.need_id)
Check "interpretation labelled" ($need.interpretation.interaction_source -or $need.interpretation.interpretation_source) ($need.interpretation | ConvertTo-Json -Compress)

# 4. Session
$mentorId = (Invoke-RestMethod "$base/api/mentors" -Headers $h).items[0].id
$session = Invoke-RestMethod -Method Post -Uri "$base/api/sessions" -Headers $h `
    -ContentType "application/json" `
    -Body (@{ mentor_id = $mentorId; need_id = $need.need_id } | ConvertTo-Json)
Check "session created" ($session.status -eq "ACTIVE")
$sid = $session.id

# 5. Chat: one clean message + a salesy mentor reply (strike + severity)
$null = Invoke-RestMethod -Method Post -Uri "$base/api/sessions/$sid/messages" -Headers $h `
    -ContentType "application/json" -Body '{"text":"I have three years of experience and want to move into UX design."}'
$sent = Invoke-RestMethod -Method Post -Uri "$base/api/sessions/$sid/mentor-reply?style=salesy" -Headers $h
Check "salesy reply screened" ($sent.guardian.action -ne $null) $sent.guardian.action
Write-Host "  guardian action on salesy: $($sent.guardian.action)"

# 6. Reveal: NONE -> REVEALED with a contact (scrubbed)
$rev = Invoke-RestMethod -Method Post -Uri "$base/api/sessions/$sid/reveal" -Headers $h `
    -ContentType "application/json" `
    -Body '{"consent":true,"contact_optional":"call me at +1 555 123 4567"}'
Check "reveal REVEALED" ($rev.state -eq "REVEALED" -and $rev.revealed) $rev.state
Check "two contacts exposed" ($rev.contacts.Count -eq 2)
$menteeContact = ($rev.contacts | Where-Object { $_.role -eq "mentee" }).contact_optional
Check "contact scrubbed (no raw phone)" ($menteeContact -notmatch "555 123 4567") $menteeContact
Check "mentor contact labelled simulated" (($rev.contacts | Where-Object { $_.role -eq "mentor" }).is_simulated -eq $true)

# 6b. Once REVEALED, withdrawal must be refused
$withdrawCode = try {
    Invoke-RestMethod -Method Post -Uri "$base/api/sessions/$sid/reveal" -Headers $h `
        -ContentType "application/json" -Body '{"consent":false}' | Out-Null
    200
} catch { ($_.Exception.Response.StatusCode.value__) }
Check "reveal locked after REVEALED" ($withdrawCode -eq 400) "got $withdrawCode"

# 7. End session
$ended = Invoke-RestMethod -Method Post -Uri "$base/api/sessions/$sid/end" -Headers $h
Check "session ended" ($ended.status -eq "ENDED")

# 8. Summary: generated, <=5 action items, catalogue things-to-try
$summary = Invoke-RestMethod "$base/api/sessions/$sid/summary" -Headers $h
Check "summary generated" ($summary.source -in @("gemini","fallback")) $summary.source
Check "action items capped at 5" ($summary.action_items.Count -le 5) "$($summary.action_items.Count)"
Check "caveats present" ($summary.caveats.Count -gt 0)
Write-Host "  source: $($summary.source), key points: $($summary.key_points.Count), things to try: $($summary.things_to_try.Count)"

# 9. Summary editability (survives regeneration)
$edited = Invoke-RestMethod -Method Patch -Uri "$base/api/sessions/$sid/summary" -Headers $h `
    -ContentType "application/json" `
    -Body '{"action_items":["Do one informational interview this week."]}'
Check "summary edited" ($edited.edited -eq $true)
$again = Invoke-RestMethod "$base/api/sessions/$sid/summary" -Headers $h
Check "edit survives regeneration" ($again.action_items[0] -eq "Do one informational interview this week.") ($again.action_items -join " | ")

# 10. Feedback: mentee with felt_pitched, agreement returned
$fb = Invoke-RestMethod -Method Post -Uri "$base/api/sessions/$sid/feedback" -Headers $h `
    -ContentType "application/json" `
    -Body '{"role":"mentee","mentee":{"helpfulness_1_5":5,"felt_pitched":"no","would_recommend":true,"free_text":"Great help."}}'
Check "feedback accepted" ($fb.ok -eq $true)
Check "agreement returned with sample size" ($fb.agreement -ne $null -and $fb.agreement.sample_size -ge 0)
Write-Host "  agreement so far: share=$($fb.agreement.share) samples=$($fb.agreement.sample_size) ($($fb.agreement.label))"

# 11. Mentor (simulated) feedback
$fb2 = Invoke-RestMethod -Method Post -Uri "$base/api/sessions/$sid/feedback" -Headers $h `
    -ContentType "application/json" `
    -Body '{"role":"mentor","mentor":{"mentee_seriousness_1_5":4,"respectful":true}}'
Check "mentor feedback accepted" ($fb2.ok -eq $true)

# 12. Metrics endpoint: agreement with sample size, hidden below 3
$metrics = Invoke-RestMethod "$base/api/dev/metrics/guardian" -Headers $h
Check "metrics agreement present" ($metrics.agreement.sample_size -ge 0)
Check "metrics labelled simulated" ($metrics.agreement.is_simulated -eq $true)
Check "share hidden below 3 samples" ($metrics.agreement.sample_size -ge 3 -or $metrics.agreement.share -eq $null)
Write-Host "  metrics: share=$($metrics.agreement.share) samples=$($metrics.agreement.sample_size)"

# 13. Mentor impact dashboard
$impact = Invoke-RestMethod "$base/api/dev/mentors/$mentorId/impact" -Headers $h
Check "impact dashboard" ($impact.sessions_completed -ge 1) "sessions=$($impact.sessions_completed)"
Check "impact labelled simulated" ($impact.is_simulated -eq $true)
Write-Host "  impact: sessions=$($impact.sessions_completed) quality=$($impact.quality_score) helpfulness=$($impact.avg_helpfulness) responses=$($impact.helpfulness_responses)"

# 14. Honesty: public mentor card never exposes stats
$card = (Invoke-RestMethod "$base/api/mentors" -Headers $h).items[0]
Check "public card hides stats" (-not ($card.PSObject.Properties.Name -contains "stats"))

Write-Host ""
if ($failed.Count -eq 0) {
    Write-Host "SMOKE A3 PASSED - all checks green"
} else {
    Write-Host "SMOKE A3 FAILED - $($failed.Count) failing: $($failed -join ', ')"
    exit 1
}
