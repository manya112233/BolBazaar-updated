// Maps each English produce name to all recognised aliases:
// Hindi script, common romanised transliterations, and alternate spellings.
// Add more entries here as the catalogue grows.
const PRODUCE_ALIASES: Record<string, string[]> = {
  tomato:      ['tomato', 'टमाटर', 'tamatar', 'tamato', 'tamatoes'],
  onion:       ['onion', 'प्याज', 'pyaaz', 'pyaz', 'pyaj', 'kanda', 'dungri'],
  potato:      ['potato', 'आलू', 'aloo', 'alu', 'alloo'],
  carrot:      ['carrot', 'गाजर', 'gajar', 'gazar'],
  cabbage:     ['cabbage', 'पत्ता गोभी', 'patta gobhi', 'bandh gobhi', 'band gobhi', 'gobhi'],
  cauliflower: ['cauliflower', 'फूल गोभी', 'phool gobhi', 'phul gobhi', 'gobi', 'gobhi'],
  spinach:     ['spinach', 'पालक', 'palak'],
  greens:      ['greens', 'हरी सब्जियां', 'hari sabji', 'hari sabzi', 'sabzi', 'sabji'],
  banana:      ['banana', 'केला', 'kela', 'kele'],
  mango:       ['mango', 'आम', 'aam', 'am'],
  apple:       ['apple', 'सेब', 'seb'],
};

// Pre-build a flat lookup: alias → canonical English key
const _aliasToKey = new Map<string, string>();
for (const [key, aliases] of Object.entries(PRODUCE_ALIASES)) {
  for (const alias of aliases) {
    _aliasToKey.set(alias.toLowerCase(), key);
  }
}

/**
 * Returns all equivalent search terms for a query string.
 * If the query matches a known alias (Hindi, transliteration, or English),
 * all aliases for that produce are returned. Otherwise returns [query].
 */
function expandQuery(query: string): string[] {
  const q = query.trim().toLowerCase();
  if (!q) return [q];

  // Direct lookup
  if (_aliasToKey.has(q)) {
    const key = _aliasToKey.get(q)!;
    return PRODUCE_ALIASES[key].map((a) => a.toLowerCase());
  }

  // Substring lookup — e.g. query "pyaz" contained in alias "pyaaz" or vice-versa
  for (const [alias, key] of _aliasToKey.entries()) {
    if (alias.includes(q) || q.includes(alias)) {
      return PRODUCE_ALIASES[key].map((a) => a.toLowerCase());
    }
  }

  return [q];
}

/**
 * Returns true if `text` matches `query`, taking Hindi aliases and
 * transliterations into account.
 *
 * Drop-in replacement for:
 *   text.toLowerCase().includes(query.toLowerCase())
 */
export function matchesProduceQuery(text: string, query: string): boolean {
  const q = query.trim().toLowerCase();
  if (!q) return true;
  const haystack = text.toLowerCase();
  // Fast path — direct substring match
  if (haystack.includes(q)) return true;
  // Alias expansion
  const terms = expandQuery(q);
  return terms.some((term) => haystack.includes(term));
}
