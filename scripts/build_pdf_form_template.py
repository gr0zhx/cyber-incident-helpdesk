"""Script sekali-jalan: tambahkan AcroForm text field & checkbox di atas
Formulir Laporan Insiden Keamanan Informasi (No. 46.5/TI.100/A.8/01/2026) resmi,
supaya bisa diisi otomatis oleh pdf_report_generator.py.

Koordinat diukur langsung dari PDF sumber pakai pdfplumber. PDF sumber
bersifat statis (tidak ada AcroForm sama sekali) sehingga field dibuat dari
nol di posisi yang sama dengan garis titik-titik / kotak checkbox pada
dokumen asli.

Jalankan: python scripts/build_pdf_form_template.py
"""
from pathlib import Path

from pypdf import PdfReader, PdfWriter
from pypdf._page import PageObject
from pypdf.generic import (
    ArrayObject,
    BooleanObject,
    DecodedStreamObject,
    DictionaryObject,
    NameObject,
    NumberObject,
    TextStringObject,
)

SOURCE_PDF = Path("TA (Progress Saya)/1. Form Laporan Insiden Keamanan Informasi.pdf")
OUTPUT_PDF = Path("app/dashboard/assets/formulir_template.pdf")

PAGE_HEIGHT = 841.8


def rect(x0: float, top: float, x1: float, bottom: float) -> list[float]:
    """Convert koordinat pdfplumber (origin kiri-atas) ke rect PDF (origin kiri-bawah)."""
    return [x0, PAGE_HEIGHT - bottom, x1, PAGE_HEIGHT - top]


