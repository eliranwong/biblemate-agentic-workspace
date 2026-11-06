# NiceGUI lives in ~/ai
WEB_PYTHON="$HOME/ai/bin/python3"

# ss cannot open a netlink socket here, so a refused connect is the port check.
port_is_open() {
  python3 -c 'import socket,sys
s=socket.socket(); s.settimeout(0.4)
r=s.connect_ex(("127.0.0.1", int(sys.argv[1]))); s.close()
sys.exit(0 if r==0 else 1)' "$1"
}

start_web_app() {
  local name="$1" port="$2" script="$3" logfile="$4"
  shift 4
  if port_is_open "$port"; then
    echo "$name is already listening on port $port."
    return 0
  fi
  if [ ! -x "$WEB_PYTHON" ] || [ ! -f "$script" ]; then
    echo "$name did not start: missing interpreter or $script" >&2
    return 1
  fi
  echo "Starting $name on port $port ..."
  nohup env "$@" "$WEB_PYTHON" "$script" >>"$logfile" 2>&1 &
}

## biblemate studies agy web app
start_biblemate_agy() {
  start_web_app "BibleMate Antigravity" 33381 \
    "$HOME/biblemate_studies/web_app_agy.py" /tmp/biblemate-agy-33381.log \
    BIBLEMATE_AGY_PORT=33381
}
start_biblemate_agy

## biblemate studies claude web app
start_biblemate_claude() {
  start_web_app "BibleMate Claude" 33382 \
    "$HOME/biblemate_studies/web_app_claude.py" /tmp/biblemate-claude-33382.log \
    BIBLEMATE_CLAUDE_PORT=33382
}
start_biblemate_claude

## biblemate studies codex web app
start_biblemate_codex() {
  start_web_app "BibleMate Codex" 33383 \
    "$HOME/biblemate_studies/web_app_codex.py" /tmp/biblemate-codex-33383.log \
    BIBLEMATE_CODEX_PORT=33383
}
start_biblemate_codex

## biblemate studies grok web app
start_biblemate_grok() {
  start_web_app "BibleMate Grok" 33384 \
    "$HOME/biblemate_studies/web_app_grok.py" /tmp/biblemate-grok-33384.log \
    BIBLEMATE_GROK_PORT=33384
}
start_biblemate_grok