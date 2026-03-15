# utils/ats_analyzer.py
"""
ATS Analyzer Engine
Menganalisis kecocokan CV kandidat terhadap kualifikasi posisi / MPRF.

Output:
    {
        score          : int (0-100),
        grade          : str ('A'/'B'/'C'/'D'),
        rekomendasi    : str ('Lanjutkan'/'Pertimbangkan'/'Tolak'),
        rekomen_color  : str ('success'/'warning'/'danger'),
        skill_match    : list[str],   # skill CV ∩ kualifikasi
        skill_gap      : list[str],   # skill kualifikasi - CV
        skill_extra    : list[str],   # skill CV - kualifikasi (bonus)
        kelebihan      : list[str],
        kekurangan     : list[str],
        detail_score   : dict,        # skor per kategori
        catatan_ats    : str,         # teks siap simpan ke catatan
    }
"""

import re
from dataclasses import dataclass, field
from typing import Optional


# ─────────────────────────────────────────────────────────────────────────────
# EDUCATION LEVEL RANKING
# ─────────────────────────────────────────────────────────────────────────────

EDU_RANK = {'SD': 1, 'SMP': 2, 'SMA/SMK': 3, 'D3': 4, 'S1': 5, 'S2': 6, 'S3': 7}


def edu_rank(level: str) -> int:
    return EDU_RANK.get(level.upper().strip(), 0)


# ─────────────────────────────────────────────────────────────────────────────
# KRITERIA (dari MPRF atau input manual)
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class Kriteria:
    jabatan:           str = ''
    pendidikan_min:    str = ''          # 'S1', 'D3', dll
    pengalaman_min:    int = 0           # tahun
    skill_wajib:       list = field(default_factory=list)   # HARUS ada
    skill_diinginkan:  list = field(default_factory=list)   # nice-to-have
    kualifikasi_teks:  str = ''          # teks bebas dari MPRF

    @classmethod
    def from_mprf(cls, mprf) -> 'Kriteria':
        """Buat Kriteria dari objek ManpowerRequest Django."""
        k = cls()
        k.jabatan          = mprf.nama_jabatan
        k.kualifikasi_teks = mprf.kualifikasi or ''
        k._parse_kualifikasi_text(k.kualifikasi_teks)
        return k

    @classmethod
    def from_manual(cls, jabatan: str, pendidikan_min: str,
                    pengalaman_min: int, skill_wajib_str: str,
                    skill_diinginkan_str: str = '') -> 'Kriteria':
        """Buat Kriteria dari input manual di form."""
        k = cls()
        k.jabatan           = jabatan
        k.pendidikan_min    = pendidikan_min
        k.pengalaman_min    = pengalaman_min
        k.skill_wajib       = _parse_skill_str(skill_wajib_str)
        k.skill_diinginkan  = _parse_skill_str(skill_diinginkan_str)
        return k

    def _parse_kualifikasi_text(self, text: str):
        """Auto-parse teks kualifikasi MPRF → pendidikan, pengalaman, skill."""
        low = text.lower()

        # Pendidikan minimum
        for level in ['s3', 's2', 's1', 'd4', 'd3', 'd2', 'd1',
                      'sma/smk', 'smk', 'sma', 'smp', 'sd']:
            if level in low:
                mapping = {
                    's3': 'S3', 's2': 'S2', 's1': 'S1',
                    'd4': 'S1', 'd3': 'D3', 'd2': 'D3', 'd1': 'D3',
                    'sma/smk': 'SMA/SMK', 'smk': 'SMA/SMK', 'sma': 'SMA/SMK',
                    'smp': 'SMP', 'sd': 'SD',
                }
                self.pendidikan_min = mapping[level]
                break

        # Pengalaman minimum (cari pola "X tahun")
        m = re.search(r'(\d+)\s*[\-–]?\s*(\d+)?\s*tahun', low)
        if m:
            self.pengalaman_min = int(m.group(1))
        else:
            m2 = re.search(r'minimal?\s*(\d+)\s*tahun', low)
            if m2:
                self.pengalaman_min = int(m2.group(1))

        # Skill — tiap baris yang dimulai bullet / angka dianggap requirement
        skill_candidates = []
        for line in text.splitlines():
            line = line.strip().lstrip('-•*·1234567890.)').strip()
            if 3 <= len(line) <= 60:
                skill_candidates.append(line)

        # Pisah: wajib = semua, diinginkan = yang mengandung "diinginkan/plus"
        nice_kw = ['diinginkan', 'nilai plus', 'advantage', 'preferred',
                   'nice to have', 'menjadi nilai']
        for s in skill_candidates:
            if any(k in s.lower() for k in nice_kw):
                self.skill_diinginkan.append(s)
            else:
                self.skill_wajib.append(s)


