"""Input Sanitizer — membersihkan input pengguna sebelum masuk ke pipeline."""
import re
import unicodedata

_HTML_TAG_RE = re.compile(r"<[^>]{0,200}>", re.DOTALL)
_CONTROL_CHAR_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
_MULTI_WHITESPACE_RE = re.compile(r"[ \t]{2,}")


class InputSanitizer:
    MAX_LENGTH = 2000

    def sanitize(self, raw_input: str) -> str:
        """Bersihkan input pengguna.

        Langkah:
        1. Normalisasi encoding ke Unicode NFC
        2. Strip HTML/XML tags
        3. Hapus karakter kontrol (kecuali newline dan tab normal)
        4. Collapse multi-spasi
        5. Potong jika melebihi MAX_LENGTH
        6. Strip whitespace sisi kanan/kiri
        """
        if not isinstance(raw_input, str):
            raw_input = str(raw_input)

        # 1. Normalisasi Unicode NFC
        text = unicodedata.normalize("NFC", raw_input)

        # 2. Strip HTML tags
        text = _HTML_TAG_RE.sub(" ", text)

        # 3. Hapus karakter kontrol (pertahankan \n \t)
        text = _CONTROL_CHAR_RE.sub("", text)

        # 4. Collapse multiple spaces/tabs (bukan newlines)
        text = _MULTI_WHITESPACE_RE.sub(" ", text)

        # 5. Potong
        if len(text) > self.MAX_LENGTH:
            text = text[: self.MAX_LENGTH]

        # 6. Strip
        return text.strip()
