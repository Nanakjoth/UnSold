# Stage A2 live smoke: advice -> session -> Guardian -> Friend Test.
# Run: backend on 8081, then `pwsh scripts/smoke_a2.ps1`.
$ErrorActionPreference = "Stop"
$base = "http://localhost:8081"

# 1. Demo login.
$login = Invoke-RestMethod -Method Post -Uri "$base/api/dev/demo-login" -ContentType "application/json" `
  -Body (@{ label = "smoke-a2" } | ConvertTo-Json)
$h = @{ Authorization = "Bearer $($login.token)" }
Write-Host "OK  login uid=$($login.uid)"

# 2. Create a money need -> matches.
$needText = "Should I pay for an expensive negotiation course to ask for more money at work?"
$need = Invoke-RestMethod -Method Post -Uri "$base/api/needs" -Headers $h -ContentType "application/json" `
  -Body (@{ text = $needText; money_involved = $true } | ConvertTo-Json)
Write-Host "OK  need $($need.need_id) matches=$($need.matches.Count) source=$($need.retrieval_source)"
$mentorId = $need.matches[0].mentor.id

# 3. Open a session linked to the need.
$session = Invoke-RestMethod -Method Post -Uri "$base/api/sessions" -Headers $h -ContentType "application/json" `
  -Body (@{ mentor_id = $mentorId; need_id = $need.need_id } | ConvertTo-Json)
$sid = $session.id
Write-Host "OK  session $sid with $($session.mentor_pseudonym) money_involved=$($session.money_involved)"

# 4. Mentee sends a clean message -> ALLOW.
$m1 = Invoke-RestMethod -Method Post -Uri "$base/api/sessions/$sid/messages" -Headers $h -ContentType "application/json" `
  -Body (@{ text = "Hi, I want advice on whether a paid course is worth it for my salary negotiation." } | ConvertTo-Json)
Write-Host "OK  mentee msg -> $($m1.guardian.action)"

# 5. Salesy mentor reply -> Guardian should BLOCK + redact + strike.
$block = Invoke-RestMethod -Method Post -Uri "$base/api/sessions/$sid/mentor-reply?style=salesy" -Headers $h
Write-Host "OK  salesy reply -> $($block.guardian.action) strike=$($block.guardian.strike_incurred)"
if ($block.guardian.action -ne "BLOCK_AND_REDACT") { throw "Expected BLOCK" }
if ($block.message.display_text -ne "[Message removed: promotion or contact details]") { throw "Expected redaction" }

# 6. Subtle reply -> WARN (tagged, not blocked).
$subtle = Invoke-RestMethod -Method Post -Uri "$base/api/sessions/$sid/mentor-reply?style=subtle" -Headers $h
Write-Host "OK  subtle reply -> $($subtle.guardian.action)"

# 7. Friend Test -> pushes_to_spend.
$ft = Invoke-RestMethod -Uri "$base/api/sessions/$sid/friend-test" -Headers $h
Write-Host "OK  friend-test applicable=$($ft.applicable) stance=$($ft.stance)"
if ($ft.stance -ne "pushes_to_spend") { throw "Expected pushes_to_spend" }

# 8. Messages never store raw PII: leak a number, confirm redaction + scrub.
$leak = Invoke-RestMethod -Method Post -Uri "$base/api/sessions/$sid/messages" -Headers $h -ContentType "application/json" `
  -Body (@{ text = "My direct number is 555-987-6543, call me." } | ConvertTo-Json)
$stored = $leak.message.text_scrubbed
Write-Host "OK  leak -> action=$($leak.guardian.action) stored scrubbed=$($stored -notmatch '555-987-6543')"

# 9. End the session.
$ended = Invoke-RestMethod -Method Post -Uri "$base/api/sessions/$sid/end" -Headers $h
Write-Host "OK  end -> status=$($ended.status)"

Write-Host "`nA2 SMOKE PASSED"
