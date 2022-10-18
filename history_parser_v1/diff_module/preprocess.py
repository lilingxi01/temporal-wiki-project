def preprocess_str_to_pool(candidate: str):
    pool = []
    for line in candidate.splitlines(keepends=False):
        if len(line) == 0:
            continue
        pool.append(line)
    return pool
