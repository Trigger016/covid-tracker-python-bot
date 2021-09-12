import re
import pytz
import pandas as pd
import datetime
import data_fetch
from telegram.ext import Updater, CallbackContext
from telegram import ChatAction, ParseMode, Update
from functools import wraps
from textwrap import dedent
from fuzzywuzzy import process

def typing(action):
    """ DECORATOR Give (typing...) feedback to user"""
    def decorator(func):
        @wraps(func)
        def command_func(update, context, *args, **kwargs):
            context.bot.send_chat_action(chat_id=update.effective_message.chat_id, action=action)
            return func(update, context, *args, **kwargs)
        return command_func
    return decorator

def format(val):
    val = str(int(val))
    pattern = "(\d)(?=(\d{3})+(?!\d))"
    sub = r"\1,"
    val = re.sub(pattern, sub, val)
    return val

def suggestion(val, ref):
    highest = process.extractOne(val, ref)
    return highest[0]

def remove_job_if_exists(name: str, context: CallbackContext) -> bool:
    """Remove job with given name. Returns whether job was removed."""
    current_jobs = context.job_queue.get_jobs_by_name(name)
    if not current_jobs:
        return False
    for job in current_jobs:
        job.schedule_removal()
    return True

@typing(ChatAction.TYPING)
def start_command(update: Update, context: CallbackContext):
    """starting bot and refreshing data"""
    
    # obtaining user basic info 
    first = update.message.chat.first_name
    last = update.message.chat.last_name
    chat_id = update.message.chat_id
    user_job_id = f"first_run={str(chat_id)}"

    # internal job
    def updating(context: CallbackContext):
        try:
            context.bot.send_message(chat_id=chat_id, 
                                     text="\nMohon Tunggu, data sedang di update...")
            context.bot.send_sticker(chat_id=chat_id, 
                                     sticker="CAACAgIAAxkBAAEC3MVhNfa2LUuYGj0NDs0DYn3AhzwqyAACIwADKA9qFCdRJeeMIKQGIAQ")         
            # refreshing data
            data_fetch.table_fetch()
            data_fetch.local_fetch()
            # sending success message
            context.bot.send_message(chat_id=chat_id, 
                                     text="Data Selesai di update.\nData akan di update setiap hari pukul 06:00 WIB.\n\nSilahkan Gunakan /help untuk Melihat Daftar Perintah dan Utilitas.")
        except Exception as e:
            context.bot.send_message(chat_id=chat_id, 
                                     text="Data Gagal di Update. Error :" + str(e))
    
    context.bot.send_message(chat_id=chat_id, 
                             text=f"Selamat Datang {first} {last} di Bot CovidTracker🤖.")
    
    # Run the command for first time 
    context.job_queue.run_once(updating, 
                               when=0.5, 
                               context=chat_id, 
                               name=user_job_id)
    # queue the job daily
    context.job_queue.run_daily(updating, datetime.time(hour=6, 
                                                        minute=0, 
                                                        tzinfo=pytz.timezone('Asia/Jakarta')), 
                                                        days=(0,1,2,3,4,5,6), 
                                                        context=chat_id, 
                                                        name="d_update")


