from flask import Flask, render_template
from flask_socketio import SocketIO, emit
import psutil
import threading
import time
import json
import signal
import sys

app = Flask(__name__)
socketio = SocketIO(app)

network_info = {
    'received': 0,
    'sent': 0,
    'connections': 0,
    'received_per_sec': '0 B/s',
    'sent_per_sec': '0 B/s',
}

def convert_size(size_bytes):
    units = ['B', 'KB', 'MB', 'GB', 'TB']
    for unit in units:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0

def monitor_network():
    last_received = psutil.net_io_counters().bytes_recv
    last_sent = psutil.net_io_counters().bytes_sent
    last_time = time.time()

    while True:
        network_info['received'] = psutil.net_io_counters().bytes_recv
        network_info['sent'] = psutil.net_io_counters().bytes_sent
        network_info['connections'] = len(psutil.net_connections())

        received_bytes = network_info['received']
        sent_bytes = network_info['sent']
        elapsed_time = time.time() - last_time

        # Menghitung perubahan dalam jumlah penerimaan dan pengiriman setiap detik
        received_per_sec = received_bytes - last_received
        sent_per_sec = sent_bytes - last_sent

        # Mengupdate nilai terakhir untuk perhitungan selanjutnya
        last_received = received_bytes
        last_sent = sent_bytes
        last_time = time.time()

        # Konversi ukuran data ke format yang lebih mudah dibaca
        received_per_sec_str = convert_size(received_per_sec / elapsed_time) + '/s'
        sent_per_sec_str = convert_size(sent_per_sec / elapsed_time) + '/s'

        # Memperbarui informasi data per detik
        network_info['received_per_sec'] = received_per_sec_str
        network_info['sent_per_sec'] = sent_per_sec_str

        # Mengupdate informasi pemantauan
        socketio.emit('update_data', network_info)
        time.sleep(1)

monitor_thread = threading.Thread(target=monitor_network)
monitor_thread.start()

# Fungsi untuk menangani sinyal SIGINT (Ctrl + C)
def signal_handler(sig, frame):
    print('Exiting...')
    sys.exit(0)

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('connect')
def handle_connect():
    emit('update_data', network_info)

if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal_handler)
    socketio.run(app, debug=True)