# (page_index, field_name, rect, kind) — kind: "text" | "checkbox"
FIELDS: list[tuple[int, str, list[float], str]] = [
    # ── PAGE 1 — Bagian A: Informasi Pelapor ──
    (0, "nama_pelapor", rect(152, 165.4, 478, 188.6), "text"),
    (0, "nip_identitas", rect(152, 190.2, 478, 213.4), "text"),
    (0, "unit_kerja", rect(152, 215.0, 478, 238.0), "text"),
    (0, "no_telp_hp", rect(152, 239.6, 478, 262.8), "text"),
    (0, "tanggal_jam_lapor", rect(152, 264.4, 478, 287.7), "text"),
    (0, "media_email", rect(150.2, 290.6, 161.2, 301.6), "checkbox"),
    (0, "media_telepon", rect(188.2, 290.6, 199.2, 301.6), "checkbox"),
    (0, "media_whatsapp", rect(240.5, 290.6, 251.5, 301.6), "checkbox"),
    (0, "media_datang_langsung", rect(303.1, 290.6, 314.1, 301.6), "checkbox"),
    (0, "media_sistem_tiket", rect(395.5, 290.6, 406.5, 301.6), "checkbox"),

    # ── PAGE 1 — Bagian B: Deskripsi Kejadian ──
    (0, "waktu_hari", rect(66.4, 383.6, 149.8, 394.6), "text"),
    (0, "waktu_tanggal", rect(192.2, 383.6, 275.4, 394.6), "text"),
    (0, "waktu_jam", rect(300.8, 383.6, 384.0, 394.6), "text"),
    (0, "lokasi_kejadian", rect(42.6, 451.0, 459.4, 462.0), "text"),
    (0, "kronologi_line1", rect(42.6, 533.1, 459.4, 544.1), "text"),
    (0, "kronologi_line2", rect(42.6, 555.7, 459.4, 566.7), "text"),
    (0, "kronologi_line3", rect(42.6, 578.1, 459.2, 589.1), "text"),
    (0, "bukti_screenshot", rect(42.6, 622.5, 53.6, 633.5), "checkbox"),
    (0, "bukti_file_log", rect(42.6, 645.9, 53.6, 656.9), "checkbox"),
    (0, "bukti_email_phishing", rect(42.6, 669.3, 53.6, 680.3), "checkbox"),
    (0, "bukti_lainnya", rect(42.6, 692.7, 53.6, 703.7), "checkbox"),
    (0, "bukti_lainnya_text", rect(95.8, 693.9, 179.0, 704.9), "text"),

    # ── PAGE 2 — Bagian C: Triase dan Analisis ──
    (1, "kategori_akses_ilegal", rect(43.6, 190.4, 54.6, 201.4), "checkbox"),
    (1, "kategori_malware_virus", rect(43.6, 216.0, 54.6, 227.0), "checkbox"),
    (1, "kategori_kebocoran_data", rect(43.6, 241.6, 54.6, 252.6), "checkbox"),
    (1, "kategori_serangan_web", rect(43.6, 267.2, 54.6, 278.2), "checkbox"),
    (1, "kategori_ketersediaan", rect(43.6, 293.0, 54.6, 304.0), "checkbox"),
    (1, "kategori_pelanggaran_fisik", rect(43.6, 318.6, 54.6, 329.6), "checkbox"),
    (1, "kategori_lainnya", rect(43.6, 344.2, 54.6, 355.2), "checkbox"),
    (1, "kategori_lainnya_text", rect(150.2, 345.2, 383.8, 356.2), "text"),
    (1, "severity_low", rect(519.4, 417.9, 530.4, 428.9), "checkbox"),
    (1, "severity_medium", rect(519.4, 443.5, 530.4, 454.5), "checkbox"),
    (1, "severity_high", rect(519.4, 469.3, 530.4, 480.3), "checkbox"),
    (1, "severity_critical", rect(519.4, 494.9, 530.4, 505.9), "checkbox"),
    (1, "cia_conf_terjaga", rect(217.1, 542.3, 228.1, 553.3), "checkbox"),
    (1, "cia_conf_terlanggar", rect(265.9, 542.3, 276.9, 553.3), "checkbox"),
    (1, "cia_integ_terjaga", rect(176.2, 565.7, 187.2, 576.7), "checkbox"),
    (1, "cia_integ_terlanggar", rect(225.1, 565.7, 236.1, 576.7), "checkbox"),
    (1, "cia_avail_terjaga", rect(204.9, 589.1, 215.9, 600.1), "checkbox"),
    (1, "cia_avail_terganggu", rect(253.7, 589.1, 264.7, 600.1), "checkbox"),

    # ── PAGE 2/3 — Bagian D: Tindakan Penanganan & Pemulihan ──
    (1, "containment_line1", rect(42.6, 703.1, 459.2, 714.1), "text"),
    (2, "containment_line2", rect(42.6, 118.8, 459.4, 129.8), "text"),
    (2, "recovery_line1", rect(42.6, 186.2, 459.5, 197.2), "text"),
    (2, "recovery_line2", rect(42.6, 208.8, 459.4, 219.8), "text"),
    (2, "penyelesaian_tanggal", rect(82.6, 253.8, 165.8, 264.8), "text"),
    (2, "penyelesaian_jam", rect(191.2, 253.8, 274.6, 264.8), "text"),
    (2, "total_durasi_jam", rect(360.8, 253.8, 394.1, 264.8), "text"),

    # ── PAGE 3 — Bagian E: Pengesahan dan Penutupan ──
    (2, "status_open", rect(42.6, 343.2, 53.6, 354.2), "checkbox"),
    (2, "status_monitoring", rect(42.6, 366.6, 53.6, 377.6), "checkbox"),
    (2, "status_closed", rect(42.6, 390.1, 53.6, 401.1), "checkbox"),
    # x1 dipersempit dari 116.6 -> 112: pada PDF asli, ")" penutup kolom Pelapor menyatu
    # dalam satu glyph run dengan titik-titiknya (beda dari kolom lain yang ")" terpisah),
    # jadi kalau field selebar penuh, mask penutup titik-titik ikut menutup ")" itu juga.
    (2, "ttd_pelapor_nama", rect(49.4, 479.4, 112.0, 490.4), "text"),
    (2, "ttd_penerima_nama", rect(134.6, 479.4, 237.4, 490.4), "text"),
    (2, "ttd_ketua_csirt_nama", rect(263.5, 479.4, 377.2, 490.4), "text"),
    (2, "ttd_pelapor_tgl", rect(64, 504.3, 125, 515.3), "text"),
    (2, "ttd_penerima_tgl", rect(150, 504.3, 254, 515.3), "text"),
    (2, "ttd_ketua_csirt_tgl", rect(278, 504.3, 397, 515.3), "text"),
    (2, "ttd_mengetahui_tgl", rect(421, 504.3, 530, 515.3), "text"),
]

