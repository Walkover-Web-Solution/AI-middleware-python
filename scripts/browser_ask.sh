#!/bin/zsh
# Dev helper: send one message to a local gtwy agent with the Gtwy_Browser tool enabled
# and print the streamed events in a readable form.
#
#   export TOKEN='<authorization JWT>'
#   export THREAD='my-test-1'                # keep the same value for follow-up messages
#   ./scripts/browser_ask.sh "Open https://example.com and tell me the main heading."
#
# Optional: VERSION_ID (agent version), GTWY_URL (defaults to localhost:8080).

: ${GTWY_URL:=http://localhost:8080}
: ${VERSION_ID:=675be2047473749f8beac632}
: ${THREAD:=browser-dev-1}

if [[ -z "$TOKEN" ]]; then echo "set TOKEN first (authorization JWT)" >&2; exit 1; fi
if [[ -z "$1" ]]; then echo "usage: $0 \"<message>\"" >&2; exit 1; fi

curl -s -N -m 300 -X POST "$GTWY_URL/api/v2/model/chat/completion" \
  -H "authorization: $TOKEN" -H 'content-type: application/json' \
  -H 'origin: https://dev-ai.viasocket.com' \
  --data-raw "{\"version_id\":\"$VERSION_ID\",\"configuration\":{\"type\":\"chat\"},\"thread_id\":\"$THREAD\",\"user\":$(printf '%s' "$1" | python3 -c 'import json,sys; print(json.dumps(sys.stdin.read()))'),\"user_urls\":[],\"variables\":{\"name\":\"openai\"},\"built_in_tools\":[\"Gtwy_Browser\"],\"is_playground\":true,\"orchestrator_flag\":false,\"stream\":true}" \
| python3 -c "
import sys, json
text = ''
for line in sys.stdin:
    line = line.strip()
    if not line.startswith('data: '):
        continue
    try:
        ev = json.loads(line[6:])
    except Exception:
        continue
    event = ev.get('event')
    if event == 'delta':
        text += ev.get('content', '')
    elif event == 'tool_call':
        args = ev.get('args') or {}
        print('TOOL_CALL', {k: v for k, v in args.items() if v})
    elif event == 'tool_result':
        print('TOOL_RESULT', str(ev.get('content'))[:300].replace(chr(10), ' | '), '...')
    elif event == 'browser_handoff':
        print()
        print('>>> LOGIN NEEDED - open this and sign in:', ev.get('live_url'))
        print()
    elif event in ('error', 'fallback'):
        print(event.upper(), json.dumps(ev)[:300])
    elif event == 'done':
        print('DONE finish_reason=', ev.get('finish_reason'))
print()
print('ANSWER:', text)
"
