celery -A config.celery worker -l INFO
buat fungsi artikel seperti ini: https://www.metoffice.gov.uk/weather/learn-about/weather/types-of-weather

fitur
-	ada tag di momen dan attachment
- 	ketika user posting bisa men-tag user kedalam momen dan foto
- 	user yang di-tag mendapatkan notifikasi
- 	jika momen diposting non-anonim maka user anonim tidak bisa melihatnya
	user terdaftar bisa melihat momen anonim dan momen non-anonim, user anonim hanya bisa melihat
	posting anonim pula
-	komentar pada momen dan foto
-	hashtags moment dan foto

selesai
1	daftar
2	login
3	profil
4	lupa password
5	submit lokasi
6	submit attachments
7	submit moment
8	tags moment
9	tags attachment
10	withs moment
11	moment comment
12	tags berbasis lokasi
13	filter moment dengan tags

selanjutnya
1	attachment comment
2	urutan foto salah setelah edit dengan menambah foto

flow
1	harus mengaktifkan lokasi (gps) ponsel / browser
2	simpan data gps dapatkan guid-nya
3	masukkan guid_gps ke moment
4	atau masukkan guid_gps ke attachment

problem sebagai anonim
- sulit selalu menggunakan attribute setiap edit / delete
- solusinya gunakan data device sebagai user account (nama device, imei, iccid, imsi, uuid)
- gunakan imei sebagai email/username dan password (jika user ingin hapus / edit moment nya)

harus dikalkulasi di level Moment setelah itu subquerykan kedalam tag