FONT_SIZE = 10  # dikalibrasi supaya sebanding dengan label formulir (~11pt) dan tetap
                # muat ~85 karakter/baris pada lebar baris asli (~417pt) — lihat
                # _LINE_CHAR_BUDGET di pdf_report_generator.py.


def _text_annotation(name: str, box: list[float]) -> DictionaryObject:
    """Field teks satu baris. Formulir resmi hanya punya baris titik-titik tunggal per
    baris cetak — pypdf tidak mendukung word-wrap otomatis untuk field multiline saat
    generate appearance sendiri, jadi field panjang (kronologi, containment, recovery)
    dipecah jadi beberapa field satu-baris (lihat FIELDS) dan dibungkus manual di
    pdf_report_generator.py (_wrap_lines). Font size default di sini bisa di-override
    per nilai saat fill-time (lihat _fit_font_size di pdf_report_generator.py) — dipakai
    untuk kolom tanda tangan yang sempit tapi isinya panjangnya bervariasi, karena
    auto-size bawaan pypdf (Tf 0) hanya mengikuti TINGGI kotak, bukan lebar teks."""
    annot = DictionaryObject()
    annot[NameObject("/FT")] = NameObject("/Tx")
    annot[NameObject("/Subtype")] = NameObject("/Widget")
    annot[NameObject("/T")] = TextStringObject(name)
    annot[NameObject("/Rect")] = ArrayObject([NumberObject(v) for v in box])
    annot[NameObject("/V")] = TextStringObject("")
    annot[NameObject("/DA")] = TextStringObject(f"/Helv {FONT_SIZE} Tf 0 g")
    annot[NameObject("/F")] = NumberObject(4)  # Print flag
    return annot


def _form_xobject(writer: PdfWriter, width: float, height: float, content: bytes) -> DictionaryObject:
    stream = DecodedStreamObject()
    stream.set_data(content)
    stream[NameObject("/Type")] = NameObject("/XObject")
    stream[NameObject("/Subtype")] = NameObject("/Form")
    stream[NameObject("/FormType")] = NumberObject(1)
    stream[NameObject("/BBox")] = ArrayObject(
        [NumberObject(0), NumberObject(0), NumberObject(width), NumberObject(height)]
    )
    ref = writer._add_object(stream)
    return ref


def _checkbox_annotation(writer: PdfWriter, name: str, box: list[float]) -> DictionaryObject:
    width = box[2] - box[0]
    height = box[3] - box[1]
    off_xobj = _form_xobject(writer, width, height, b"")
    # "X" mark memenuhi kotak, sedikit margin. Margin 0.26 sudah diverifikasi presisi
    # (ink bounding box X == ink bounding box kotak kosong, diukur render 1200 DPI) —
    # kalau ingin memperbesar tanda, naikkan STROKE WIDTH (garis lebih tebal), jangan
    # kurangi margin, karena itu akan membuat X meluber keluar kotak asli.
    m = min(width, height) * 0.26
    on_content = (
        f"0 G 1 J 1 j 1.8 w {m:.2f} {m:.2f} m {width - m:.2f} {height - m:.2f} l S "
        f"{m:.2f} {height - m:.2f} m {width - m:.2f} {m:.2f} l S"
    ).encode("ascii")
    on_xobj = _form_xobject(writer, width, height, on_content)

    normal_states = DictionaryObject()
    normal_states[NameObject("/Off")] = off_xobj
    normal_states[NameObject("/Yes")] = on_xobj
    ap_dict = DictionaryObject()
    ap_dict[NameObject("/N")] = normal_states

    annot = DictionaryObject()
    annot[NameObject("/FT")] = NameObject("/Btn")
    annot[NameObject("/Subtype")] = NameObject("/Widget")
    annot[NameObject("/T")] = TextStringObject(name)
    annot[NameObject("/Rect")] = ArrayObject([NumberObject(v) for v in box])
    annot[NameObject("/V")] = NameObject("/Off")
    annot[NameObject("/AS")] = NameObject("/Off")
    annot[NameObject("/F")] = NumberObject(4)
    annot[NameObject("/AP")] = ap_dict
    return annot


