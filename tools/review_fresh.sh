#!/usr/bin/env bash
# One review round with a blank reviewer context (docs/writing-method.md, section 7), for the Codex CLI.
# The reviewer gets a new, empty CODEX_HOME: only the login is copied, memories are off, and the session is not saved.
#   REVIEW_MODEL=<model> REVIEW_EFFORT=<effort> bash tools/review_fresh.sh <packet_dir> <out_prefix>
# packet_dir holds prompt.txt, the PDF(s) and pages/*.png. Writes <out_prefix>_raw.jsonl, .err, .code and two listings of the
# reviewer home (before and after) for the audit. Keep the model, the effort and the prompt the same from round to round.
set -u
: "${REVIEW_MODEL:?set REVIEW_MODEL}"; EFFORT="${REVIEW_EFFORT:-high}"
PK=$(readlink -f "$1"); OUT=$(readlink -f -m "$2"); SRC="${CODEX_HOME:-$HOME/.codex}"
H=$(mktemp -d "${TMPDIR:-/tmp}/review_fresh_XXXXXX")
cp "$SRC/auth.json" "$H/auth.json"; chmod 600 "$H/auth.json"
printf 'model = "%s"\nmodel_reasoning_effort = "%s"\n[features]\nmemories = false\n' "$REVIEW_MODEL" "$EFFORT" > "$H/config.toml"
ls -A "$H" > "${OUT}_home_before.txt"
cd "$PK" || exit 2
CODEX_HOME="$H" codex exec --ephemeral --skip-git-repo-check -s read-only -m "$REVIEW_MODEL" -c model_reasoning_effort="$EFFORT" \
  --json -i pages/*.png - < prompt.txt > "${OUT}_raw.jsonl" 2> "${OUT}.err"
echo $? > "${OUT}.code"
# a refreshed login token must reach the user's home, or the next login there fails
if ! cmp -s "$H/auth.json" "$SRC/auth.json"; then cp "$SRC/auth.json" "$SRC/auth.json.bak_review"; cp "$H/auth.json" "$SRC/auth.json"; fi
ls -AR "$H" > "${OUT}_home_after.txt"
rm -rf "$H"
