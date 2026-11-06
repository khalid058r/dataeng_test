"""Inversion des mots et justification de texte, avec la bibliothèque standard."""


def reverse_words(s: str) -> str:
    """Inverser les mots en conservant un seul espace entre eux."""
    words = s.split()
    return " ".join(reversed(words))


def full_justify(words: list[str], max_width: int) -> list[str]:
    """Remplir chaque ligne, puis répartir les espaces en privilégiant la gauche.

    Les mots sont non vides, sans espaces, et tiennent dans max_width.
    La dernière ligne et les lignes à un seul mot sont alignées à gauche.
    """
    if max_width < 1:
        raise ValueError("la largeur doit être positive")
    if not words or any(not word or len(word) > max_width for word in words):
        raise ValueError("fournir des mots non vides qui tiennent dans la largeur")

    lines = []
    start = 0
    while start < len(words):
        end = start
        letters = 0
        # end - start est le nombre d'espaces minimum avant le nouveau mot.
        while end < len(words) and letters + len(words[end]) + (end - start) <= max_width:
            letters += len(words[end])
            end += 1

        gaps = end - start - 1
        if end == len(words) or gaps == 0:
            line = " ".join(words[start:end]).ljust(max_width)
        else:
            base_spaces, extra_spaces = divmod(max_width - letters, gaps)
            parts = []
            for index in range(start, end - 1):
                gap_width = base_spaces
                if index - start < extra_spaces:
                    gap_width += 1
                parts.append(words[index])
                parts.append(" " * gap_width)
            parts.append(words[end - 1])
            line = "".join(parts)

        lines.append(line)
        start = end

    return lines
