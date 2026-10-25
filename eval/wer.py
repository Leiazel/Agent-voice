def compute_wer(reference: str, hypothesis: str) -> float:
    """
    Calcula el Word Error Rate (WER) entre una transcripción de referencia y una hipótesis
    utilizando distancia de edición a nivel de palabras (Levenshtein).
    """
    ref_words = [w.strip(".,;:!?¿¡\"'") for w in reference.lower().split() if w.strip(".,;:!?¿¡\"'")]
    hyp_words = [w.strip(".,;:!?¿¡\"'") for w in hypothesis.lower().split() if w.strip(".,;:!?¿¡\"'")]

    if not ref_words:
        return 0.0 if not hyp_words else 1.0

    n, m = len(ref_words), len(hyp_words)
    dp = [[0] * (m + 1) for _ in range(n + 1)]

    for i in range(n + 1):
        dp[i][0] = i
    for j in range(m + 1):
        dp[0][j] = j

    for i in range(1, n + 1):
        for j in range(1, m + 1):
            if ref_words[i - 1] == hyp_words[j - 1]:
                dp[i][j] = dp[i - 1][j - 1]
            else:
                dp[i][j] = min(
                    dp[i - 1][j] + 1,      # Deletion
                    dp[i][j - 1] + 1,      # Insertion
                    dp[i - 1][j - 1] + 1,  # Substitution
                )

    return round(dp[n][m] / n, 4)

