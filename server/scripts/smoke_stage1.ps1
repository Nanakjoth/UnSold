# Stage 1 live end-to-end smoke test against a running Atlas server.
$ErrorActionPreference = "Stop"
$Base = "http://127.0.0.1:8081"
$pass = 0
$fail = 0

function Check($name, $cond, $detail = "") {
    if ($cond) { $script:pass++; Write-Output "  PASS  $name" }
    else { $script:fail++; Write-Output "  FAIL  $name $detail" }
}

# 1. Config is public and honest about AI availability
$cfg = Invoke-RestMethod "$Base/api/config"
Check "config public" ($cfg.app_mode -eq "demo" -and $cfg.ai_available -eq $false) ($cfg | ConvertTo-Json -Compress)

# 2. Browse without any account
$browse = Invoke-RestMethod "$Base/api/interests?limit=5"
Check "browse total >= 80" ($browse.total -ge 80) "total=$($browse.total)"
Check "search_source=keyword" ($browse.search_source -eq "keyword")
Check "ai_search_available=false" ($browse.ai_search_available -eq $false)
Check "page size honored" ($browse.items.Count -eq 5)

# 3. Keyword search finds real content
$paper = Invoke-RestMethod "$Base/api/interests?q=paper&limit=50"
Check "search 'paper' > 0 hits" ($paper.total -gt 0) "total=$($paper.total)"
Check "bookbinding in paper results" (@($paper.items | Where-Object { $_.slug -eq "bookbinding" }).Count -eq 1)

# 4. Zero-hit query returns empty, not fabrications
$none = Invoke-RestMethod "$Base/api/interests?q=zzzqqqnotathing"
Check "zero-hit query returns 0" ($none.total -eq 0 -and $none.items.Count -eq 0)

# 5. Filters
$cat = Invoke-RestMethod "$Base/api/interests?category=Food%20%26%20Culture&limit=50"
Check "category filter works" ($cat.total -ge 5 -and (@($cat.items | Where-Object { $_.category -ne "Food & Culture" }).Count -eq 0))
$beg = Invoke-RestMethod "$Base/api/interests?beginner=true&limit=50"
Check "beginner filter works" ($beg.total -gt 0 -and (@($beg.items | Where-Object { $_.difficulty -ne "beginner" }).Count -eq 0))

# 6. Categories facets
$cats = Invoke-RestMethod "$Base/api/interests/categories"
Check "10 category facets" ($cats.items.Count -eq 10) "count=$($cats.items.Count)"
Check "facet sum >= 80" ((($cats.items | Measure-Object -Property count -Sum).Sum) -ge 80)

# 7. Detail page with expanded relationships
$detail = Invoke-RestMethod "$Base/api/interests/bookbinding"
Check "detail loads" ($detail.slug -eq "bookbinding")
Check "detail has long text" ($detail.long_description.Length -gt 50)
Check "detail has related edges" ($detail.related.Count -ge 2) "related=$($detail.related.Count)"
Check "related entries are cards" ($detail.related[0].interest.title.Length -gt 0 -and $detail.related[0].type.Length -gt 0)
Check "sample content flagged" ($detail.is_sample_content -eq $true)

try { Invoke-RestMethod "$Base/api/interests/not-a-real-thing" | Out-Null; Check "unknown slug 404" $false }
catch { Check "unknown slug 404" ($_.Exception.Response.StatusCode.value__ -eq 404) }

# 8. Save/feedback require auth
try { Invoke-RestMethod "$Base/api/library/saved" | Out-Null; Check "saved requires auth" $false }
catch { Check "saved requires auth" ($_.Exception.Response.StatusCode.value__ -eq 401) }

# 9. Demo login -> session
$login = Invoke-RestMethod -Method Post "$Base/api/dev/demo-login" -ContentType "application/json" -Body '{"label":"smoke-a"}'
$H = @{ Authorization = "Bearer $($login.token)" }
Check "demo login returns pseudonym" ($login.pseudonym -match "^[a-z]+-[a-z]+-\d+$") ($login.pseudonym)
$sess = Invoke-RestMethod -Method Post "$Base/api/auth/session" -Headers $H
Check "session uid matches login" ($sess.uid -eq $login.uid)