@typing(ChatAction.TYPING)
def help_command(update: Update, context: CallbackContext):
    """display command listing to user"""
    text = """
           <strong>🤖Berikut Daftar Menu pada Bot.</strong>
           
           <strong><em><u>⚙️Utilitas Bot.</u></em></strong>

           ✅/start - Memulai Bot.
           ✅/help - Memberikan Daftar Perintah yang Tersedia.
           ✅/refresh - Mengambil/Memperbarui data secara manual.

           <strong><em><u>⏰Pengatur Notifikasi.</u></em></strong>
           
           ✅/notif jam menit 
           <code><em>(contoh: /notif 16 00)</em></code>
           Deskripsi :
           Memberikan notifikasi data statistik COVID-19 setiap hari pada jam dan waktu yang diatur pengguna.
           (Menggunakan zona waktu WIB)
           ✅/reset
           Deskripsi :
           Menghentikan notifikasi yang telah dibuat.
           
           <strong><em><u>ℹ️Informasi COVID-19.</u></em></strong>

           ✅/covid19
           Deskripsi :
           Memberikan Informasi Dasar Mengenai COVID-19.
           ✅/covid_world all | nama_negara 
           <code><em>(contoh: /covid_world korea)</em></code>
           Deskripsi : 
           Mengambil Data Statistik COVID-19 di Seluruh Dunia atau pada Negara Tertentu.
           ✅/covid_id nama_provinsi
           <code><em>(contoh: /covid_id aceh)</em></code>
           Deskripsi :
           Mengambil Data Statistik COVID-19 di Seluruh Dunia atau pada Negara Tertentu.
           ✅/berita
           Menyajikan berita terkini yang tersedia mengenai COVID-19.
           """
    if text is not None:
        update.message.reply_text(text=dedent(text),
                                  parse_mode=ParseMode.HTML,
                                  disable_web_page_preview=True)

@typing(ChatAction.TYPING)
def status_comm(update: Updater, context: CallbackContext):
    chat_id = update.message.chat_id
    # Data Proccess
    cd = pd.read_csv('./stored_data/cov_data.csv')

    # Retrieving reg list
    countrylist = cd["Country,Other"].tolist()
    countrylist = [str(each).lower() for each in countrylist]
    try:
        # Converting Params to str
        reg = str(context.args[0]).lower()
        if reg == "all":
            w_data = cd[cd["Country,Other"] == "World"].values.tolist()[0]
            text = f"""
                    <strong>Statistik COVID-19 Dunia</strong>
                    Tanggal : {datetime.date.today().strftime('%d %B %Y')}
                    
                    📊 Aktif
                    Ringan :
                    {format((w_data[9] - w_data[10]))} Jiwa
                    Serius :
                    {format(w_data[10])} Jiwa
                    
                    📊 Kematian
                    {format(w_data[5])}({w_data[6]}) Jiwa
                    
                    📊 Pulih/Sembuh
                    {format(w_data[7])}({w_data[8]}) Jiwa

                    📊 Total
                    {format(w_data[3])}({w_data[4]}) Jiwa
                    """
        else:
            suggested = suggestion(reg, countrylist)
            c_data = cd[cd["Country,Other"].str.lower() == suggested].values.tolist()[0]
            text = f"""
                    <strong>Statistik COVID-19 {c_data[2]}</strong>
                    Tanggal : {datetime.date.today().strftime('%d %B %Y')}
                    
                    📊 Aktif
                    Ringan :
                    {format((c_data[9] - c_data[10]))} Jiwa
                    Serius :
                    {format(c_data[10])} Jiwa
                    
                    📊 Kematian
                    {format(c_data[5])}({c_data[6]}) Jiwa
                    
                    📊 Pulih/Sembuh
                    {format(c_data[7])}({c_data[8]}) Jiwa

                    📊 Total
                    {format(c_data[3])}({c_data[4]}) Jiwa\n
                    """
            if reg in countrylist:
                text += ""
            else:
                text += f"<em>Menampilkan hasil untuk : {suggested}</em>"

    except(IndexError, ValueError):
        text = "Format yang anda masukkan salah.\nGunakan format: \n/covid_world <em>all  |  nama_negara</em>"
            
    if text is not None:
        context.bot.send_message(chat_id=chat_id,
                                 text=dedent(text), 
                                 parse_mode=ParseMode.HTML, 
                                 disable_web_page_preview=True)

