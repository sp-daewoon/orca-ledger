#!/bin/sh
# Close the Orca tab hosting the calling agent session after a short delay.
# Resolves the terminal from this process's own environment (ORCA_TAB_ID /
# ORCA_AGENT_PANE), never from a ledger: a resumed session usually runs in a
# new tab, and a recorded terminal id points at the old one.
# Detached with nohup so it outlives the agent's turn.
O=$(command -v orca || echo /Applications/Orca.app/Contents/Resources/bin/orca)
[ -n "$ORCA_TAB_ID" ] || { echo "ERROR: not inside an Orca tab (ORCA_TAB_ID is empty)"; exit 1; }
LEAF=${ORCA_AGENT_PANE#*:}
LIST=$("$O" terminal list 2>/dev/null)
TERM_ID=$(printf '%s\n' "$LIST" | grep "tab=$ORCA_TAB_ID" | grep "leaf=$LEAF" | grep -o 'term_[0-9a-f-]*' | head -1)
[ -n "$TERM_ID" ] || TERM_ID=$(printf '%s\n' "$LIST" | grep "tab=$ORCA_TAB_ID" | grep -o 'term_[0-9a-f-]*' | head -1)
[ -n "$TERM_ID" ] || { echo "ERROR: no terminal found for tab $ORCA_TAB_ID"; exit 1; }
DELAY=${1:-3}
nohup /bin/sh -c "sleep $DELAY; '$O' terminal close --terminal $TERM_ID --tab" >/dev/null 2>&1 </dev/null &
echo "closing $TERM_ID (tab $ORCA_TAB_ID) in ${DELAY}s"
