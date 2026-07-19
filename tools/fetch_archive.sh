#!/usr/bin/env bash
# Re-fetch the source material for this archive from the Wayback Machine.
#
# Everything under archive/raw/ and the recovered ZIPs were produced by this script.
# It is idempotent: existing, non-empty files are left alone, so a re-run only
# fills gaps. web.archive.org rate-limits aggressively, hence the retry flags.
#
#   usage: tools/fetch_archive.sh [output-dir]     (default: ./archive/_fetch)
set -euo pipefail

OUT="${1:-archive/_fetch}"
CDX="http://web.archive.org/cdx/search/cdx"
CURL=(curl -sL --max-time 300 --retry 6 --retry-delay 5 --retry-all-errors)

mkdir -p "$OUT"/{raw/etc-cmu,raw/google-sites,bin,img}

# ---------------------------------------------------------------------------
# 1. enumerate every capture the Wayback Machine holds for both hosts
# ---------------------------------------------------------------------------
echo "==> enumerating captures"
"${CURL[@]}" "$CDX?url=etc.cmu.edu/projects/pandai*&output=text&fl=timestamp,original,mimetype,statuscode&collapse=urlkey" \
  -o "$OUT/cdx-etc-cmu.txt"
"${CURL[@]}" "$CDX?url=sites.google.com/site/etcpandai*&output=text&fl=timestamp,original,mimetype,statuscode&collapse=urlkey" \
  -o "$OUT/cdx-google-sites.txt"
echo "    etc.cmu.edu:        $(wc -l < "$OUT/cdx-etc-cmu.txt") captures"
echo "    sites.google.com:   $(wc -l < "$OUT/cdx-google-sites.txt") captures"

# The "id_" modifier asks for the original bytes, without the Wayback banner and
# without its rewriting of embedded URLs.
fetch() { # fetch <timestamp> <original-url> <destination>
  [ -s "$3" ] && return 0
  "${CURL[@]}" "https://web.archive.org/web/${1}id_/${2}" -o "$3"
  printf '    %-52s %8s bytes\n' "$(basename "$3")" "$(wc -c < "$3" | tr -d ' ')"
}

# ---------------------------------------------------------------------------
# 2. the 2010 ETC pages
# ---------------------------------------------------------------------------
echo "==> etc.cmu.edu pages"
for page in index aitypes Community Download Gallery Pathfinding Research Team; do
  ts=$(awk -v want="/$page.html" '$2 ~ want && $4 == "200" { print $1; exit }' "$OUT/cdx-etc-cmu.txt")
  [ -n "$ts" ] || { echo "    !! no capture for $page.html"; continue; }
  fetch "$ts" "http://www.etc.cmu.edu/projects/pandai/$page.html" "$OUT/raw/etc-cmu/$page.html"
done

# ---------------------------------------------------------------------------
# 3. the Google Sites wiki (skip /system/, which is Google's own chrome)
# ---------------------------------------------------------------------------
echo "==> sites.google.com pages"
awk '$3 == "text/html" && $4 == "200" { print $1, $2 }' "$OUT/cdx-google-sites.txt" \
  | grep -v '/system/' \
  | while read -r ts url; do
      slug=$(printf '%s' "$url" | sed 's#https://sites.google.com/site/etcpandai/##; s#/$##; s#/#__#g')
      [ -n "$slug" ] || slug="index"
      fetch "$ts" "$url" "$OUT/raw/google-sites/$slug.html"
    done

# ---------------------------------------------------------------------------
# 4. binaries and images
# ---------------------------------------------------------------------------
echo "==> etc.cmu.edu downloads and images"
grep -E '\.(zip|docx)' "$OUT/cdx-etc-cmu.txt" | while read -r ts url mime st; do
  [ "$st" = "200" ] || continue
  name=$(basename "$url" | python3 -c 'import sys,urllib.parse; print(urllib.parse.unquote(sys.stdin.read().strip()))')
  fetch "$ts" "$url" "$OUT/bin/$name"
done

grep -E 'image/' "$OUT/cdx-etc-cmu.txt" | while read -r ts url mime st; do
  name=$(basename "$url" | python3 -c 'import sys,urllib.parse; print(urllib.parse.unquote(sys.stdin.read().strip()))')
  fetch "$ts" "$url" "$OUT/img/$name"
done

# Google Sites served attachments through a 302 to a signed URL, so these need the
# redirect followed rather than the "id_" raw-bytes form used above.
echo "==> sites.google.com attachments"
grep -E '\.zip\?attredirects=0&d=1' "$OUT/cdx-google-sites.txt" | while read -r ts url mime st; do
  name=$(basename "${url%%\?*}")
  dest="$OUT/bin/$name"
  [ -s "$dest" ] && continue
  "${CURL[@]}" "https://web.archive.org/web/${ts}/${url}" -o "$dest"
  printf '    %-52s %8s bytes\n' "$name" "$(wc -c < "$dest" | tr -d ' ')"
done

echo "==> done; fetched into $OUT"
echo "    Compare against the committed copies before replacing anything:"
echo "      diff -rq $OUT/raw archive/raw"
