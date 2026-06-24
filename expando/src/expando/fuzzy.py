from __future__ import annotations


def fuzzy_score(query: str, target: str) -> int:
    """Score how well query matches target (higher is better, 0 = no match).
    AC2 this-round: fuzzy_filter dead code removed; only fuzzy_score + fuzzy_filter_search_items shipped.
    """
    if not query:
        return 1

    query_folded = query.casefold()
    target_folded = target.casefold()

    if query_folded in target_folded:
        return 1000 + (200 - target_folded.index(query_folded))

    score = 0
    query_index = 0
    consecutive = 0
    last_match_index = -2

    for char_index, char in enumerate(target_folded):
        if query_index < len(query_folded) and char == query_folded[query_index]:
            query_index += 1
            if char_index == last_match_index + 1:
                consecutive += 1
            else:
                consecutive = 1
            score += 10 + consecutive * 5
            if char_index == 0 or target_folded[char_index - 1] in {":", "-", "_", " "}:
                score += 8
            last_match_index = char_index

    if query_index != len(query_folded):
        return 0
    return score


def item_search_text(item: dict[str, object]) -> str:
    parts = [
        str(item.get("label", "")),
        str(item.get("trigger", "")),
        str(item.get("preview", "")),
    ]
    terms = item.get("search_terms", []) or []
    parts.extend(str(term) for term in terms)
    return " ".join(part for part in parts if part)


def fuzzy_filter_search_items(query: str, items: list[dict[str, object]]) -> list[dict[str, object]]:
    if not query:
        return list(items)

    scored: list[tuple[int, dict[str, object]]] = []
    for item in items:
        score = fuzzy_score(query, item_search_text(item))
        if score > 0:
            scored.append((score, item))

    scored.sort(key=lambda pair: (-pair[0], str(pair[1].get("label", pair[1].get("trigger", "")))))
    return [item for _, item in scored]