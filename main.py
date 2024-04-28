from typing import Union
from typing import List, Annotated

# FastAPI
from fastapi import FastAPI, Request, HTTPException, Depends, File, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os, asyncio

# import SQLAlchemy from provider
import provider.models
from provider.db import engine, SessionLocal
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy import update

# import function
from function.docxauto import Doc_Auto

# Fonnte Connection
from provider.send_rq import ResponseHandler
tw = ResponseHandler()

# create database column
provider.models.Base.metadata.create_all(bind=engine)

# activate database
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# activate FastAPI
db_dependency = Annotated[Session, Depends(get_db)]
Session = sessionmaker(bind=engine)
word = Doc_Auto(db_con=Session(), model=provider.models)
app = FastAPI()

# Create a directory to store uploaded files
UPLOAD_DIRECTORY = "public"
os.makedirs(UPLOAD_DIRECTORY, exist_ok=True)

# Mount the public directory to serve static files
app.mount("/files", StaticFiles(directory=UPLOAD_DIRECTORY), name="files")

# ==================================================
# FastAPI endpoints
@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.get("/message")
def read_root():
    return {"Hello": "World"}

@app.get("/download/{file_name}")
async def get_pdf(file_name: str, request: Request):
    client_host = request.client.host
    docx_path = f"public/files/{file_name}"

    if not os.path.exists(docx_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(docx_path, media_type="application/docx")

@app.post("/message")
async def message_handler(req: Request, db: db_dependency):
    incoming_payload = await req.json()
    protocol = req.url.scheme
    host = req.headers["host"]

    # sumber
    message_body = incoming_payload.get('pesan','')
    print(message_body)
    nomor_hp = incoming_payload.get('pengirim', '')
    name = incoming_payload.get('name', 'User')

    # response_message = "Received message: " + message_body
    user_activity = db.query(provider.models.user_activity).filter_by(no_hp = nomor_hp).first()

    # cek aktivitas user & greeting
    if user_activity == 'None' or user_activity == None:
        tw.sendMsg(nomor_hp, f"Selamat datang dalam sistem chatbot KOPITU, {name}! Ketik 'mulai' untuk ke menu pilihan.")
        new_user = provider.models.user_activity(no_hp=nomor_hp, activity='menu')
        db.add(new_user)
        db.commit()
    
    if user_activity.no_hp == nomor_hp:
        # membuat form otomatis
        if user_activity.activity == 'menu':
            user_activity.activity = 'decision'
            db.commit()
            tw.sendMsg(nomor_hp, f"*[MENU CHATBOT KOPITU]*\nApa yang dapat kami bantu, {name}?\n1. Informasi Umum KOPITU \n2. Registrasi Member Baru")
            return {"success": True}
        
        if user_activity.activity == 'decision':
            # change activity
            user_activity.activity = f'service_{message_body}'
            db.commit()
            # if else based on choice
            if message_body == "1" or 'informasi' in message_body:
                tw.sendMsg(nomor_hp, f"Apa yang anda ingin anda ketahui pada KOPITU?\n1. Tentang KOPITU\n2. Program KOPITU")                
                return {"success": True}

            if message_body == "2" or 'member' in message_body:
                user_activity.activity = f'service_2#registrasi#nama#{nomor_hp}'
                db.commit()
                tw.sendMsg(nomor_hp, f"[REGISTRASI KEANGGOTAAN KOPITU]\nSelamat datang di registrasi untuk anggota baru KOPITU! Selanjutnya kami akan meminta biodata anda untuk keperluan pendataan.\n\nSiapa nama lengkap Anda?")                
                return {"success": True}
            
            if message_body not in ['1','2', 'informasi', 'member', 'menu']:
                user_activity.activity = 'decision'
                db.commit()
                tw.sendMsg(nomor_hp, f"Maaf pilihan Anda tidak ada.")
                return {"success": True}

        # FAQ
        if user_activity.activity.startswith('service_1'):
            # TENTANG KOPITU
            if message_body == 'a':
                tw.sendMsg(nomor_hp, f"*[INFORMASI TENTANG KOPITU]*\nApa yang ingin Anda ketahui tentang KOPITU?\na. Informasi Umum KOPITU\n2. Sejarah KOPITU\n3. Segitiga Filosofi KOPITU\n4. Informasi Kontak KOPITU")            
                user_activity.activity = 'service_1#faq#kopitu'
                db.commit()
                return {"success": True}
            # TENTANG PROGRAM KOPITU
            elif message_body == 'b':
                tw.sendMsg(nomor_hp, f"*[INFORMASI PROGRAM KOPITU]*\nPilih program Kopitu yang ingin anda ketahui\na. PRAKERJA\nb. Kopitu PRENEUR\nc. Bisnis INCUBATORS\nd. Kopitu TANIPRENEUR\ne. Kopitu SISTERCITY\nf. Kopitu E-STORE\ng. Kopitu SANTRIPRENEUR\nh. Kopitu NELAYANPRENEUR\ni. Kopitu DIFABELPRENEUR\nj. Kopitu METAVERSE\nK. IDNTOWN\nl. IDNTOWN Kampoeng Halal\nm. KOPITU Desa AI")
                user_activity.activity = f'service_1#faq#program'
                db.commit()
                return {"success": True}
            # TENTANG MEMBERSHIP
            elif message_body == 'c':
                tw.sendMsg(nomor_hp, f"*[INFORMASI PENDAFTARAN MEMBER]*\na. Cara mendaftar sebagai member\nb.Tentang member KOPITU")
                user_activity.activity = f'service_1#faq#member'
                db.commit()
                return {"success": True}
            # ERROR MESSAGE
            elif message_body not in ['a', 'b', 'kembali', 'menu']:
                tw.sendMsg(nomor_hp, 'Pilihan ada tidak ada, silakan membalas "kembali" atau pilih "batal" untuk kembali ke menu.')
                return {"success": True}

        if user_activity.activity.startswith('service_1#'):
            act_faq = user_activity.activity.split()
            back = "_(Pilih 'menu' untuk kembali ke menu awal atau 'kembali' untuk melihat informasi lain.)_"
            # TENTANG KOPITU
            if act_faq[2] == 'kopitu':
                # INFORMASI UMUM KOPITU
                if message_body == '1' or 'tentang kopitu' in message_body:
                    user_activity.activity = 'service_1#faq#done'
                    db.commit()
                    tw.sendMsg(nomor_hp, f"*[TENTANG KOPITU]*\nKomite Pengusaha Mikro Kecil Menengah Indonesia Bersatu (KOPITU) dibentuk sebagai wadah di tingkat nasional yang menyatukan pelaku usaha dan pemangku kepentingan lain baik pemerintah maupun non pemerintah lintas sectoral dan multi sectoral untuk bersinergi meningkatkan kemampuan bersaing UMKM Indonesia\n\n{back}")
                    return {"success": True}
                # SEJARAH KOPITU
                if message_body == '2' or 'sejarah' in message_body:
                    user_activity.activity = 'service_1#faq#done'
                    db.commit()
                    tw.sendMsg(nomor_hp, f"*[SEJARAH KOPITU]*\nPeran Usaha Mikro Kecil dan Menengah (UMKM) atau Usaha Kecil Menengah (UKM) dalam pertumbuhan perekonomian suatu negara dinilai penting. UMKM memiliki kontribusi besar dan krusial bagi perekonomian Indonesia. Kriteria UMKM Menurut Undang-undang Nomor 20 Tahun 2008 tentang Usaha Mikro, Kecil dan Menengah (UMKM) usaha kecil didefinisikan sebagai kegiatan ekonomi produktif yang berdiri sendiri.\n\nUsaha ini dilakukan perorangan atau badan usaha yang bukan merupakan anak perusahaan atau bukan cabang perusahaan yang dimiliki, dikuasai atau menjadi bagian baik langsung maupun tidak langsung dari usaha menengah atau usaha besar serta memenuhi kriteria lain. Dalam UU tersebut juga dijelaskan perbedaan kriteria UMKM dengan Usaha Besar.\n\n1. Usaha Mikro: aset maksimal Rp 50 juta (tidak termasuk tanah dan bangunan tempat usaha) dan omzet maksimal Rp 300 juta per tahun.\n2. Usaha Kecil: aset lebih dari Rp 50 juta - Rp 500 juta (tidak termasuk tanah dan bangunan tempat usaha) dan omzet maksimal lebih dari Rp 300 juta - Rp 2,5 miliar per tahun.\n3. Usaha Menengah: aset lebih dari Rp 500 juta - Rp 10 miliar (tidak termasuk tanah dan bangunan tempat usaha) dan omzet lebih dari Rp 2,5 miliar - Rp 50 miliar per tahun.\n4. Usaha Besar: aset lebih dari Rp 10 miliar (tidak termasuk tanah dan bangunan tempat usaha) dan omzet lebih dari Rp 50 miliar per tahun.\n\nUMKM merupakan pilar terpenting dalam perekonomian Indonesia. Berdasarkan data Kementerian Koperasi dan UKM, jumlah UMKM saat ini mencapai 64,2 juta dengan kontribusi terhadap PDB sebesar 61,07% atau senilai 8.573,89 triliun rupiah. Kontribusi UMKM terhadap perekonomian Indonesia meliputi kemampuan menyerap 97% dari total tenaga kerja yang ada serta dapat menghimpun sampai 60,4% dari total investasi. Namun, tingginya jumlah UMKM di Indonesia juga tidak terlepas dari tantangan yang ada.\n\nSalah satu tantangan yang ada saat ini yaitu Pandemi COVID-19. Dampak dari pandemi ini salah satu contohnya adalah mendorong shifting pola konsumsi barang dan jasa dari offline ke online, dengan adanya kenaikan trafik internet berkisar 15-20%. Hal ini menjadi momentum untuk mengakselerasi transformasi digital. Potensi digital ekonomi Indonesia juga masih terbuka lebar dengan jumlah populasi terbesar ke-4 di dunia dan penetrasi internet yang telah menjangkau 196,7 juta orang.\n\nDi samping itu, perubahan iklim bisnis secara luas dapat mempengaruhi produktivitas dan aktivitas UMKM. Oleh karena itu, diperlukan tidak hanya koordinasi dan aggregasi satu arah atau mono sectoral untuk mempertahankan eksistensi dan menumbuh kembangkan UMKM di Indonesia.\n\n{back}")
                # FILOSOFI KOPITU
                if message_body == '3' or 'filosofi' in message_body:
                    user_activity.activity = 'service_1#faq#done'
                    db.commit()
                    tw.sendMsg(nomor_hp, f"*[FILOSOFI SEGITIGA KOPITU]*\nSegitiga Sama Sisi, Sebagai integritas yang saling mendukung, menopang dan melengkapi.\nKOPITU disisi Bawah Segitiga, Sebagai pondasi naungan untuk para UMKM yang bersifat nirlaba, independen dan tidak beraliansi dengan partai.\nKoperasi UKM Sukses Bersama dan PT UKM Sukses Bersama disebelah kanan dan kiri segitiga, Merupakan Wujud hasil dari kemitraan dengan mitra strategis yang di implementasikan melalui Koperasi dan PT yang sudah bermitra dengan KOPITU.\nKetiganya Membentuk Segitiga Sama Sisi, Menaungi program kerja KOPITU yang akan terus berkembang seiring berjalannya waktu.\n\n{back}")
                # KONTAK KOPITU
                if message_body == '4' or 'kontak' in message_body:
                    user_activity.activity = 'service_1#faq#done'
                    db.commit()
                    tw.sendMsg(nomor_hp, f"*[INFORMASI KONTAK KOPITU]*\n\U0001F4DE +62 851 - 7326 - 5221\n\U0001F4E7 info@kopitu.co.id\n\U0001F4E7 kopitumedia@gmail.com\n\U0001F4CD Soho Podomoro City (Soho Residence) Unit 3829, Lt. 38, Tanjung Duren Selatan, Jakarta, Indonesia 11470\nWaktu Operasional Kami : Senin - Sabtu (08.00 - 17.00)\n\n{back}")
                    return {"success": True}
                # NOT AVAILABLE
                if message_body not in ['1','2','3','4','menu','kembali','batal','tentang kopitu','sejarah','filosofi','kontak']:
                    tw.sendMsg(nomor_hp, f"Pilihan Anda tidak ada. Silakan kirim kembali berdasarkan opsi yang ada.")  
                    return {"success": True}

            # TENTANG PROGRAM KOPITU
            elif act_faq[2] == 'program':
                # PRAKERJA
                if message_body == '1':
                    tw.sendMsg(nomor_hp, f"*[PRAKERJA]*\n\nProgram Kartu Prakerja adalah program pengembangan kompetensi kerja dan kewirausahaan yang ditujukan untuk pencari kerja, pekerja/buruh yang terkena pemutusan hubungan kerja, dan/atau pekerja/buruh yang membutuhkan peningkatan kompetensi, termasuk pelaku usaha mikro dan kecil.\n\nInformasi lebih lanjut: https://www.prakerja.go.id/tentang-prakerja\n\n{back}")
                    user_activity.activity = 'service_1#faq#done'
                    db.commit()
                # Kopitu PRENEUR
                if message_body == '2':
                    tw.sendMsg(nomor_hp, f"*[KOPITU PRENEUR]*\nKOPITUPRENEUR dibentuk langsung dibawah DPP KOPITU yang bergerak di daerah sebagai agen Hulu dan Hilir penggerak bisnis bagi para UMKM, Petani, Nelayan, Peternak, dan IKM melalui pelatihan-pelatihan dan sosialisasi antara Pelaku Usaha dengan menyediakan pelayanan dalam bidang jasa perizinan dan konsultasi bisnis bagi UMKM yang berfungsi dalam meningkatkan UMKM sesuai dengan VIsi dan Misi KOPITU yaitu bisa mandiri, naik kelas, dan Go Global (ekspor) sesuai dengan slogan “UKM Juara di negeri Sendiri dan Mendunia” serta menyadarkan pentingnya perlundungan keselamatan kerja meskipun di tingkat UKM lewat program New Perisai BPJamsostek\n\nDengan adanya KOPITUPRENEUR, UKM Indonesia kususnya anggota KOPITU dapat lebih mudah dalam menjalankan bisnisnya, dari mulai perizinan, inovasi bisnis hingga pemasaran dalam dan luar negeri dapat diakses dalam satu pintu.\n\nInformasi lebih lanjut: https://kopitupreneur.com/\n\n{back}")
                    user_activity.activity = 'service_1#faq#done'
                    db.commit()
                # Bisnis INCUBATORS
                if message_body == '3':
                    tw.sendMsg(nomor_hp, f"*[Bisnis INCUBATORS]*\nInformasi sedang dalam proses.\n\n{back}")
                    user_activity.activity = 'service_1#faq#done'
                    db.commit()
                # Kopitu TANIPRENEUR
                if message_body == '4':
                    tw.sendMsg(nomor_hp, f"*[KOPITU TANIPRENEURS]*\nInformasi sedang dalam proses.\n\n{back}")
                    user_activity.activity = 'service_1#faq#done'
                    db.commit()
                # Kopitu SISTERCITY
                if message_body == '5':
                    tw.sendMsg(nomor_hp, f"*[KOPITU SISTERCITY]*\nInformasi sedang dalam proses.\n\n{back}")
                    user_activity.activity = 'service_1#faq#done'
                    db.commit()
                # Kopitu E-STORE
                if message_body == '6':
                    tw.sendMsg(nomor_hp, f"*[KOPITU E-STORE]*\nInformasi sedang dalam proses.\n\n{back}")
                    user_activity.activity = 'service_1#faq#done'
                    db.commit()
                # Kopitu SANTRIPRENEUR
                if message_body == '7':
                    tw.sendMsg(nomor_hp, f"*[KOPITU SANTRIPRENEUR]*\nInformasi sedang dalam proses.\n\n{back}")
                    user_activity.activity = 'service_1#faq#done'
                    db.commit()
                # Kopitu NELAYANPRENEUR
                if message_body == '8':
                    tw.sendMsg(nomor_hp, f"*[KOPITU NELAYANPRENEUR]*\nInformasi sedang dalam proses.\n\n{back}")
                    user_activity.activity = 'service_1#faq#done'
                    db.commit()
                # Kopitu DIFABELPRENEUR
                if message_body == '9':
                    tw.sendMsg(nomor_hp, f"*[KOPITU DIFABELPRENEUR]*\nInformasi sedang dalam proses.\n\n{back}")
                    user_activity.activity = 'service_1#faq#done'
                    db.commit()
                # Kopitu METAVERSE
                if message_body == '10':
                    tw.sendMsg(nomor_hp, f"*[KOPITU METAVERSE]*\nInformasi sedang dalam proses.\n\n{back}")
                    user_activity.activity = 'service_1#faq#done'
                    db.commit()
                # IDNTOWN
                if message_body == '11':
                    tw.sendMsg(nomor_hp, f"*[IDNTOWN]*\nInformasi sedang dalam proses.\n\n{back}")
                    user_activity.activity = 'service_1#faq#done'
                    db.commit()
                # IDNTOWN Kampoeng Halal
                if message_body == '12':
                    tw.sendMsg(nomor_hp, f"*[IDNTOWN KAMPOENG HALAL]*\nInformasi sedang dalam proses.\n\n{back}")
                    user_activity.activity = 'service_1#faq#done'
                    db.commit()
                # KOPITU Desa AI
                if message_body == '13':
                    tw.sendMsg(nomor_hp, f"*[KOPITU DESA AI]*\nInformasi sedang dalam proses.\n\n{back}")
                    user_activity.activity = 'service_1#faq#done'
                    db.commit()
                # Error            
                    
            # TENTANG MEMBERSHIP
            elif act_faq[2] == 'member':
                user_activity.activity = 'decision'
                db.commit()
                return {"success": True}

            elif act_faq[2] == 'done' and message_body == 'kembali':
                user_activity.activity == 'service_1'
                tw.sendMsg(nomor_hp, f"Apa yang anda ingin anda ketahui pada KOPITU?\n1. Tentang KOPITU\n2. Program KOPITU")                
                return {"success": True}
            
        if user_activity.activity.startswith('service_2#'):
            user_activity.activity.split('#')
            act = user_activity.activity.split('#')
            print(act)
            # FORM KTP
            if act[1] == 'registrasi':
                if act[2] == 'nama':
                    # Insert first data to form_ktp
                    new_regist_form = provider.models.registrasi(nama=message_body, id_user_activity=int(user_activity.id))
                    db.add(new_regist_form)
                    db.commit()
                    # Update Activity
                    user_activity.activity = f'service_2#registrasi#nik#{new_regist_form.id_registrasi}'
                    db.commit()
                    tw.sendMsg(nomor_hp, f"Berapa Nomor Induk Keluarga (NIK) Anda?")
                    return {"success": True}
                if act[2] == "nik":
                    existing_regist_form = db.query(provider.models.registrasi).filter_by(id_registrasi = act[3]).first()
                    existing_regist_form.nik = message_body
                    user_activity.activity = f'service_2#registrasi#ttl#{act[3]}'
                    db.commit()
                    tw.sendMsg(nomor_hp, f"Kapan Anda lahir? (TANGGAL/BULAN/TAHUN contoh 19/10/1970 atau 19 Desember 1970)")
                    return {"success": True}
                if act[2] == "ttl":
                    existing_regist_form = db.query(provider.models.registrasi).filter_by(id_registrasi = act[3]).first()
                    existing_regist_form.ttl = message_body
                    user_activity.activity = f'service_2#registrasi#jenis_kelamin#{act[3]}'
                    db.commit()
                    tw.sendMsg(nomor_hp, f"Apa jenis kelamin Anda? (P/L)")    
                    return {"success": True}        
                if act[2] == "jenis_kelamin":
                    existing_regist_form = db.query(provider.models.registrasi).filter_by(id_registrasi = act[3]).first()
                    existing_regist_form.jenis_kelamin = message_body
                    user_activity.activity = f'service_2#registrasi#no_hp#{act[3]}'
                    db.commit()
                    tw.sendMsg(nomor_hp, f"Berapa nomor telpon Anda yang dapat kami hubungi?")
                    return {"success": True}
                if act[2] == "no_hp":
                    existing_regist_form = db.query(provider.models.registrasi).filter_by(id_registrasi = act[3]).first()
                    existing_regist_form.no_hp = message_body
                    user_activity.activity = f'service_2#registrasi#member#{act[3]}'
                    db.commit()
                    tw.sendMsg(nomor_hp, f"Jenis member apa yang hendak Anda daftarkan?\nPilihan:\n- SILVER(gratis)\n- GOLD\n- PLATINUM)")
                    return {"success": True}
                if act[2] == "member":
                    # if-else tanya info pilihan member
                    existing_regist_form = db.query(provider.models.registrasi).filter_by(id_registrasi = act[3]).first()
                    existing_regist_form.member = message_body
                    user_activity.activity = f'service_2#registrasi#provinsi#{act[3]}'
                    db.commit()
                    tw.sendMsg(nomor_hp, f"Dimana provinsi Anda tinggal?")
                    return {"success": True}
                if act[2] == "provinsi":
                    existing_regist_form = db.query(provider.models.registrasi).filter_by(id_registrasi = act[3]).first()
                    existing_regist_form.provinsi = message_body
                    user_activity.activity = f'service_2#registrasi#kecamatan#{act[3]}'
                    db.commit()
                    tw.sendMsg(nomor_hp, f"Dimana kecamatan tempat Anda tinggal?")
                    return {"success": True}
                if act[2] == "kecamatan":
                    existing_regist_form = db.query(provider.models.registrasi).filter_by(id_registrasi = act[3]).first()
                    existing_regist_form.kecamatan = message_body
                    user_activity.activity = f'service_2#registrasi#kabupaten_kota#{act[3]}'
                    db.commit()
                    tw.sendMsg(nomor_hp, f"Dimana Kabupaten/Kota Anda tinggal?")
                    return {"success": True}
                if act[2] == "kabupaten_kota":
                    existing_regist_form = db.query(provider.models.registrasi).filter_by(id_registrasi = act[3]).first()
                    existing_regist_form.kabupaten_kota = message_body
                    user_activity.activity = f'service_2#registrasi#kode_pos#{act[3]}'
                    db.commit()
                    tw.sendMsg(nomor_hp, f"Berapa Kode Pos alamat Anda?")
                    return {"success": True}
                if act[2] == "kode_pos":
                    existing_regist_form = db.query(provider.models.registrasi).filter_by(id_registrasi = act[3]).first()
                    existing_regist_form.kode_pos = message_body
                    user_activity.activity = f'service_2#registrasi#warganegara#{act[3]}'
                    db.commit()
                    tw.sendMsg(nomor_hp, f"Apa kewarganegaraan Anda?")
                    return {"success": True}
                if act[2] == "warganegara":
                    existing_regist_form = db.query(provider.models.registrasi).filter_by(id_registrasi = act[3]).first()
                    existing_regist_form.warganegara = message_body
                    user_activity.activity = f'service_2#registrasi#alamat#{act[3]}'
                    db.commit()
                    tw.sendMsg(nomor_hp, f"Di mana alamat lengkap Anda?")
                    return {"success": True}
                if act[2] == "alamat":
                    existing_regist_form = db.query(provider.models.registrasi).filter_by(id_registrasi = act[3]).first()
                    existing_regist_form.alamat = message_body
                    user_activity.activity = f'service_2#registrasi#jenis_usaha#{act[3]}'
                    db.commit()
                    tw.sendMsg(nomor_hp, f"Apa jenis usaha Anda?")
                    return {"success": True}
                if act[2] == "jenis_usaha":
                    existing_regist_form = db.query(provider.models.registrasi).filter_by(id_registrasi = act[3]).first()
                    existing_regist_form.jenis_usaha = message_body
                    user_activity.activity = f'service_2#registrasi#kelas_usaha#{act[3]}'
                    db.commit()
                    tw.sendMsg(nomor_hp, f"Apa kelas dari usaha Anda?\n- MIKRO - (50-300JT)\n- KECIL - (300-500JT)\n- MENENGAH - (2.5M-50M)\n- BESAR (>50M)")
                    return {"success": True}
                if act[2] == "kelas_usaha":
                    existing_regist_form = db.query(provider.models.registrasi).filter_by(id_registrasi = act[3]).first()
                    existing_regist_form.kelas_usaha = message_body
                    user_activity.activity = f'service_2#registrasi#deskripsi_usaha#{act[3]}'
                    db.commit()
                    tw.sendMsg(nomor_hp, f"Bisakah Anda jelaskan deskripsi usaha Anda?")
                    return {"success": True}
                if act[2] == "deskripsi_usaha":
                    existing_regist_form = db.query(provider.models.registrasi).filter_by(id_registrasi = act[3]).first()
                    existing_regist_form.deskripsi_usaha = message_body
                    user_activity.activity = f'service_2#registrasi#ijin_usaha#{act[3]}'
                    db.commit()
                    tw.sendMsg(nomor_hp, f"Apa saja perizinan yang Anda miliki saat ini?\n- Usaha Dagang\n1. Surat Izin Usaha Perdagangan\n2. Sertifikat Halal\n3. Sertifikat BPOM\n4. Sertifikat PIRT\n5. Sertifikat NIB\n6. Sertifikat SKU\n7. Sertifikat IUMK\n8. Tidak Memiliki Izin\nPilih sertifikat yang dimiliki dengan menginput nomor di atas (Contoh: 1,2,5,dst)")
                    return {"success": True}
                if act[2] == "ijin_usaha":
                    existing_regist_form = db.query(provider.models.registrasi).filter_by(id_registrasi = act[3]).first()
                    existing_regist_form.ijin_usaha = message_body
                    user_activity.activity = f'service_2#registrasi#finish#{act[3]}'
                    db.commit()
                    
                    tw.sendMsg(nomor_hp, f"Terima kasih. Dokumen anda telah selesai diproses.\n a. Cetak pdf dokumen registrasi b. Tampilkan data di layar")
                if act[2] == "finish":
                    if message_body == 'a':
                        # cetak pdf
                        tw.sendMsg(nomor_hp, f"Dokumen sedang diproses, mohon ditunggu. Pengolahan dokumen dapat memakan waktu 1 hingga 5 menit")
                        file_name = word.wrapper_doc(nomor_hp=nomor_hp)
                        url = f'{protocol}://{host}/download/{file_name}.docx'
                        user_activity.activity = f'finish'
                        db.commit()

                        tw.sendAttach(nomor_hp, url, f"Terima kasih. Berikut dokumen anda yang telah diproses.\n\nLink bila dokumen tidak dapat dibuka: {url}\n\nKetik 'menu' untuk kembali.")
                        return {"success": True}
                    if message_body == 'b':
                        user_activity.activity = 'menu'
                        tw.sendAttach(nomor_hp, url, f"(Contoh tampilan data), ketik 'menu' untuk kembali ke awal.")
                        return {"success": True}
                    if message_body not in ['a', 'b', 'menu']:
                        tw.sendMsg(nomor_hp, "Pilihan tidak ada. Silakan memilih kembali berdasarkan menu yang diberikan.")

        if message_body == 'menu' or message_body == 'Menu':
            user_activity.activity = 'decision'
            db.commit()
            tw.sendMsg(nomor_hp, f"*[MENU CHATBOT KOPITU]*\nApa yang dapat kami bantu, {name}?\n1. Informasi Umum KOPITU \n2.Registrasi Member Baru\n3. Bantuan Informasi")
            return {"success": True}

    return {"success": True}
    

