# Ruang Dongeng

Web dongeng anak dengan scene Three.js, model buku GLB yang dibuat Python, narator neural Bahasa Indonesia, gambar sampul, ilustrasi, musik, dan efek suara.

## Menjalankan di Windows

1. Pasang Python 3.10 atau lebih baru.
2. Jalankan `run.bat`.
3. Buka `http://127.0.0.1:8000`.

Script akan membuat virtual environment, memasang paket dari `requirements.txt`, lalu menjalankan web server lokal. Koneksi internet dibutuhkan untuk pemasangan paket, model Three.js dari CDN, dan suara neural.

## Layanan

- `POST /api/model` membuat buku GLB bertekstur dari judul dan sampul yang dikirim editor. Scene Three.js memuat model hasil Python dengan GLTFLoader.
- `POST /api/tts` merender teks menjadi MP3 memakai suara neural Indonesia `id-ID-GadisNeural` atau `id-ID-ArdiNeural`.
- `GET /api/docs` membuka dokumentasi API lokal.

Jika model gagal dibuat, periksa terminal tempat server berjalan untuk stack trace. Endpoint juga akan menampilkan tipe dan pesan exception agar masalah seperti dependensi GLB atau data gambar mudah dikenali.

Cerita, gambar, serta berkas musik/efek tetap disimpan di browser perangkat pembaca. Batasi unggahan audio kecil agar kuota penyimpanan browser tidak penuh. Untuk login tersinkron atau menyimpan cerita lintas perangkat, repo ini masih memerlukan database dan autentikasi server.

Narator memakai `edge-tts`, yang mengakses layanan suara online Edge dari Python. Gunakan sesuai syarat layanan penyedia. Suara neural lebih alami daripada speech synthesis bawaan browser, tetapi koneksi internet dibutuhkan setiap kali narasi baru dibuat.