def _parse_skill_str(s: str) -> list:
    """Split string skill oleh koma/baris/titik koma."""
    if not s:
        return []
    parts = re.split(r'[,;\n]', s)
    return [p.strip() for p in parts if p.strip() and len(p.strip()) >= 2]


# ─────────────────────────────────────────────────────────────────────────────
# SKILL MATCHER
# ─────────────────────────────────────────────────────────────────────────────

def _normalize(s: str) -> str:
    return re.sub(r'[^a-z0-9]', '', s.lower())


def _skill_match_score(cv_skills: list, required: list) -> tuple:
    """
    Return (matched_list, gap_list, score_pct).
    Menggunakan partial / fuzzy match sederhana.
    """
    if not required:
        return [], [], 100

    matched, gap = [], []
    cv_norm = [_normalize(s) for s in cv_skills]

    for req in required:
        req_norm  = _normalize(req)
        req_words = req_norm.split() if ' ' in req else [req_norm]

        found = False
        for cv_n in cv_norm:
            # Exact substring match
            if req_norm in cv_n or cv_n in req_norm:
                found = True
                break
            # Semua kata dalam requirement ada di skill CV
            if all(w in cv_n for w in req_words):
                found = True
                break

        if found:
            matched.append(req)
        else:
            gap.append(req)

    score = int(len(matched) / len(required) * 100) if required else 100
    return matched, gap, score


# ─────────────────────────────────────────────────────────────────────────────
# MAIN ANALYZER
# ─────────────────────────────────────────────────────────────────────────────

