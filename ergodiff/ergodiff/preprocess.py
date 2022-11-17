def preprocess_str_to_pool(candidate: str):
    pool = []
    for line in candidate.splitlines(keepends=False):
        if len(line) == 0:  # TODO: If I cannot find
            continue
        pool.append(line.rstrip())
    return pool
