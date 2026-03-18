"""
PDF generator untuk i-Kira
Menggunakan reportlab
"""
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from io import BytesIO
from django.http import HttpResponse
from utils.number_utils import format_rupiah, terbilang


# Warna brand
BRAND_BLUE = colors.HexColor('#1F4E79')
LIGHT_BLUE = colors.HexColor('#DEEAF1')
YELLOW = colors.HexColor('#FFF2CC')
GRAY = colors.HexColor('#F2F2F2')


def get_styles():
    styles = getSampleStyleSheet()
    custom = {
        'title': ParagraphStyle('title', fontSize=14, fontName='Helvetica-Bold',
                                 textColor=BRAND_BLUE, alignment=TA_CENTER, spaceAfter=4),
        'subtitle': ParagraphStyle('subtitle', fontSize=10, fontName='Helvetica',
                                    alignment=TA_CENTER, spaceAfter=2),
        'heading': ParagraphStyle('heading', fontSize=10, fontName='Helvetica-Bold',
                                   textColor=BRAND_BLUE, spaceBefore=8, spaceAfter=4),
        'normal': ParagraphStyle('normal', fontSize=9, fontName='Helvetica',
                                  spaceAfter=2),
        'right': ParagraphStyle('right', fontSize=9, fontName='Helvetica',
                                 alignment=TA_RIGHT),
        'bold': ParagraphStyle('bold', fontSize=9, fontName='Helvetica-Bold'),
        'small': ParagraphStyle('small', fontSize=8, fontName='Helvetica',
                                 textColor=colors.gray),
    }
    return custom


