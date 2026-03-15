"""
utils/approval_engine.py
========================
Engine terpusat untuk approval workflow HRIS SmartDesk.

Cara pakai:
    from utils.approval_engine import ApprovalEngine, get_approval_chain_display

    engine = ApprovalEngine(company, modul='leave', jabatan_pemohon=employee.jabatan)
    chain  = engine.get_chain()                        # list[ApprovalStep]
    approver = engine.get_first_approver_employee()    # Employee | None
    engine.approve(obj, user, catatan='ok')
    engine.reject(obj, user, catatan='kurang data')
    engine.can_approve(user)                           # bool

Modul valid:
    leave | overtime | payroll | performance | movement |
    recruitment | contract | sp | phk
"""
import logging
from dataclasses import dataclass, field
from typing import List, Optional

logger = logging.getLogger(__name__)

# ─── Status mapping per modul ────────────────────────────────────────────────
MODULE_STATUS = {
    'leave': {
        'approved': 'Approved',
        'rejected': 'Rejected',
        'pending':  'Pending',
    },
    'overtime': {
        'approved': 'Approved',
        'rejected': 'Rejected',
        'pending':  'Pending',
    },
    'performance': {
        'approved': 'approved',
        'rejected': 'rejected',
        'pending':  'submit',
    },
    # Generic fallback untuk modul lain
    '_default': {
        'approved': 'Approved',
        'rejected': 'Rejected',
        'pending':  'Pending',
    },
}


# ─── ApprovalStep dataclass ───────────────────────────────────────────────────
@dataclass
class ApprovalStep:
    level: int
    jabatan_nama: str
    jabatan_id: Optional[int]
    approver_employee: Optional[object]   # Employee | None
    auto_approve_hari: int = 0
    is_resolved: bool = field(default=False)  # True jika ada employee yg menjabat


# ─── Helper: resolve jabatan approver → Employee ─────────────────────────────
def resolve_approver(company, jabatan) -> Optional[object]:
    """
    Temukan Employee aktif pertama yang memegang jabatan tersebut
    di perusahaan yang sama.
    Returns Employee | None.
    """
    if jabatan is None or company is None:
        return None
    try:
        from apps.employees.models import Employee
        return Employee.objects.filter(
            company=company,
            jabatan=jabatan,
            status='Aktif',
        ).select_related('jabatan').first()
    except Exception:
        return None


# ─── get_approval_chain_display ───────────────────────────────────────────────
def get_approval_chain_display(employee, modul: str) -> List[dict]:
    """
    Kembalikan list dict untuk ditampilkan di template.
    Setiap item: {level, jabatan, approver_nama, is_resolved, auto_approve_hari}

    Parameter employee dapat berupa Employee model atau object duck-typed
    dengan attribute .company dan .jabatan.
    """
    if employee is None:
        return []

    jabatan = getattr(employee, 'jabatan', None)
    company = getattr(employee, 'company', None)

    if jabatan is None or company is None:
        return []

    try:
        chain_raw = jabatan.get_full_approval_chain(modul)
    except Exception:
        return []

    result = []
    for item in chain_raw:
        jabatan_approver = item.get('jabatan')
        approver_emp = resolve_approver(company, jabatan_approver)
        result.append({
            'level':             item.get('level', 0),
            'jabatan':           jabatan_approver.nama if jabatan_approver else '—',
            'jabatan_id':        jabatan_approver.pk   if jabatan_approver else None,
            'approver_nama':     approver_emp.nama     if approver_emp     else '(Belum ada pejabat)',
            'is_resolved':       approver_emp is not None,
            'auto_approve_hari': item.get('auto_approve_hari', 0),
        })
    return result