def _cover_dots(writer: PdfWriter, page_boxes: dict[int, list[list[float]]], pad: float = 1.0) -> None:
    """Tutup garis titik-titik asli di setiap box teks dengan kotak putih, digambar sebagai
    layer konten halaman tambahan (di atas konten asli, di bawah annotation field), supaya
    teks yang diisi tidak tampil dobel/tercoret oleh titik-titik lama di baliknya."""
    for page_index, boxes in page_boxes.items():
        page = writer.pages[page_index]
        ops = ["q", "1 g"]
        for box in boxes:
            x0, y0, x1, y1 = box[0] - pad, box[1] - pad, box[2] + pad, box[3] + pad
            ops.append(f"{x0:.2f} {y0:.2f} {x1 - x0:.2f} {y1 - y0:.2f} re f")
        ops.append("Q")
        content = " ".join(ops).encode("ascii")

        mask_page = PageObject.create_blank_page(width=page.mediabox.width, height=page.mediabox.height)
        stream = DecodedStreamObject()
        stream.set_data(content)
        mask_page.replace_contents(stream)
        page.merge_page(mask_page, over=True)


def _default_resources() -> DictionaryObject:
    font_dict = DictionaryObject()
    helv = DictionaryObject()
    helv[NameObject("/Type")] = NameObject("/Font")
    helv[NameObject("/Subtype")] = NameObject("/Type1")
    helv[NameObject("/BaseFont")] = NameObject("/Helvetica")
    helv[NameObject("/Encoding")] = NameObject("/WinAnsiEncoding")
    font_dict[NameObject("/Helv")] = helv
    dr = DictionaryObject()
    dr[NameObject("/Font")] = font_dict
    return dr


# Sel tabel Bagian A (Informasi Pelapor) kosong di PDF asli — tidak ada titik-titik
# yang perlu ditutup di sana, dan menutupinya berisiko memakan garis tabel di
# sekitarnya. Hanya field yang benar-benar duduk di atas garis titik-titik yang perlu
# di-mask (lihat pengukuran koordinat asli).
_NO_MASK_FIELDS = {
    "nama_pelapor", "nip_identitas", "unit_kerja", "no_telp_hp", "tanggal_jam_lapor",
}


def build() -> None:
    reader = PdfReader(str(SOURCE_PDF))
    writer = PdfWriter()
    writer.append(reader)

    text_boxes_by_page: dict[int, list[list[float]]] = {}
    for page_index, name, box, kind in FIELDS:
        if kind != "checkbox" and name not in _NO_MASK_FIELDS:
            text_boxes_by_page.setdefault(page_index, []).append(box)
    _cover_dots(writer, text_boxes_by_page, pad=0.4)

    field_refs = ArrayObject()
    for page_index, name, box, kind in FIELDS:
        if kind == "checkbox":
            annot = _checkbox_annotation(writer, name, box)
        else:
            annot = _text_annotation(name, box)
        added = writer.add_annotation(page_number=page_index, annotation=annot)
        field_refs.append(added.indirect_reference)

    acro_form = DictionaryObject()
    acro_form[NameObject("/Fields")] = field_refs
    # NeedAppearances=False: appearance sudah kita generate sendiri saat mengisi
    # field (auto_regenerate=False di pdf_report_generator.py). Kalau True, sebagian
    # viewer (Chrome/Acrobat) meregenerasi ulang appearance dengan font/posisinya
    # sendiri saat file di-save/print — menyebabkan teks meluber keluar baris.
    acro_form[NameObject("/NeedAppearances")] = BooleanObject(False)
    acro_form[NameObject("/DA")] = TextStringObject(f"/Helv {FONT_SIZE} Tf 0 g")
    acro_form[NameObject("/DR")] = _default_resources()
    writer._root_object[NameObject("/AcroForm")] = acro_form

    OUTPUT_PDF.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PDF, "wb") as fh:
        writer.write(fh)
    print(f"Template ditulis ke {OUTPUT_PDF} ({len(FIELDS)} field)")


if __name__ == "__main__":
    build()
