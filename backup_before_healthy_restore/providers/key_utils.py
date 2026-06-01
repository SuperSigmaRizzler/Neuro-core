import random
from typing import List, Sequence, Tuple


def masked_secret(value: str) -> str:
    value = str(value or "")

    if len(value) <= 10:
        return "hidden-secret"

    return value[:6] + "..." + value[-4:]


def pick_attempt_keys(keys: Sequence[str], max_attempts: int) -> List[str]:
    clean = [k for k in keys if k]

    if not clean:
        return []

    result = []
    pool = clean[:]

    while len(result) < max_attempts:
        random.shuffle(pool)
        result.extend(pool)

    return result[:max_attempts]


def cloudflare_pairs(
    account_ids: Sequence[str],
    tokens: Sequence[str],
    max_attempts: int
) -> List[Tuple[str, str]]:
    ids = [x for x in account_ids if x]
    toks = [x for x in tokens if x]

    if not ids or not toks:
        return []

    pairs = []

    if len(ids) == 1:
        pairs = [(ids[0], token) for token in toks]
    elif len(toks) == 1:
        pairs = [(account_id, toks[0]) for account_id in ids]
    else:
        pairs = [(ids[i], toks[i]) for i in range(min(len(ids), len(toks)))]

    result = []

    while len(result) < max_attempts:
        random.shuffle(pairs)
        result.extend(pairs)

    return result[:max_attempts]


def first_available(*groups):
    for group in groups:
        if group:
            return group
    return []