# ─── ApprovalEngine ───────────────────────────────────────────────────────────
class ApprovalEngine:
    """
    Engine approval terpusat.

    Args:
        company:          Company instance
        modul:            string modul (leave, overtime, performance, dst.)
        jabatan_pemohon:  Position instance milik pemohon (boleh None)
    """

    def __init__(self, company, modul: str, jabatan_pemohon=None):
        self.company          = company
        self.modul            = modul
        self.jabatan_pemohon  = jabatan_pemohon
        self._status_map      = MODULE_STATUS.get(modul, MODULE_STATUS['_default'])

    # ── Ambil chain approval ──────────────────────────────────────────────────
    def get_chain(self) -> List[ApprovalStep]:
        """Kembalikan list[ApprovalStep] urut level 1, 2, dst."""
        if self.jabatan_pemohon is None:
            return []
        try:
            chain_raw = self.jabatan_pemohon.get_full_approval_chain(self.modul)
        except Exception:
            return []

        steps = []
        for item in chain_raw:
            jabatan_approver = item.get('jabatan')
            approver_emp = resolve_approver(self.company, jabatan_approver)
            steps.append(ApprovalStep(
                level             = item.get('level', 0),
                jabatan_nama      = jabatan_approver.nama if jabatan_approver else '—',
                jabatan_id        = jabatan_approver.pk   if jabatan_approver else None,
                approver_employee = approver_emp,
                auto_approve_hari = item.get('auto_approve_hari', 0),
                is_resolved       = approver_emp is not None,
            ))
        return steps

    # ── Ambil approver pertama ────────────────────────────────────────────────
    def get_first_approver_employee(self) -> Optional[object]:
        """Kembalikan Employee approver level-1, atau None jika tidak ada."""
        chain = self.get_chain()
        for step in chain:
            if step.is_resolved:
                return step.approver_employee
        return None

    # ── Cek apakah user bisa approve ─────────────────────────────────────────
    def can_approve(self, user) -> bool:
        """
        True jika user adalah:
        - Developer / superuser
        - HR (role administrator / hr_manager / hr_staff / admin)
        - Employee yang jabatannya ada dalam chain approver modul ini
        """
        if user is None:
            return False

        # Developer selalu bisa
        if getattr(user, 'is_superuser', False):
            return True

        # HR selalu bisa
        if getattr(user, 'is_hr', False):
            return True

        # Cek apakah jabatan user ada di chain
        user_jabatan = getattr(user, 'jabatan', None)
        if user_jabatan is None:
            return False

        chain = self.get_chain()
        for step in chain:
            if step.jabatan_id and user_jabatan.pk == step.jabatan_id:
                return True

        return False

    # ── Approve ───────────────────────────────────────────────────────────────
    def approve(self, obj, user, catatan: str = '') -> None:
        """
        Set status obj ke approved, simpan catatan & approver.
        Bekerja untuk Leave, PenilaianKaryawan, atau model apapun
        yang punya field status (dan opsional: approved_by, approved_at, catatan_approval / catatan_atasan).
        """
        from django.utils import timezone

        status_val = self._status_map['approved']

        try:
            obj.status = status_val

            # Leave fields
            if hasattr(obj, 'approved_by') and hasattr(obj, 'approved_at'):
                # approved_by pada Leave FK ke Employee, bukan User
                # Coba resolve Employee dari user
                try:
                    from apps.employees.models import Employee
                    emp = Employee.objects.filter(
                        company=self.company,
                        user=user,
                    ).first()
                    obj.approved_by = emp
                except Exception:
                    pass
                obj.approved_at = timezone.now()

            if hasattr(obj, 'catatan_approval'):
                obj.catatan_approval = catatan
            elif hasattr(obj, 'catatan_atasan'):
                obj.catatan_atasan = catatan

            obj.save()
            self._log(obj, user, 'APPROVE', catatan or f'{self.modul} disetujui')
        except Exception as e:
            logger.error(f'ApprovalEngine.approve error: {e}', exc_info=True)
            raise

    # ── Reject ────────────────────────────────────────────────────────────────
    def reject(self, obj, user, catatan: str = '') -> None:
        """Set status obj ke rejected dan simpan catatan."""
        status_val = self._status_map['rejected']

        try:
            obj.status = status_val

            if hasattr(obj, 'catatan_approval'):
                obj.catatan_approval = catatan
            elif hasattr(obj, 'catatan_atasan'):
                obj.catatan_atasan = catatan

            obj.save()
            self._log(obj, user, 'REJECT', catatan or f'{self.modul} ditolak')
        except Exception as e:
            logger.error(f'ApprovalEngine.reject error: {e}', exc_info=True)
            raise

    # ── Internal: log ke AuditLog ─────────────────────────────────────────────
    def _log(self, obj, user, action: str, detail: str = '') -> None:
        """Catat aksi approval ke AuditLog. Silent fail agar tidak ganggu flow."""
        try:
            from apps.core.models import AuditLog
            AuditLog.objects.create(
                company    = self.company,
                user       = user if hasattr(user, 'pk') else None,
                action     = f'APPROVAL_{action}',
                model_name = obj.__class__.__name__,
                object_id  = getattr(obj, 'pk', None),
                detail     = f'[{self.modul.upper()}] {detail}',
            )
        except Exception as e:
            logger.warning(f'ApprovalEngine._log failed (non-critical): {e}')

    # ── Internal: kirim notifikasi email ─────────────────────────────────────
    def _send_notification(self, obj, user, action: str = 'submitted') -> None:
        """
        Kirim notifikasi email. Silent fail — jangan crash flow utama.
        Saat ini hanya support Leave. Modul lain bisa ditambah.
        """
        try:
            if self.modul == 'leave':
                from utils.email_sender import send_leave_notification
                send_leave_notification(obj, action=action)
            else:
                # Generic fallback — kirim simple email ke approver pertama
                approver = self.get_first_approver_employee()
                if approver and getattr(approver, 'email', None):
                    from utils.email_sender import send_simple_email
                    model_name = obj.__class__.__name__
                    send_simple_email(
                        subject        = f'[HRIS] Pengajuan {self.modul.upper()} baru',
                        body           = f'Ada pengajuan {self.modul} baru yang membutuhkan persetujuan Anda.',
                        recipient_list = [approver.email],
                    )
        except Exception as e:
            logger.warning(f'ApprovalEngine._send_notification failed (non-critical): {e}')