# 10. Save -> list -> unsave
$saved1 = Invoke-RestMethod -Method Post "$Base/api/library/saved/bookbinding" -Headers $H
Check "save adds card" (@($saved1.items | Where-Object { $_.slug -eq "bookbinding" }).Count -eq 1)
$saved2 = Invoke-RestMethod "$Base/api/library/saved" -Headers $H
Check "saved persists across calls" ($saved2.total -eq 1)
Invoke-RestMethod -Method Post "$Base/api/library/saved/bookbinding" -Headers $H | Out-Null
$saved3 = Invoke-RestMethod "$Base/api/library/saved" -Headers $H
Check "save is idempotent" ($saved3.total -eq 1) "total=$($saved3.total)"

# 11. Feedback with fixed reason
$fb = Invoke-RestMethod -Method Post "$Base/api/library/feedback" -Headers $H -ContentType "application/json" `
    -Body '{"interest_slug":"origami","action":"dismiss","reason":"not_relevant"}'
Check "feedback confirmed" ($fb.action -eq "dismiss" -and $fb.interest_slug -eq "origami")
Check "agreement withheld below 3 samples" ($null -eq $fb.agreement)

# 12. Dismissal does NOT hide the entry
$post = Invoke-RestMethod "$Base/api/interests?q=origami"
Check "dismissed entry still listed" (@($post.items | Where-Object { $_.slug -eq "origami" }).Count -eq 1)

# 13. Per-member isolation: second identity sees an empty list
$loginB = Invoke-RestMethod -Method Post "$Base/api/dev/demo-login" -ContentType "application/json" -Body '{"label":"smoke-b"}'
$HB = @{ Authorization = "Bearer $($loginB.token)" }
$savedB = Invoke-RestMethod "$Base/api/library/saved" -Headers $HB
Check "other member's list is empty" ($savedB.total -eq 0) "total=$($savedB.total)"
Check "distinct identities" ($loginB.uid -ne $login.uid)

# 14. Agreement summary appears once >= 3 samples exist
foreach ($label in @("smoke-c", "smoke-d", "smoke-e")) {
    $lx = Invoke-RestMethod -Method Post "$Base/api/dev/demo-login" -ContentType "application/json" -Body ('{"label":"' + $label + '"}')
    $hx = @{ Authorization = "Bearer $($lx.token)" }
    Invoke-RestMethod -Method Post "$Base/api/library/feedback" -Headers $hx -ContentType "application/json" `
        -Body '{"interest_slug":"bookbinding","action":"save"}' | Out-Null
}
$fb2 = Invoke-RestMethod -Method Post "$Base/api/library/feedback" -Headers $H -ContentType "application/json" `
    -Body '{"interest_slug":"bookbinding","action":"save"}'
Check "agreement appears at >=3 samples" ($null -ne $fb2.agreement) ($fb2 | ConvertTo-Json -Compress)
Check "agreement is labelled simulated" ($fb2.agreement.label -like "*Simulated*")

# 15. Deletion removes owned records and reports counts
$del = Invoke-RestMethod -Method Delete "$Base/api/auth/session" -Headers $H
Check "deletion reports saved_interests" ($del.deleted.saved_interests -ge 1) ($del | ConvertTo-Json -Compress)
Check "deletion reports discovery_feedback" ($del.deleted.discovery_feedback -ge 2) ($del | ConvertTo-Json -Compress)
$savedAfter = Invoke-RestMethod "$Base/api/library/saved" -Headers $H
Check "saved list empty after deletion" ($savedAfter.total -eq 0)

Write-Output ""
Write-Output "SMOKE RESULT: $pass passed, $fail failed"
if ($fail -gt 0) { exit 1 }