@typing(ChatAction.TYPING)
def set_tracker(update: Update, context: CallbackContext) -> None:
    """Add a job to the queue."""
    chat_id = update.message.chat_id
    
    # internal jobs
    def status(context: CallbackContext):
        data_fetch.table_fetch()
        job_data = pd.read_csv('./stored_data/cov_data.csv')
        daily_job = job_data[job_data["Country,Other"] == "World"].values.tolist()[0]
        text = f"""
                ⏰ALARM


                Statistik COVID-19 Dunia
                Tanggal : {datetime.date.today().strftime('%d %B %Y')}
                
                📊 Aktif
                Ringan :
                {format((daily_job[9] - daily_job[10]))} Jiwa
                Serius :
                {format(daily_job[10])} Jiwa
                
                📊 Kematian
                {format(daily_job[5])}({daily_job[6]}) Jiwa
                
                📊 Pulih/Sembuh
                {format(daily_job[7])}({daily_job[8]}) Jiwa

                📊 Total
                {format(daily_job[3])}({daily_job[4]}) Jiwa

                Alarm berhasil dijalankan pada pukul {datetime.datetime.now().strftime("%H:%M")} WIB.
                """
        context.bot.send_message(chat_id=chat_id, 
                                 text=dedent(text), 
                                 parse_mode=ParseMode.HTML)

    try:
        # defining argument pass
        hours = int(context.args[0])
        minutes = int(context.args[1])
        
        # args[0] should contain the time for the timer in seconds
        if 0<=hours<24 and 0<=minutes<60:
            if minutes < 10:
                text=f"Mengatur Notifikasi status COVID pada\n{hours}:0{minutes} WIB\n{hours + 1}:0{minutes} WITA\n{hours + 2}:0{minutes} WIT\nSetiap Hari"
            else: 
                text=f"Mengatur Notifikasi status COVID pada\n{hours}:{minutes} WIB\n{hours + 1}:{minutes} WITA\n{hours + 2}:{minutes} WIT\nSetiap Hari"
            text+="\nGunakan /reset untuk menghentikan notifikasi"
        else : 
            text = "Jam atau Menit yang anda atur melewati format 24 jam."
        
        # Check if job Exist
        job_removed = remove_job_if_exists(str(chat_id), context)
        if job_removed:
            text+="\nTimer lama berhasil dihapus"
        update.message.reply_text(text)

        # input job to job queue
        context.job_queue.run_daily(status, datetime.time(hour=hours, 
                                                          minute=minutes, 
                                                          tzinfo=pytz.timezone('Asia/Jakarta')),
                                                          days=(0, 1, 2, 3, 4, 5, 6), 
                                                          context=chat_id, 
                                                          name=str(chat_id))

    except(IndexError, ValueError):
        update.message.reply_text('Penggunaan: /notif jam menit \n*Gunakan Format Waktu 24 Jam')

@typing(ChatAction.TYPING)
def unset(update: Update, context: CallbackContext) -> None:
    """Remove the job if the user changed their mind."""
    chat_id = update.message.chat_id
    job_removed = remove_job_if_exists(str(chat_id), context)
    text = 'Timer berhasil dibatalkan' if job_removed else 'Saat ini tidak ada Timer yang diatur.'
    update.message.reply_text(text)

@typing(ChatAction.TYPING)
def berita(update: Update, context: CallbackContext):
    try:
        text = ""
        # updating and reading the data
        update.message.reply_text("Mohon tunggu...\nSedang memperbarui berita hari ini.")
        data_list = data_fetch.news_fetch()
        update.message.reply_text("Berita berhasil diperbarui")
        
        # formatting output
        for key in data_list:
            text += f"\n\nBerita Terkini Mengenai {key.upper()}\n\n"
            for item in data_list[key]:
                text += f"""- <a href="{item['link']}">{item['title']} ({item['timestamp']})</a>\n"""
                
    except(IndexError):
        pass
    update.message.reply_text(text=dedent(text),
                              parse_mode=ParseMode.HTML)

