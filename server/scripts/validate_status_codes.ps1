# Validates HTTP status codes for UI click actions (success + error paths).
$Base = "http://127.0.0.1:8081"
$pass = 0; $fail = 0; $results = @()

function Check($name, $expected, $actual) {
    if ($actual -eq $expected) { $script:pass++; $script:results += "  OK   [$actual] $name" }
    else { $script:fail++; $script:results += "  FAIL [got $actual, want $expected] $name" }
}

function Req($method, $path, $body = $null, $token = $null) {
    try {
        $h = @{ "Content-Type" = "application/json" }
        if ($token) { $h["Authorization"] = "Bearer $token" }
        if ($body) { $r = Invoke-WebRequest -Uri "$Base$path" -Method $method -Headers $h -Body ($body | ConvertTo-Json) -UseBasicParsing -TimeoutSec 10 }
        else { $r = Invoke-WebRequest -Uri "$Base$path" -Method $method -Headers $h -UseBasicParsing -TimeoutSec 10 }
        return $r.StatusCode
    } catch {
        $resp = $_.Exception.Response
        if ($resp) { return [int]$resp.StatusCode }
        return 0
    }
}

Write-Host "=== Click actions: success paths ==="
Check "Home/health" 200 (Req GET "/healthz")
Check "Explore list (browse)" 200 (Req GET "/api/interests?limit=5")
Check "Explore search box" 200 (Req GET "/api/interests?q=garden")
Check "Explore category filter" 200 (Req GET "/api/interests?category=creative_arts")
Check "Explore difficulty filter" 200 (Req GET "/api/interests?difficulty=beginner")
Check "Categories load" 200 (Req GET "/api/interests/categories")
Check "Interest detail click" 200 (Req GET "/api/interests/backyard-astronomy")
Check "Config badge" 200 (Req GET "/api/config")

# Demo sign-in: label-based, response field is `token`.
$label = "validator"
$loginBody = @{ label = $label }
$token = $null
try {
    $h = @{ "Content-Type" = "application/json" }
    $r = Invoke-WebRequest -Uri "$Base/api/dev/demo-login" -Method POST -Headers $h -Body ($loginBody | ConvertTo-Json) -UseBasicParsing -TimeoutSec 10
    $token = ($r.Content | ConvertFrom-Json).token
    Check "Sign in (demo login)" 200 $r.StatusCode
} catch {
    $resp = $_.Exception.Response
    $code = 0
    if ($resp) { $code = [int]$resp.StatusCode }
    Check "Sign in (demo login)" 200 $code
}

Check "Saved list (signed in)" 200 (Req GET "/api/library/saved" $null $token)
Check "Save interest click" 200 (Req POST "/api/library/saved/backyard-astronomy" $null $token)
Check "Save same again (idempotent)" 200 (Req POST "/api/library/saved/balcony-gardening" $null $token)
Check "Feedback: already_know" 200 (Req POST "/api/library/feedback" @{ interest_slug = "basketry"; action = "already_know"; reason = "not_relevant" } $token)
Check "Feedback: want_to_try" 200 (Req POST "/api/library/feedback" @{ interest_slug = "amateur-microscopy"; action = "want_to_try" } $token)
Check "Profile load (/dev/me)" 200 (Req GET "/api/dev/me" $null $token)
Check "Unsave click" 200 (Req DELETE "/api/library/saved/balcony-gardening" $null $token)

Write-Host "=== Click actions: expected error codes ==="
Check "Detail: unknown slug -> 404" 404 (Req GET "/api/interests/does-not-exist")
Check "Unauth saved -> 401" 401 (Req GET "/api/library/saved")
Check "Unauth save click -> 401" 401 (Req POST "/api/library/saved/backyard-astronomy")
Check "Unauth feedback -> 401" 401 (Req POST "/api/library/feedback" @{ interest_slug = "basketry"; action = "save" })
Check "Unauth profile -> 401" 401 (Req GET "/api/dev/me")
Check "Feedback: unknown slug -> 404" 404 (Req POST "/api/library/feedback" @{ interest_slug = "nope-nope"; action = "save" } $token)
Check "Bad feedback action -> 422" 422 (Req POST "/api/library/feedback" @{ interest_slug = "basketry"; action = "invalid_action" } $token)
Check "Bad login (empty label) -> 422" 422 (Req POST "/api/dev/demo-login" @{ label = "" })
Check "Oversized query -> 422" 422 (Req GET "/api/interests?q=$('x' * 400)")

Write-Host ""
Write-Host "=== Results ==="
$results | ForEach-Object { Write-Host $_ }
Write-Host ""
Write-Host "Passed: $pass  Failed: $fail"
if ($fail -gt 0) { exit 1 }
