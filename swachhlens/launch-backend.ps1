$ErrorActionPreference = 'Stop'
$log = 'C:\Users\prash\Music\swachh_lens-main (1)\tech\.freebuff\backend.log'
$logErr = 'C:\Users\prash\Music\swachh_lens-main (1)\tech\.freebuff\backend.log.err'
$workDir = 'C:\Users\prash\Music\swachh_lens-main (1)\tech\backend'
$proc = Start-Process -FilePath 'py' -ArgumentList '-m','uvicorn','app.main:app','--host','127.0.0.1','--port','8000' -WorkingDirectory $workDir -RedirectStandardOutput $log -RedirectStandardError $logErr -WindowStyle Hidden -PassThru
Write-Output $proc.Id
