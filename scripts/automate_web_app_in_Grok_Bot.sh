## Place under ~/.bashrc or ~/.profile
## biblemate claude web app
start_biblemate_claude() {
  echo "Starting BibleMate Claude on port 33379 ..."
  # NiceGUI lives in the /workspace/ai venv, not on the system interpreter.
  PYTHONPATH="/workspace/ai/lib/python3.13/site-packages${PYTHONPATH:+:$PYTHONPATH}" \
    nohup /usr/bin/python3 /workspace/biblemate_studies/web_app_claude.py \
    >>/tmp/biblemate-claude-33379.log 2>&1 &
}
## Start when port 33379 is not listening
if ! ss -H -ltn 'sport = :33379' 2>/dev/null | grep -q .; then
  start_biblemate_claude
else
  echo "BibleMate Claude is already listening on port 33379."
fi