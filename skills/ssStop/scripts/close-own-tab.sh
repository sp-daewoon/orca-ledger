#!/bin/sh
# Close the Orca tab that hosts this agent session, a moment after the reply ends.
#
# Orca tells a session which terminal it is: ORCA_TERMINAL_HANDLE is set in every
# managed terminal, and `orca terminal show` with no handle describes the current one.
# Never use a terminal id copied from a ledger: a resumed session runs in a new tab
# and the recorded id points at the old one, so the close silently misses.
#
# The close is detached (nohup) so it outlives the agent's turn; the short delay lets
# the final reply render before the tab disappears.
O=$(command -v orca || echo /Applications/Orca.app/Contents/Resources/bin/orca)
DELAY=${1:-2}
HANDLE=${ORCA_TERMINAL_HANDLE:-}
if [ -z "$HANDLE" ]; then
  HANDLE=$("$O" terminal show --json 2>/dev/null | grep -o '"handle": *"term_[^"]*"' | head -1 | grep -o 'term_[^"]*')
fi
[ -n "$HANDLE" ] || { echo "ERROR: this session is not in an Orca-managed terminal"; exit 1; }
"$O" terminal show --terminal "$HANDLE" >/dev/null 2>&1 || { echo "ERROR: Orca does not recognise $HANDLE"; exit 1; }
nohup /bin/sh -c "sleep $DELAY; '$O' terminal close --terminal $HANDLE --tab" >/dev/null 2>&1 </dev/null &
echo "closing tab of $HANDLE in ${DELAY}s"
