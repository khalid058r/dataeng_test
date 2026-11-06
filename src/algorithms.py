"""Solutions des deux exercices : mots inversés et texte justifié."""


def reverse_words(s: str) -> str:
    """Inverser l'ordre des mots avec un seul espace entre eux."""
    words = s.split()
    return " ".join(reversed(words))


def full_justify(words: list[str], max_width: int) -> list[str]:
    """Former des lignes de max_width caractères.

    Le surplus d'espaces va aux premiers intervalles.
    La dernière ligne et les lignes à un mot sont alignées à gauche.
    Les mots sont non vides, sans espaces, et tiennent dans la largeur.
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
        # Compter un espace entre les mots pour tester la place.
        while end < len(words) and letters + len(words[end]) + (end - start) <= max_width:
            letters += len(words[end])
            end += 1

        gaps = end - start - 1
        if end == len(words) or gaps == 0:
            line = " ".join(words[start:end]).ljust(max_width)
        else:
            # Donner les espaces en plus aux premiers intervalles.
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
