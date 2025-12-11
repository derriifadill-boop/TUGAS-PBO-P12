import logging
from abc import ABC, abstractmethod
from typing import List, Dict, Any

# Konfigurasi logging dasar
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s'
)
LOGGER = logging.getLogger(__name__)


# Abstraksi: kontrak untuk semua aturan validasi
class IValidationRule(ABC):
    """Antarmuka untuk aturan validasi pendaftaran.

    Setiap aturan harus mengimplementasikan method `validate`.
    """

    @abstractmethod
    def validate(self,  Dict[str, Any]) -> tuple[bool, str]:
        """Memvalidasi data mahasiswa berdasarkan aturan spesifik.

        Args:
            data: Data mahasiswa berupa dictionary dengan struktur:
                {
                    "name": str,
                    "completed_courses": List[{"code": str}],
                    "courses": List[{"code": str, "sks": int, ...}]
                }

        Returns:
            tuple[bool, str]: 
                - bool: True jika valid, False jika gagal
                - str: Pesan deskriptif hasil validasi
        """
        pass


# Implementasi aturan: Validasi batas SKS
class SksLimitRule(IValidationRule):
    """Aturan validasi untuk membatasi total SKS yang diambil mahasiswa."""

    def __init__(self, max_sks: int = 24):
        """Inisialisasi aturan batas SKS.

        Args:
            max_sks: Batas maksimal SKS yang diperbolehkan. Default: 24.
        """
        self.max_sks = max_sks

    def validate(self,  Dict[str, Any]) -> tuple[bool, str]:
        """Memeriksa apakah total SKS melebihi batas.

        Args:
            data: Data mahasiswa (lihat docstring IValidationRule).

        Returns:
            tuple[bool, str]: Hasil validasi dan pesan.
        """
        courses = data.get("courses", [])
        total_sks = sum(course.get("sks", 0) for course in courses)
        if total_sks > self.max_sks:
            return False, f"Total SKS ({total_sks}) melebihi batas maksimal ({self.max_sks})"
        return True, "SKS valid"


# Implementasi aturan: Validasi prasyarat
class PrerequisiteRule(IValidationRule):
    """Aturan validasi untuk memastikan prasyarat mata kuliah terpenuhi."""

    def validate(self,  Dict[str, Any]) -> tuple[bool, str]:
        """Memeriksa kelengkapan prasyarat untuk setiap mata kuliah yang diambil.

        Args:
            data: Data mahasiswa (lihat docstring IValidationRule).

        Returns:
            tuple[bool, str]: Hasil validasi dan pesan.
        """
        completed_courses = {c["code"] for c in data.get("completed_courses", [])}
        for course in data.get("courses", []):
            prereq = course.get("prerequisite")
            if prereq and prereq not in completed_courses:
                return False, f"Prasyarat tidak terpenuhi: {prereq} belum diambil untuk {course['code']}"
        return True, "Prasyarat terpenuhi"


# Implementasi aturan tambahan (untuk challenge OCP)
class JadwalBentrokRule(IValidationRule):
    """Aturan validasi untuk mendeteksi bentrok jadwal mata kuliah."""

    def validate(self,  Dict[str, Any]) -> tuple[bool, str]:
        """Memeriksa tumpang tindih jadwal antar mata kuliah.

        Format jadwal diharapkan: "Hari JamMulai-JamSelesai", contoh: "Senin 08:00-10:00".

        Args:
            data: Data mahasiswa (lihat docstring IValidationRule).

        Returns:
            tuple[bool, str]: Hasil validasi dan pesan.
        """
        schedules = []
        for course in data.get("courses", []):
            sched = course.get("schedule")
            if sched and " " in sched and "-" in sched:
                parts = sched.split(" ", 1)
                day = parts[0]
                time_part = parts[1]
                if "-" in time_part:
                    start, end = time_part.split("-", 1)
                    schedules.append((day, start.strip(), end.strip(), course["code"]))
        
        for i in range(len(schedules)):
            day1, start1, end1, code1 = schedules[i]
            for j in range(i + 1, len(schedules)):
                day2, start2, end2, code2 = schedules[j]
                if day1 == day2:
                    try:
                        s1 = int(start1[:2]) * 60 + int(start1[3:5])
                        e1 = int(end1[:2]) * 60 + int(end1[3:5])
                        s2 = int(start2[:2]) * 60 + int(start2[3:5])
                        e2 = int(end2[:2]) * 60 + int(end2[3:5])
                        if s1 < e2 and s2 < e1:
                            return False, f"Jadwal bentrok antara {code1} dan {code2} pada {day1}"
                    except (ValueError, IndexError):
                        continue
        return True, "Tidak ada bentrok jadwal"


# Kelas koordinator: menerapkan SRP dan DIP
class RegistrationService:
    """Kelas koordinator untuk menjalankan validasi pendaftaran mahasiswa.

    Menerapkan prinsip:
    - SRP: Hanya bertanggung jawab mengkoordinasikan validasi.
    - DIP: Bergantung pada abstraksi (IValidationRule), bukan implementasi.
    """

    def __init__(self, rules: List[IValidationRule]):
        """Inisialisasi dengan daftar aturan validasi.

        Args:
            rules: Daftar objek yang mengimplementasikan IValidationRule.
        """
        self.rules = rules

    def validate_registration(self, student_ Dict[str, Any]) -> bool:
        """Menjalankan semua aturan validasi secara berurutan.

        Validasi berhenti saat pertama kali gagal.

        Args:
            student_data: Data mahasiswa (lihat docstring IValidationRule).

        Returns:
            bool: True jika semua aturan lolos, False jika ada yang gagal.
        """
        for rule in self.rules:
            is_valid, message = rule.validate(student_data)
            if not is_valid:
                LOGGER.warning(f"Validasi gagal: {message}")
                return False
        LOGGER.info("Registrasi berhasil: semua aturan terpenuhi.")
        return True


# Program utama — demo
if __name__ == "__main__":
    mahasiswa = {
        "name": "Budi",
        "completed_courses": [
            {"code": "MK101"},
            {"code": "MK102"}
        ],
        "courses": [
            {"code": "MK201", "sks": 3, "prerequisite": "MK101", "schedule": "Senin 08:00-10:00"},
            {"code": "MK202", "sks": 3, "prerequisite": "MK102", "schedule": "Senin 09:30-11:30"},
            {"code": "MK203", "sks": 2}
        ]
    }

    print("=== Skenario 1: Validasi Dasar (SKS + Prasyarat) ===")
    rules_dasar = [SksLimitRule(max_sks=20), PrerequisiteRule()]
    service1 = RegistrationService(rules_dasar)
    service1.validate_registration(mahasiswa)

    print("\n=== Skenario 2: Validasi Lengkap (Termasuk Jadwal Bentrok) ===")
    rules_lengkap = [SksLimitRule(max_sks=20), PrerequisiteRule(), JadwalBentrokRule()]
    service2 = RegistrationService(rules_lengkap)
    service2.validate_registration(mahasiswa)