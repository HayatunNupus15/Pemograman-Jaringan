import socket
import json
import threading
import time
import psutil
import signal
import sys

# Inisialisasi server socket
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_address = ('localhost', 12345)
server_socket.bind(server_address)
server_socket.listen(1)

# Fungsi yang akan dijalankan dalam thread untuk memantau jaringan
# Fungsi yang akan dijalankan dalam thread untuk memantau jaringan
def monitor_network(connection):
    last_received = psutil.net_io_counters().bytes_recv
    last_sent = psutil.net_io_counters().bytes_sent
    last_time = time.time()
    
    while True:
        # Ambil informasi pemantauan jaringan dari psutil
        received_bytes = psutil.net_io_counters().bytes_recv
        sent_bytes = psutil.net_io_counters().bytes_sent
        connections = len(psutil.net_connections())

        # Menghitung perubahan dalam jumlah penerimaan dan pengiriman setiap detik
        received_per_sec = received_bytes - last_received
        sent_per_sec = sent_bytes - last_sent
        elapsed_time = time.time() - last_time

        # Mengupdate nilai terakhir untuk perhitungan selanjutnya
        last_received = received_bytes
        last_sent = sent_bytes
        last_time = time.time()

        # Konversi ukuran data ke format yang lebih mudah dibaca
        received = convert_size(received_bytes)
        sent = convert_size(sent_bytes)
        received_per_sec_str = convert_size(received_per_sec / elapsed_time) + '/s'
        sent_per_sec_str = convert_size(sent_per_sec / elapsed_time) + '/s'

        # Data yang akan dikirim ke client
        data = {
            'received': received,
            'sent': sent,
            'connections': connections,
            'received_per_sec': received_per_sec_str,
            'sent_per_sec': sent_per_sec_str,
        }

        # Kirim informasi pemantauan ke client
        try:
            connection.sendall(json.dumps(data).encode('utf-8'))
        except (socket.error, BrokenPipeError):
            # Tangani exception jika koneksi terputus
            break

        # Tunggu sebentar sebelum pembaruan berikutnya
        time.sleep(1)

# Fungsi untuk menangani koneksi dari client
def handle_client_connection(connection):
    while True:
        # Menunggu menerima data dari server
        try:
            data = connection.recv(1024).decode('utf-8')
            if not data:
                break
            print(f"Received data: {data}")
        except (socket.error, ConnectionResetError):
            # Tangani exception jika koneksi terputus
            break

# Fungsi untuk mengonversi ukuran data ke format yang lebih mudah dibaca
def convert_size(size_bytes):
    for unit in ['bytes', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0

# Fungsi untuk menangani sinyal SIGINT (Ctrl + C)
def signal_handler(sig, frame):
    print('Exiting...')
    # Tutup server socket sebelum keluar
    server_socket.close()
    sys.exit(0)

# Atur penanganan sinyal SIGINT
signal.signal(signal.SIGINT, signal_handler)

# Server akan menerima koneksi dari client dan membuat thread untuk menangani setiap koneksi
while True:
    print('Waiting for a connection...')
    client_connection, client_address = server_socket.accept()
    print('Accepted connection from', client_address)
    
    # Buat thread baru untuk memantau jaringan dan menangani koneksi dari client
    monitor_thread = threading.Thread(target=monitor_network, args=(client_connection,))
    client_thread = threading.Thread(target=handle_client_connection, args=(client_connection,))
    
    # Mulai thread-thread tersebut
    monitor_thread.start()
    client_thread.start()

    # Tunggu sampai kedua thread selesai
    monitor_thread.join()
    client_thread.join()