@typing(ChatAction.TYPING)
def indonesia(update: Update, context: CallbackContext):
    '''serving local covid data'''
    chat_id = update.message.chat_id
    
    # Calling Data
    local_data = pd.read_csv("./stored_data/local_cov.csv")
    province_data = local_data["Provinsi"].tolist()
    provinces = [str(each).lower() for each in province_data]
    try:    
        p_input = str(context.args[0]).lower()
        # Data Matching
        suggest = suggestion(p_input, provinces)
        # output Designing
        w_data = local_data[local_data["Provinsi"].str.lower() == suggest].values.tolist()[0]
        text = f"""
                Status COVID-19 di {w_data[3]}
                Tanggal : {datetime.date.today().strftime("%d %B %Y")}
                
                📊 Positif :
                {format(w_data[4])}
                📊 Sembuh : 
                {format(w_data[5])}
                📊 Kematian:
                {format(w_data[6])}
                """
        if p_input in provinces:
            text += "Format yang anda masukkan salah.\nGunakan format: \n/covid_id <em>nama_provinsi</em>"
        else:
            text += f"<em>Menampilkan hasil untuk : {suggest}</em>"
    except (IndexError, ValueError):
        text = "Format yang anda masukkan salah.\nGunakan format: \n/covid_id <em>nama_provinsi</em>"
    if text is not None:
        context.bot.send_message(chat_id=chat_id, 
                                 text=dedent(text), 
                                 parse_mode=ParseMode.HTML)

def info(update:Updater, context: CallbackContext):
    text = """
           🦠<strong><u>COVID-19</u></strong>🦠
           
           <strong><em>Pengertian Umum</em></strong>
           Secara umum, COVID-19 adalah penyakit menular dari jenis keluarga Coronavirus yang ditemukan pada tahun 2019.
           Mayoritas orang yang terpapar COVID-19 akan mengalami gejala ringan hingga sedang bahkan terdapat kemungkinan
           dapat sembuh tanpa pengobatan khusus. Namun, beberapa diantaranya mengalami sakit serius dan memerlukan perhatian medis.

           <strong><em>Sejarah Singkat</em></strong>
           Corona virus merupakan sebuah keluarga virus yang menjadi penyebab berbagai macam penyakit, mulai dari gejala ringan sampai berat. 
           Pada saat ini, terdapat dua jenis Corona Virus yang menyebabkan penyakit gejala berat yaitu Middle East Respiratory Syndrome (MERS)
           dan Severe Acute Respiratory Syndrome (SARS). Secara umum penyakit ini adalah zoonosis (menular dari hewan maupun manusia).
           Kisah COVID-19 ini berasal dari penemuan penyakit peradangan paru-paru yang tidak diketahui sebabnya di Wuhan, Cina pada tanggal 19 Desember 2019.
           Dilanjutkan pada tanggal 7 Januari 2020 Cina mengidentifkasikan virus tersebut sebagai bagian dari keluarga baru Coronavirus yang secara resmi dinamakan 
           <em>Coronavirus Disease 19(COVID-19)</em> atau dengan nama lain <em>Severe Acute Respiratory Syndrome Corona Virus 2(SARS-CoV-2).</em>
           
           <strong><em>Penyebaran</em></strong>
           Menurut WHO, virus ini dapat menyebar melalui mulut atau hidung orang yang terinfeksi dalam bentuk partikel cairan kecil ketika
           batuk, bersin, berbicara, bernyanyi, atau bernapas. Partikel-partikel tersebut kemudian jatuh dan dapat menempel di permukaan kulit
           manusia maupun benda. Virus akan mudah untuk menginfeksi seseorang jika secara tidak sengaja memegang permukaan yang terkontaminasi, kemudian menyentuh bagian muka seperti mata atau hidung. 

           Virus ini juga menyebar lebih cepat di dalam ruang tertutup dan di tempat yang ramai.

           <strong><em>Pencegahan</em></strong>
           Tetap berhati-hati dengan melakukan beberapa tindakan sederhana seperti :
           - Menjaga jarak.
           - Memakai masker.
           - Menjaga agar ruangan berventilasi.
           - Menghindari keramaian.
           - Mencuci tangan secara teratur atau menggunakan sanitizer.
           - Menutup mulut dan hidung ketika batuk dan bersin menggunakan tisu atau lengan.
           """
    update.message.reply_text(text=dedent(text),
                              parse_mode=ParseMode.HTML)

def refresh(update:Updater, context: CallbackContext):
    try:
        update.message.reply_text("Mohon Tunggu, Data sedang di Update")
        data_fetch.table_fetch()
        data_fetch.local_fetch()
        update.message.reply_text("Data Berhasil di Update")
    except Exception as e:
        update.message.reply_text("Data Gagal di Update. Error :" + str(e))