class ATSAnalyzer:

    # Bobot penilaian
    WEIGHT = {
        'skill_wajib':      40,
        'skill_diinginkan': 15,
        'pendidikan':       20,
        'pengalaman':       25,
    }

    def analyze(self, cv_data: dict, kriteria: Kriteria) -> dict:
        """
        cv_data  : output dari CVParser.parse()
        kriteria : objek Kriteria
        return   : dict hasil analisis lengkap
        """
        cv_skills     = self._flatten_skills(cv_data.get('skill', ''),
                                             cv_data.get('skill_list', []))
        cv_edu        = cv_data.get('pendidikan', '')
        cv_exp        = int(cv_data.get('pengalaman_tahun', 0) or 0)

        # ── SKILL ─────────────────────────────────────────────────────
        wajib_match, wajib_gap, wajib_score = _skill_match_score(
            cv_skills, kriteria.skill_wajib)
        nice_match,  nice_gap,  nice_score  = _skill_match_score(
            cv_skills, kriteria.skill_diinginkan)

        # Skill extra (ada di CV tapi tidak di requirement)
        all_req_norm = set(_normalize(s)
                           for s in kriteria.skill_wajib + kriteria.skill_diinginkan)
        skill_extra = [s for s in cv_skills
                       if _normalize(s) not in all_req_norm and len(s) >= 3]

        # ── PENDIDIKAN ────────────────────────────────────────────────
        edu_score = 0
        edu_note  = ''
        if not kriteria.pendidikan_min:
            edu_score = 100
            edu_note  = 'Tidak ada persyaratan pendidikan'
        else:
            cv_rank  = edu_rank(cv_edu)
            req_rank = edu_rank(kriteria.pendidikan_min)
            if cv_rank >= req_rank:
                edu_score = 100
                edu_note  = (f'✓ {cv_edu} memenuhi minimum {kriteria.pendidikan_min}'
                             if cv_edu else f'Memenuhi minimum {kriteria.pendidikan_min}')
            elif cv_rank == req_rank - 1:
                edu_score = 60
                edu_note  = f'⚠ {cv_edu or "?"} — satu level di bawah {kriteria.pendidikan_min}'
            else:
                edu_score = 0
                edu_note  = f'✗ {cv_edu or "?"} tidak memenuhi minimum {kriteria.pendidikan_min}'

        # ── PENGALAMAN ────────────────────────────────────────────────
        exp_score = 0
        exp_note  = ''
        if kriteria.pengalaman_min <= 0:
            exp_score = 100
            exp_note  = 'Tidak ada persyaratan pengalaman minimum'
        else:
            ratio = cv_exp / kriteria.pengalaman_min
            if ratio >= 1.0:
                exp_score = 100
                exp_note  = f'✓ {cv_exp} tahun ≥ minimum {kriteria.pengalaman_min} tahun'
            elif ratio >= 0.7:
                exp_score = 70
                exp_note  = f'⚠ {cv_exp} tahun — sedikit kurang dari {kriteria.pengalaman_min} tahun'
            elif ratio >= 0.5:
                exp_score = 40
                exp_note  = f'✗ {cv_exp} tahun — kurang dari {kriteria.pengalaman_min} tahun'
            else:
                exp_score = 0
                exp_note  = f'✗ {cv_exp} tahun — jauh di bawah {kriteria.pengalaman_min} tahun'

        # ── TOTAL SCORE ───────────────────────────────────────────────
        # FIX: pakai bobot dari kriteria (Job Library) jika ada,
        #      fallback ke WEIGHT default jika tidak
        bobot = getattr(kriteria, 'bobot', None) or self.WEIGHT
        w_sw  = bobot.get('skill_wajib',      self.WEIGHT['skill_wajib'])
        w_sd  = bobot.get('skill_diinginkan', self.WEIGHT['skill_diinginkan'])
        w_edu = bobot.get('pendidikan',        self.WEIGHT['pendidikan'])
        w_exp = bobot.get('pengalaman',        self.WEIGHT['pengalaman'])

        total = (
            wajib_score * w_sw  / 100 +
            nice_score  * w_sd  / 100 +
            edu_score   * w_edu / 100 +
            exp_score   * w_exp / 100
        )
        score = round(total)

        # ── GRADE & REKOMENDASI ───────────────────────────────────────
        if score >= 80:
            grade, rekomen, color = 'A', 'Lanjutkan', 'success'
        elif score >= 60:
            grade, rekomen, color = 'B', 'Pertimbangkan', 'warning'
        elif score >= 40:
            grade, rekomen, color = 'C', 'Pertimbangkan', 'warning'
        else:
            grade, rekomen, color = 'D', 'Tolak', 'danger'

        # ── KELEBIHAN & KEKURANGAN ────────────────────────────────────
        kelebihan  = self._build_kelebihan(
            cv_exp, kriteria, wajib_match, nice_match,
            skill_extra, cv_edu, edu_score, exp_score)
        kekurangan = self._build_kekurangan(
            wajib_gap, nice_gap, edu_note, exp_score, exp_note,
            cv_edu, kriteria)

        # ── CATATAN ATS (teks untuk disimpan ke field catatan) ────────
        catatan = self._build_catatan(
            score, grade, rekomen, kriteria,
            wajib_match, wajib_gap, nice_match, nice_gap,
            skill_extra, edu_note, exp_note, kelebihan, kekurangan,
            cv_data)

        return {
            'score':           score,
            'grade':           grade,
            'rekomendasi':     rekomen,
            'rekomen_color':   color,
            'skill_match':     wajib_match + nice_match,
            'skill_wajib_match': wajib_match,
            'skill_wajib_gap':   wajib_gap,
            'skill_nice_match':  nice_match,
            'skill_nice_gap':    nice_gap,
            'skill_extra':     skill_extra[:15],
            'kelebihan':       kelebihan,
            'kekurangan':      kekurangan,
            'detail_score': {
                'skill_wajib':     {'score': wajib_score, 'bobot': self.WEIGHT['skill_wajib']},
                'skill_diinginkan':{'score': nice_score,  'bobot': self.WEIGHT['skill_diinginkan']},
                'pendidikan':      {'score': edu_score,   'bobot': self.WEIGHT['pendidikan'],  'note': edu_note},
                'pengalaman':      {'score': exp_score,   'bobot': self.WEIGHT['pengalaman'],  'note': exp_note},
            },
            'catatan_ats': catatan,
            'kriteria':    kriteria,
        }

    # ── HELPERS ───────────────────────────────────────────────────────────────

    def _flatten_skills(self, skill_str: str, skill_list: list) -> list:
        combined = list(skill_list)
        if skill_str:
            for s in re.split(r'[,;\n]', skill_str):
                s = s.strip()
                if s and s not in combined:
                    combined.append(s)
        return combined

    def _build_kelebihan(self, cv_exp, kriteria, wajib_match,
                         nice_match, skill_extra, cv_edu, edu_score, exp_score):
        items = []
        if exp_score == 100 and kriteria.pengalaman_min > 0:
            items.append(f'Pengalaman {cv_exp} tahun memenuhi persyaratan')
        elif cv_exp > kriteria.pengalaman_min and kriteria.pengalaman_min > 0:
            items.append(f'Pengalaman {cv_exp} tahun melebihi persyaratan {kriteria.pengalaman_min} tahun')
        if edu_score == 100 and kriteria.pendidikan_min:
            items.append(f'Pendidikan {cv_edu} memenuhi/melampaui syarat {kriteria.pendidikan_min}')
        if wajib_match:
            items.append(f'Menguasai {len(wajib_match)} dari {len(wajib_match) + len(kriteria.skill_wajib) - len(wajib_match)} skill wajib: {", ".join(wajib_match[:4])}{"..." if len(wajib_match) > 4 else ""}')
        if nice_match:
            items.append(f'Memiliki skill tambahan yang diinginkan: {", ".join(nice_match[:3])}')
        if skill_extra:
            items.append(f'Memiliki {len(skill_extra)} skill tambahan di luar persyaratan')
        if not items:
            items.append('Tidak ada kelebihan signifikan yang teridentifikasi')
        return items

    def _build_kekurangan(self, wajib_gap, nice_gap, edu_note,
                          exp_score, exp_note, cv_edu, kriteria):
        items = []
        if wajib_gap:
            items.append(f'Skill wajib yang kurang: {", ".join(wajib_gap[:5])}{"..." if len(wajib_gap) > 5 else ""}')
        if exp_score < 70 and kriteria.pengalaman_min > 0:
            items.append(exp_note)
        if kriteria.pendidikan_min and edu_rank(cv_edu) < edu_rank(kriteria.pendidikan_min):
            items.append(edu_note)
        if nice_gap:
            items.append(f'Skill yang diinginkan namun tidak dimiliki: {", ".join(nice_gap[:3])}')
        if not items:
            items.append('Tidak ada kekurangan signifikan yang teridentifikasi')
        return items

    def _build_catatan(self, score, grade, rekomen, kriteria,
                       wajib_match, wajib_gap, nice_match, nice_gap,
                       skill_extra, edu_note, exp_note,
                       kelebihan, kekurangan, cv_data):
        from datetime import date
        lines = [
            f"═══════════════════════════════════════",
            f"HASIL ANALISIS ATS — {date.today().strftime('%d/%m/%Y')}",
            f"═══════════════════════════════════════",
            f"Posisi     : {kriteria.jabatan}",
            f"Skor ATS   : {score}/100  (Grade {grade})",
            f"Rekomendasi: {rekomen}",
            f"",
            f"── SKILL WAJIB ──",
        ]
        if wajib_match:
            lines.append(f"✓ Dimiliki : {', '.join(wajib_match)}")
        if wajib_gap:
            lines.append(f"✗ Kurang   : {', '.join(wajib_gap)}")
        if not kriteria.skill_wajib:
            lines.append("(tidak ada persyaratan skill wajib)")

        lines += ["", "── SKILL TAMBAHAN ──"]
        if nice_match:
            lines.append(f"✓ Dimiliki : {', '.join(nice_match)}")
        if nice_gap:
            lines.append(f"✗ Kurang   : {', '.join(nice_gap)}")
        if skill_extra:
            lines.append(f"+ Bonus    : {', '.join(skill_extra[:8])}")
        if not kriteria.skill_diinginkan:
            lines.append("(tidak ada persyaratan skill tambahan)")

        lines += ["", "── PENDIDIKAN & PENGALAMAN ──",
                  edu_note, exp_note,
                  "", "── KELEBIHAN ──"]
        for k in kelebihan:
            lines.append(f"+ {k}")

        lines += ["", "── KEKURANGAN / GAP ──"]
        for k in kekurangan:
            lines.append(f"- {k}")

        lines.append("═══════════════════════════════════════")
        return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────────────
# TAMBAHAN: from_position (dari Job Library)
# ─────────────────────────────────────────────────────────────────────────────

def kriteria_from_position(position) -> 'Kriteria':
    """
    Buat Kriteria dari objek Position Django (Job Library).
    Gunakan ini di views saat mode = 'library'.
    """
    k = Kriteria()
    k.jabatan          = position.nama
    k.pendidikan_min   = position.pendidikan_min or ''
    k.pengalaman_min   = position.pengalaman_min or 0
    k.skill_wajib      = position.skill_wajib_list
    k.skill_diinginkan = position.skill_diinginkan_list
    k.bobot = {
        'skill_wajib':      position.bobot_skill_wajib,
        'pengalaman':       position.bobot_pengalaman,
        'pendidikan':       position.bobot_pendidikan,
        'skill_diinginkan': position.bobot_skill_tambahan,
    }
    return k

# Patch Kriteria class — tambah classmethod
Kriteria.from_position = staticmethod(kriteria_from_position)