def generate_payslip_pdf(payroll_detail):
    """
    Generate slip gaji PDF untuk satu karyawan.
    Returns HttpResponse dengan file PDF.
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        rightMargin=1.5*cm, leftMargin=1.5*cm,
        topMargin=1.5*cm, bottomMargin=1.5*cm
    )

    S = get_styles()
    d = payroll_detail
    emp = d.employee
    payroll = d.payroll
    story = []

    # Header
    story.append(Paragraph("SLIP GAJI KARYAWAN", S['title']))
    story.append(Paragraph(f"Periode: {payroll.periode}", S['subtitle']))
    story.append(HRFlowable(width="100%", thickness=2, color=BRAND_BLUE))
    story.append(Spacer(1, 0.3*cm))

    # Info karyawan
    info_data = [
        ['NIK', ':', emp.nik, 'Departemen', ':', str(emp.department) if emp.department else '-'],
        ['Nama', ':', emp.nama, 'Jabatan', ':', str(emp.jabatan) if emp.jabatan else '-'],
        ['Status', ':', emp.status_karyawan, 'Tgl Masuk', ':', emp.join_date.strftime('%d/%m/%Y') if emp.join_date else '-'],
    ]
    info_table = Table(info_data, colWidths=[2.5*cm, 0.5*cm, 5*cm, 2.5*cm, 0.5*cm, 5*cm])
    info_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (3, 0), (3, -1), 'Helvetica-Bold'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ROWBACKGROUNDS', (0, 0), (-1, -1), [GRAY, colors.white]),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 0.4*cm))

    # Absensi
    story.append(Paragraph("RINGKASAN ABSENSI", S['heading']))
    att_data = [
        ['Hari Kerja', 'Hari Hadir', 'Hari Absen', 'Terlambat (menit)', 'Lembur (jam)'],
        [str(d.hari_kerja), str(d.hari_hadir), str(d.hari_absen),
         str(d.menit_telat), str(d.jam_lembur)],
    ]
    att_table = Table(att_data, colWidths=[3.4*cm]*5)
    att_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), BRAND_BLUE),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ('BACKGROUND', (0, 1), (-1, 1), LIGHT_BLUE),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(att_table)
    story.append(Spacer(1, 0.4*cm))

    # Pendapatan & Potongan side by side
    story.append(Paragraph("RINCIAN GAJI", S['heading']))

    pendapatan = [
        ['PENDAPATAN', 'JUMLAH'],
        ['Gaji Pokok', format_rupiah(d.gaji_pokok)],
        ['Tunjangan Transport', format_rupiah(d.tunjangan_transport)],
        ['Tunjangan Makan', format_rupiah(d.tunjangan_makan)],
        ['Tunjangan Komunikasi', format_rupiah(d.tunjangan_komunikasi)],
        ['Tunjangan Kesehatan', format_rupiah(d.tunjangan_kesehatan)],
        ['Tunjangan Jabatan', format_rupiah(d.tunjangan_jabatan)],
        ['Tunjangan Keahlian', format_rupiah(d.tunjangan_keahlian)],
        ['Upah Lembur', format_rupiah(d.upah_lembur)],
        ['GAJI KOTOR', format_rupiah(d.gaji_kotor)],
    ]

    potongan = [
        ['POTONGAN', 'JUMLAH'],
        ['BPJS Kesehatan', format_rupiah(d.bpjs_kesehatan)],
        ['BPJS Ketenagakerjaan', format_rupiah(d.bpjs_ketenagakerjaan)],
        ['PPH 21', format_rupiah(d.pph21)],
        ['Potongan Keterlambatan', format_rupiah(d.potongan_telat)],
        ['Potongan Absen', format_rupiah(d.potongan_absen)],
        ['', ''],
        ['', ''],
        ['', ''],
        ['TOTAL POTONGAN', format_rupiah(d.total_potongan)],
    ]

    col_w = [4*cm, 3*cm]
    pend_table = Table(pendapatan, colWidths=col_w)
    pot_table = Table(potongan, colWidths=col_w)

    tbl_style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), BRAND_BLUE),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('BACKGROUND', (0, -1), (-1, -1), YELLOW),
        ('FONTSIZE', (0, 0), (-1, -1), 8.5),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ])
    pend_table.setStyle(tbl_style)
    pot_table.setStyle(tbl_style)

    combined = Table([[pend_table, Spacer(0.3*cm, 1), pot_table]])
    combined.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'TOP')]))
    story.append(combined)
    story.append(Spacer(1, 0.4*cm))

    # Gaji bersih
    bersih_data = [
        ['GAJI BERSIH (TAKE HOME PAY)', format_rupiah(d.gaji_bersih)],
        [f'Terbilang: {terbilang(d.gaji_bersih).title()}', ''],
    ]
    bersih_table = Table(bersih_data, colWidths=[12*cm, 4*cm])
    bersih_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), BRAND_BLUE),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
        ('BACKGROUND', (0, 1), (-1, 1), LIGHT_BLUE),
        ('FONTSIZE', (0, 1), (-1, 1), 8.5),
        ('SPAN', (0, 1), (1, 1)),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(bersih_table)
    story.append(Spacer(1, 0.5*cm))

    # Info bank
    if emp.bank_name:
        story.append(Paragraph(
            f"Transfer ke: {emp.bank_name} - {emp.bank_account} a.n. {emp.bank_account_name or emp.nama}",
            S['small']
        ))

    # Tanda tangan
    story.append(Spacer(1, 1*cm))
    ttd_data = [
        ['Mengetahui,', '', 'Menerima,'],
        ['', '', ''],
        ['', '', ''],
        ['(HRD / Manager)', '', f'({emp.nama})'],
    ]
    ttd_table = Table(ttd_data, colWidths=[5*cm, 7*cm, 5*cm])
    ttd_table.setStyle(TableStyle([
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('TOPPADDING', (0, 3), (-1, 3), 2),
    ]))
    story.append(ttd_table)

    doc.build(story)
    buffer.seek(0)

    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = (
        f'inline; filename="slip_gaji_{emp.nik}_{payroll.periode}.pdf"'
    )
    return response


def generate_severance_pdf(severance):
    """Generate dokumen perhitungan pesangon PDF."""
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        rightMargin=2*cm, leftMargin=2*cm,
        topMargin=2*cm, bottomMargin=2*cm
    )
    S = get_styles()
    emp = severance.employee
    story = []

    story.append(Paragraph("PERHITUNGAN KOMPENSASI PHK", S['title']))
    story.append(Paragraph("Berdasarkan PP No. 35 Tahun 2021 (UU Cipta Kerja)", S['subtitle']))
    story.append(HRFlowable(width="100%", thickness=2, color=BRAND_BLUE))
    story.append(Spacer(1, 0.5*cm))

    info = [
        ['Nama Karyawan', ':', emp.nama],
        ['NIK', ':', emp.nik],
        ['Departemen', ':', str(emp.department) if emp.department else '-'],
        ['Jabatan', ':', str(emp.jabatan) if emp.jabatan else '-'],
        ['Tanggal Masuk', ':', emp.join_date.strftime('%d/%m/%Y') if emp.join_date else '-'],
        ['Tanggal PHK', ':', severance.tanggal_phk.strftime('%d/%m/%Y')],
        ['Alasan PHK', ':', severance.alasan_phk],
        ['Masa Kerja', ':', f"{severance.masa_kerja_tahun} tahun {severance.masa_kerja_bulan} bulan"],
    ]
    info_table = Table(info, colWidths=[4*cm, 0.5*cm, 10*cm])
    info_table.setStyle(TableStyle([
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('ROWBACKGROUNDS', (0, 0), (-1, -1), [GRAY, colors.white]),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 0.5*cm))

    story.append(Paragraph("DASAR PERHITUNGAN", S['heading']))
    dasar = [
        ['Komponen', 'Jumlah'],
        ['Gaji Pokok', format_rupiah(severance.gaji_pokok)],
        ['Tunjangan Tetap', format_rupiah(severance.tunjangan_tetap)],
        ['Upah (Gaji Pokok + Tunjangan Tetap)', format_rupiah(severance.total_upah)],
        [f'Pengali Pesangon (x{severance.pengali_pesangon})', ''],
    ]
    story.append(Table(dasar, colWidths=[10*cm, 5*cm],
        style=TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), BRAND_BLUE),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ])
    ))
    story.append(Spacer(1, 0.4*cm))

    story.append(Paragraph("TOTAL KOMPENSASI", S['heading']))
    kompensasi = [
        ['Komponen', 'Jumlah'],
        ['Uang Pesangon (UP)', format_rupiah(severance.pesangon)],
        ['Uang Penghargaan Masa Kerja (UPMK)', format_rupiah(severance.upmk)],
        ['Uang Penggantian Hak (UPH 15%)', format_rupiah(severance.uph)],
        ['TOTAL KOMPENSASI', format_rupiah(severance.total_pesangon)],
    ]
    kompensasi_table = Table(kompensasi, colWidths=[10*cm, 5*cm])
    kompensasi_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), BRAND_BLUE),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('BACKGROUND', (0, -1), (-1, -1), YELLOW),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(kompensasi_table)
    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph(
        f"Terbilang: {terbilang(severance.total_pesangon).title()}",
        S['small']
    ))

    doc.build(story)
    buffer.seek(0)
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = (
        f'inline; filename="pesangon_{emp.nik}.pdf"'
    )
    return response
