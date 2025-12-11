import logging

# Konfigurasi dasar logging: Semua log level INFO ke atas akan ditampilkan
# Format: Waktu - Level - Nama Kelas/Fungsi - Pesan
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s'
)

# Tambahkan logger untuk kelas yang akan kita gunakan
LOGGER = logging.getLogger('Checkout')


from abc import ABC, abstractmethod
from dataclasses import dataclass

# Model Sederhana
@dataclass
class Order:
    """Representasi pesanan pelanggan.

    Attributes:
        customer_name (str): Nama pelanggan.
        total_price (float): Total harga pesanan.
        status (str): Status pesanan, default "open".
    """
    customer_name: str
    total_price: float
    status: str = "open"


# === KODE BURUK (SEBELUM REFACTOR) ===
class OrderManager:  # Melanggar SRP, OCP, DIP
    """Kelas yang menangani proses checkout secara monolitik — melanggar SRP, OCP, dan DIP."""

    def process_checkout(self, order: Order, payment_method: str):
        """Memulai proses checkout untuk pesanan tertentu dengan metode pembayaran spesifik.

        Args:
            order (Order): Objek pesanan yang akan diproses.
            payment_method (str): Metode pembayaran ("credit_card", "bank_transfer", dll).

        Returns:
            bool: True jika checkout berhasil, False jika gagal atau metode tidak valid.
        """
        LOGGER.info(f"Memulai checkout untuk {order.customer_name}...")

        # LOGIKA PEMBAYARAN (Pelanggaran OCP/DIP)
        if payment_method == "credit_card":
            # Logika detail implementasi hardcoded di sini
            LOGGER.info("Processing Credit Card...")
        elif payment_method == "bank_transfer":
            # Logika detail implementasi hardcoded di sini
            LOGGER.info("Processing Bank Transfer...")
        else:
            LOGGER.warning("Metode tidak valid.")
            return False

        # LOGIKA NOTIFIKASI (Pelanggaran SRP)
        LOGGER.info(f"Mengirim notifikasi ke {order.customer_name}...")
        order.status = "paid"
        return True


# --- ABSTRAKSI (Kontrak untuk OCP/DIP) ---
class IPaymentProcessor(ABC):
    """Kontrak dasar untuk semua prosesor pembayaran.

    Setiap kelas konkret harus mengimplementasikan method `process`.
    """

    @abstractmethod
    def process(self, order: Order) -> bool:
        """Memproses pembayaran untuk pesanan tertentu.

        Args:
            order (Order): Objek pesanan yang akan diproses.

        Returns:
            bool: True jika pembayaran berhasil, False jika gagal.
        """
        pass


class INotificationService(ABC):
    """Kontrak dasar untuk semua layanan notifikasi.

    Setiap kelas konkret harus mengimplementasikan method `send`.
    """

    @abstractmethod
    def send(self, order: Order):
        """Mengirim notifikasi terkait pesanan.

        Args:
            order (Order): Objek pesanan yang akan dikirimkan notifikasinya.
        """
        pass


# --- IMPLEMENTASI KONKRIT (Plug-in) ---
class CreditCardProcessor(IPaymentProcessor):
    """Implementasi prosesor pembayaran menggunakan kartu kredit."""

    def process(self, order: Order) -> bool:
        """Memproses pembayaran dengan kartu kredit.

        Args:
            order (Order): Objek pesanan yang akan diproses.

        Returns:
            bool: Selalu True untuk simulasi.
        """
        LOGGER.info("Payment: Memporses Kartu Kredit.")
        return True


class EmailNotifier(INotificationService):
    """Implementasi layanan notifikasi melalui email."""

    def send(self, order: Order):
        """Mengirim email konfirmasi ke pelanggan.

        Args:
            order (Order): Objek pesanan yang akan dikirimkan notifikasinya.
        """
        LOGGER.info(f"Notif: Mengirim email konfirmasi ke {order.customer_name}.")


# --- KELAS KOORDINATOR (SRP & DIP) ---
class CheckoutService:
    """Kelas koordinator untuk mengelola proses checkout secara modular.

    Kelas ini memisahkan logika pembayaran dan notifikasi (memenuhi SRP),
    serta bergantung pada abstraksi, bukan implementasi konkret (memenuhi DIP).
    """

    def __init__(self, payment_processor: IPaymentProcessor, notifier: INotificationService):
        """Inisialisasi CheckoutService dengan dependensi yang diperlukan.

        Args:
            payment_processor (IPaymentProcessor): Implementasi interface pembayaran.
            notifier (INotificationService): Implementasi interface notifikasi.
        """
        self.payment_processor = payment_processor
        self.notifier = notifier

    def run_checkout(self, order: Order) -> bool:
        """Menjalankan proses checkout lengkap: pembayaran + notifikasi.

        Args:
            order (Order): Objek pesanan yang akan diproses.

        Returns:
            bool: True jika checkout sukses, False jika pembayaran gagal.
        """
        LOGGER.info(f"Memulai checkout untuk {order.customer_name}. Total: {order.total_price}")

        payment_success = self.payment_processor.process(order)  # Delegasi 1

        if payment_success:
            order.status = "paid"
            self.notifier.send(order)  # Delegasi 2
            LOGGER.info("Checkout Sukses. Status pesanan: PAID.")
            return True
        else:
            LOGGER.error("Pembayaran gagal. Transaksi dibatalkan.")
            return False


# --- PROGRAM UTAMA ---
# Setup Dependencies
andi_order = Order("Andi", 500000)
email_service = EmailNotifier()

# 1. Inject implementasi Credit Card
cc_processor = CreditCardProcessor()
checkout_cc = CheckoutService(payment_processor=cc_processor, notifier=email_service)
print("--- Skenario 1: Credit Card ---")
checkout_cc.run_checkout(andi_order)

# 2. Pembuktian OCP: Menambah Metode Pembayaran QRIS (Tanpa Mengubah CheckoutService)
class QrisProcessor(IPaymentProcessor):
    """Implementasi prosesor pembayaran menggunakan QRIS."""

    def process(self, order: Order) -> bool:
        """Memproses pembayaran dengan QRIS.

        Args:
            order (Order): Objek pesanan yang akan diproses.

        Returns:
            bool: Selalu True untuk simulasi.
        """
        LOGGER.info("Payment: Memproses QRIS.")
        return True

budi_order = Order("Budi", 100000)
qris_processor = QrisProcessor()

# Inject implementasi QRIS yang baru dibuat
checkout_qris = CheckoutService(payment_processor=qris_processor, notifier=email_service)
print("\n--- Skenario 2: Pembuktian OCP (QRIS) ---")
checkout_qris.run_checkout(budi_order)