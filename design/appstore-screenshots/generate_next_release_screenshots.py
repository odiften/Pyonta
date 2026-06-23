#!/usr/bin/env python3
from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

import generate_appstore_screenshots as g


ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(ROOT / "scripts"))
from next_release_locales import TARGET_LOCALES, complex_text_locale_codes, rtl_locale_codes  # noqa: E402


OUT = g.OUT / "next-release"
ASSET_DIR = Path(__file__).resolve().parent / "assets" / "lucide"
CORE_TEXT_SCRIPT = ROOT / "scripts" / "render_text_coretext.swift"
CORE_TEXT_BINARY = Path(tempfile.gettempdir()) / "pyonta-render-text-coretext"
CORE_TEXT_LOCALES = set(rtl_locale_codes()) | set(complex_text_locale_codes())
SHAPED_TEXT_LOCALES = {"ar", "bn", "he", "hi", "th"}


COPY = {
    "ar": {
        "subtitle": "نقل ملفات Android",
        "receiveTitle": "نقل ملفات من Android إلى Mac",
        "receiveBody": "استقبل الصور والفيديو وملفات PDF والروابط والنصوص من Android على Mac.",
        "sendTitle": "نقل ملفات من Mac إلى Android",
        "sendBody": "أرسل الملفات أو نص الحافظة من شريط القوائم أو Finder.",
        "qrTitle": "اتصال عبر QR",
        "qrBody": "إذا لم تظهر الأجهزة، تابع النقل باستخدام رمز QR.",
        "plusTitle": "افتح الاستقبال",
        "plusBody": "الإرسال من Mac مجاني. الاستقبال من Android يتطلب Pyonta+.",
    },
    "bg": {
        "subtitle": "Прехвърляне на файлове от Android",
        "receiveTitle": "Прехвърляне на файлове от Android към Mac",
        "receiveBody": "Получавайте снимки, видео, PDF, връзки и текст от Android на своя Mac.",
        "sendTitle": "Прехвърляне на файлове от Mac към Android",
        "sendBody": "Изпращайте файлове или текст от клипборда от менюто или Finder.",
        "qrTitle": "Връзка с QR",
        "qrBody": "Ако устройствата не се показват, продължете с QR код.",
        "plusTitle": "Отключете получаването",
        "plusBody": "Изпращането от Mac е безплатно. Получаването от Android изисква Pyonta+.",
    },
    "bn": {
        "subtitle": "Android ফাইল স্থানান্তর",
        "receiveTitle": "Android থেকে Mac-এ ফাইল স্থানান্তর",
        "receiveBody": "Android থেকে আপনার Mac-এ ছবি, ভিডিও, PDF, লিংক ও লেখা নিন।",
        "sendTitle": "Mac থেকে Android-এ ফাইল স্থানান্তর",
        "sendBody": "মেনু বার বা Finder থেকে ফাইল বা ক্লিপবোর্ডের লেখা পাঠান।",
        "qrTitle": "QR দিয়ে সংযোগ",
        "qrBody": "ডিভাইস না দেখালে QR কোড দিয়ে স্থানান্তর চালিয়ে যান।",
        "plusTitle": "গ্রহণ চালু করুন",
        "plusBody": "Mac থেকে পাঠানো বিনামূল্যে। Android থেকে গ্রহণ করতে Pyonta+ দরকার।",
    },
    "ca": {
        "subtitle": "Transferencia de fitxers Android",
        "receiveTitle": "Transferència de fitxers d'Android a Mac",
        "receiveBody": "Rep fotos, vídeos, PDF, enllaços i text d'Android al Mac.",
        "sendTitle": "Transferència de fitxers de Mac a Android",
        "sendBody": "Envia fitxers o text del porta-retalls des de la barra de menús o el Finder.",
        "qrTitle": "Connexió amb QR",
        "qrBody": "Si no apareixen dispositius, continua amb un codi QR.",
        "plusTitle": "Desbloqueja la recepció",
        "plusBody": "Enviar des del Mac és gratis. Rebre des d'Android requereix Pyonta+.",
    },
    "cs": {
        "subtitle": "Přenos souborů z Androidu",
        "receiveTitle": "Přenos souborů z Androidu do Macu",
        "receiveBody": "Přijímejte na Mac fotky, videa, PDF, odkazy i text z Androidu.",
        "sendTitle": "Přenos souborů z Macu do Androidu",
        "sendBody": "Posílejte soubory nebo text ze schránky z řádku nabídek či Finderu.",
        "qrTitle": "Připojení přes QR",
        "qrBody": "Když se zařízení nezobrazí, pokračujte pomocí QR kódu.",
        "plusTitle": "Odemkněte příjem",
        "plusBody": "Odesílání z Macu je zdarma. Příjem z Androidu vyžaduje Pyonta+.",
    },
    "da": {
        "subtitle": "Android-filoverførsel",
        "receiveTitle": "Filoverførsel fra Android til Mac",
        "receiveBody": "Modtag fotos, videoer, PDF'er, links og tekst fra Android på din Mac.",
        "sendTitle": "Filoverførsel fra Mac til Android",
        "sendBody": "Send filer eller udklipsholdertekst fra menulinjen eller Finder.",
        "qrTitle": "Forbind med QR",
        "qrBody": "Hvis enheder ikke vises, kan du fortsætte med en QR-kode.",
        "plusTitle": "Lås modtagelse op",
        "plusBody": "Afsendelse fra Mac er gratis. Modtagelse fra Android kræver Pyonta+.",
    },
    "de": {
        "subtitle": "Android-Dateitransfer",
        "receiveTitle": "Dateitransfer von Android zu Mac",
        "receiveBody": "Empfange Fotos, Videos, PDFs, Links und Text von Android auf deinem Mac.",
        "sendTitle": "Dateitransfer von Mac zu Android",
        "sendBody": "Sende Dateien oder Zwischenablage-Text über Menüleiste oder Finder.",
        "qrTitle": "Mit QR verbinden",
        "qrBody": "Wenn Geräte nicht erscheinen, geht es mit einem QR-Code weiter.",
        "plusTitle": "Empfang freischalten",
        "plusBody": "Senden vom Mac bleibt kostenlos. Empfang von Android erfordert Pyonta+.",
    },
    "el": {
        "subtitle": "Μεταφορά αρχείων Android",
        "receiveTitle": "Μεταφορά αρχείων Android προς Mac",
        "receiveBody": "Λάβετε φωτογραφίες, βίντεο, PDF, συνδέσμους και κείμενο από Android στο Mac.",
        "sendTitle": "Μεταφορά αρχείων Mac προς Android",
        "sendBody": "Στείλτε αρχεία ή κείμενο πρόχειρου από τη γραμμή μενού ή το Finder.",
        "qrTitle": "Σύνδεση με QR",
        "qrBody": "Αν οι συσκευές δεν εμφανίζονται, συνεχίστε με κωδικό QR.",
        "plusTitle": "Ξεκλείδωμα λήψης",
        "plusBody": "Η αποστολή από Mac είναι δωρεάν. Η λήψη από Android απαιτεί Pyonta+.",
    },
    "en": {
        "subtitle": "Android file transfer",
        "receiveTitle": "Android to Mac file transfer",
        "receiveBody": "Receive photos, videos, PDFs, links, and text from Android on your Mac.",
        "sendTitle": "Mac to Android file transfer",
        "sendBody": "Send files or clipboard text from the menu bar or Finder.",
        "qrTitle": "Connect with QR",
        "qrBody": "If devices do not appear, keep going with a QR code.",
        "plusTitle": "Unlock receiving",
        "plusBody": "Sending from Mac is free. Receiving from Android requires Pyonta+.",
    },
    "es": {
        "subtitle": "Transferencia de archivos Android",
        "receiveTitle": "Transferencia de archivos de Android a Mac",
        "receiveBody": "Recibe fotos, videos, PDF, enlaces y texto de Android en tu Mac.",
        "sendTitle": "Transferencia de archivos de Mac a Android",
        "sendBody": "Envía archivos o texto del portapapeles desde la barra de menús o Finder.",
        "qrTitle": "Conectar con QR",
        "qrBody": "Si no aparecen dispositivos, continúa con un código QR.",
        "plusTitle": "Desbloquea la recepción",
        "plusBody": "Enviar desde Mac es gratis. Recibir desde Android requiere Pyonta+.",
    },
    "et": {
        "subtitle": "Androidi failiedastus",
        "receiveTitle": "Failiedastus Androidist Maci",
        "receiveBody": "Võta Macis vastu fotosid, videoid, PDF-e, linke ja teksti Androidist.",
        "sendTitle": "Failiedastus Macist Androidi",
        "sendBody": "Saada faile või lõikelaua teksti menüüribalt või Finderist.",
        "qrTitle": "Ühenda QR-koodiga",
        "qrBody": "Kui seadmeid ei kuvata, jätka QR-koodiga.",
        "plusTitle": "Ava vastuvõtt",
        "plusBody": "Macist saatmine on tasuta. Androidist vastuvõtt nõuab Pyonta+.",
    },
    "fi": {
        "subtitle": "Android-tiedostonsiirto",
        "receiveTitle": "Tiedostonsiirto Androidista Maciin",
        "receiveBody": "Vastaanota kuvia, videoita, PDF:iä, linkkejä ja tekstiä Androidista Maciin.",
        "sendTitle": "Tiedostonsiirto Macista Androidiin",
        "sendBody": "Lähetä tiedostoja tai leikepöydän tekstiä valikkoriviltä tai Finderista.",
        "qrTitle": "Yhdistä QR:llä",
        "qrBody": "Jos laitteet eivät näy, jatka QR-koodilla.",
        "plusTitle": "Avaa vastaanotto",
        "plusBody": "Macista lähettäminen on ilmaista. Androidista vastaanotto vaatii Pyonta+.",
    },
    "fil": {
        "subtitle": "Paglipat ng file sa Android",
        "receiveTitle": "Paglipat ng file mula Android papuntang Mac",
        "receiveBody": "Tumanggap ng larawan, video, PDF, link, at text mula Android sa iyong Mac.",
        "sendTitle": "Paglipat ng file mula Mac papuntang Android",
        "sendBody": "Magpadala ng file o clipboard text mula sa menu bar o Finder.",
        "qrTitle": "Kumonekta gamit ang QR",
        "qrBody": "Kung hindi lumabas ang mga device, magpatuloy gamit ang QR code.",
        "plusTitle": "I-unlock ang pagtanggap",
        "plusBody": "Libre ang pagpapadala mula Mac. Kailangan ang Pyonta+ para tumanggap mula Android.",
    },
    "fr": {
        "subtitle": "Transfert de fichiers Android",
        "receiveTitle": "Transfert de fichiers Android vers Mac",
        "receiveBody": "Recevez photos, vidéos, PDF, liens et texte d'Android sur votre Mac.",
        "sendTitle": "Transfert de fichiers Mac vers Android",
        "sendBody": "Envoyez fichiers ou texte du presse-papiers depuis la barre de menus ou le Finder.",
        "qrTitle": "Connexion par QR",
        "qrBody": "Si les appareils n'apparaissent pas, continuez avec un code QR.",
        "plusTitle": "Débloquer la réception",
        "plusBody": "L'envoi depuis Mac est gratuit. La réception depuis Android nécessite Pyonta+.",
    },
    "he": {
        "subtitle": "העברת קבצים מ-Android",
        "receiveTitle": "העברת קבצים מ-Android ל-Mac",
        "receiveBody": "קבל תמונות, סרטונים, PDF, קישורים וטקסט מ-Android ב-Mac שלך.",
        "sendTitle": "העברת קבצים מ-Mac ל-Android",
        "sendBody": "שלח קבצים או טקסט מהלוח משורת התפריטים או מ-Finder.",
        "qrTitle": "חיבור עם QR",
        "qrBody": "אם מכשירים לא מופיעים, המשך בעזרת קוד QR.",
        "plusTitle": "פתיחת קבלה",
        "plusBody": "שליחה מ-Mac היא בחינם. קבלה מ-Android דורשת Pyonta+.",
    },
    "hi": {
        "subtitle": "Android फ़ाइल ट्रांसफर",
        "receiveTitle": "Android से Mac में फ़ाइल ट्रांसफर",
        "receiveBody": "Android से अपने Mac पर फ़ोटो, वीडियो, PDF, लिंक और टेक्स्ट प्राप्त करें।",
        "sendTitle": "Mac से Android में फ़ाइल ट्रांसफर",
        "sendBody": "मेनू बार या Finder से फ़ाइलें या क्लिपबोर्ड टेक्स्ट भेजें।",
        "qrTitle": "QR से कनेक्ट करें",
        "qrBody": "डिवाइस न दिखें तो QR कोड से स्थानांतरण जारी रखें।",
        "plusTitle": "प्राप्त करना अनलॉक करें",
        "plusBody": "Mac से भेजना मुफ़्त है। Android से प्राप्त करने के लिए Pyonta+ चाहिए।",
    },
    "hr": {
        "subtitle": "Android prijenos datoteka",
        "receiveTitle": "Prijenos datoteka s Androida na Mac",
        "receiveBody": "Primajte fotografije, videozapise, PDF-ove, poveznice i tekst s Androida na Mac.",
        "sendTitle": "Prijenos datoteka s Maca na Android",
        "sendBody": "Šaljite datoteke ili tekst međuspremnika iz trake izbornika ili Findera.",
        "qrTitle": "Poveži QR-om",
        "qrBody": "Ako se uređaji ne pojave, nastavite s QR kodom.",
        "plusTitle": "Otključajte primanje",
        "plusBody": "Slanje s Maca je besplatno. Primanje s Androida zahtijeva Pyonta+.",
    },
    "hu": {
        "subtitle": "Android-fájlátvitel",
        "receiveTitle": "Fájlátvitel Androidról Macre",
        "receiveBody": "Fogadj fotókat, videókat, PDF-eket, linkeket és szöveget Androidról a Macen.",
        "sendTitle": "Fájlátvitel Macről Androidra",
        "sendBody": "Küldj fájlokat vagy vágólapszöveget a menüsorból vagy a Finderből.",
        "qrTitle": "Kapcsolódás QR-rel",
        "qrBody": "Ha az eszközök nem jelennek meg, folytasd QR-kóddal.",
        "plusTitle": "Fogadás feloldása",
        "plusBody": "Macről küldeni ingyenes. Androidról fogadni Pyonta+ szükséges.",
    },
    "id": {
        "subtitle": "Transfer file Android",
        "receiveTitle": "Transfer file Android ke Mac",
        "receiveBody": "Terima foto, video, PDF, tautan, dan teks dari Android di Mac Anda.",
        "sendTitle": "Transfer file Mac ke Android",
        "sendBody": "Kirim file atau teks papan klip dari bilah menu atau Finder.",
        "qrTitle": "Hubungkan dengan QR",
        "qrBody": "Jika perangkat tidak muncul, lanjutkan dengan kode QR.",
        "plusTitle": "Buka penerimaan",
        "plusBody": "Mengirim dari Mac gratis. Menerima dari Android memerlukan Pyonta+.",
    },
    "it": {
        "subtitle": "Trasferimento file Android",
        "receiveTitle": "Trasferimento file da Android a Mac",
        "receiveBody": "Ricevi foto, video, PDF, link e testo da Android sul tuo Mac.",
        "sendTitle": "Trasferimento file da Mac ad Android",
        "sendBody": "Invia file o testo dagli appunti dalla barra dei menu o dal Finder.",
        "qrTitle": "Connetti con QR",
        "qrBody": "Se i dispositivi non appaiono, continua con un codice QR.",
        "plusTitle": "Sblocca la ricezione",
        "plusBody": "Inviare dal Mac è gratis. Ricevere da Android richiede Pyonta+.",
    },
    "ja": {
        "subtitle": "Androidファイル転送",
        "receiveTitle": "AndroidからMacへ\nファイル転送",
        "receiveBody": "近くのMacを自動で見つけて、写真・動画・PDF・テキストなどを受け取れます。",
        "sendTitle": "MacからAndroidへ\nファイル転送",
        "sendBody": "近くのAndroidを自動で見つけて、写真・動画・PDF・テキストなどを送れます。",
        "qrTitle": "QRでも送信",
        "qrBody": "Androidが表示されない時も、QRコードで送信を続けられます。",
        "plusTitle": "Androidからの受信を解放",
        "plusBody": "Macからの送信は無料。Androidからの受信にはPyonta+が必要です。",
    },
    "ko": {
        "subtitle": "Android 파일 전송",
        "receiveTitle": "Android에서 Mac으로 파일 전송",
        "receiveBody": "Android의 사진, 동영상, PDF, 링크, 텍스트를 Mac에서 받습니다.",
        "sendTitle": "Mac에서 Android로 파일 전송",
        "sendBody": "메뉴 막대나 Finder에서 파일 또는 클립보드 텍스트를 보냅니다.",
        "qrTitle": "QR로 연결",
        "qrBody": "기기가 보이지 않으면 QR 코드로 전송을 계속합니다.",
        "plusTitle": "받기 잠금 해제",
        "plusBody": "Mac에서 보내기는 무료입니다. Android에서 받으려면 Pyonta+가 필요합니다.",
    },
    "lt": {
        "subtitle": "Android failų perkėlimas",
        "receiveTitle": "Failų perkėlimas iš Android į Mac",
        "receiveBody": "Gaukite nuotraukas, vaizdo įrašus, PDF, nuorodas ir tekstą iš Android į Mac.",
        "sendTitle": "Failų perkėlimas iš Mac į Android",
        "sendBody": "Siųskite failus arba iškarpinės tekstą iš meniu juostos ar Finder.",
        "qrTitle": "Prisijunkite QR kodu",
        "qrBody": "Jei įrenginiai nerodomi, tęskite naudodami QR kodą.",
        "plusTitle": "Atrakinkite gavimą",
        "plusBody": "Siuntimas iš Mac nemokamas. Gavimui iš Android reikia Pyonta+.",
    },
    "lv": {
        "subtitle": "Android failu pārsūtīšana",
        "receiveTitle": "Failu pārsūtīšana no Android uz Mac",
        "receiveBody": "Saņemiet fotoattēlus, video, PDF, saites un tekstu no Android savā Mac.",
        "sendTitle": "Failu pārsūtīšana no Mac uz Android",
        "sendBody": "Sūtiet failus vai starpliktuves tekstu no izvēļņu joslas vai Finder.",
        "qrTitle": "Savienot ar QR",
        "qrBody": "Ja ierīces neparādās, turpiniet ar QR kodu.",
        "plusTitle": "Atbloķēt saņemšanu",
        "plusBody": "Sūtīšana no Mac ir bez maksas. Saņemšanai no Android vajag Pyonta+.",
    },
    "ms": {
        "subtitle": "Pemindahan fail Android",
        "receiveTitle": "Pemindahan fail Android ke Mac",
        "receiveBody": "Terima foto, video, PDF, pautan dan teks daripada Android pada Mac anda.",
        "sendTitle": "Pemindahan fail Mac ke Android",
        "sendBody": "Hantar fail atau teks papan klip daripada bar menu atau Finder.",
        "qrTitle": "Sambung dengan QR",
        "qrBody": "Jika peranti tidak muncul, teruskan dengan kod QR.",
        "plusTitle": "Buka kunci penerimaan",
        "plusBody": "Menghantar daripada Mac adalah percuma. Menerima daripada Android memerlukan Pyonta+.",
    },
    "nb": {
        "subtitle": "Android-filoverføring",
        "receiveTitle": "Filoverføring fra Android til Mac",
        "receiveBody": "Motta bilder, videoer, PDF-er, lenker og tekst fra Android på Macen.",
        "sendTitle": "Filoverføring fra Mac til Android",
        "sendBody": "Send filer eller utklippstavletekst fra menylinjen eller Finder.",
        "qrTitle": "Koble til med QR",
        "qrBody": "Hvis enheter ikke vises, fortsett med en QR-kode.",
        "plusTitle": "Lås opp mottak",
        "plusBody": "Sending fra Mac er gratis. Mottak fra Android krever Pyonta+.",
    },
    "nl": {
        "subtitle": "Android-bestandsoverdracht",
        "receiveTitle": "Bestandsoverdracht van Android naar Mac",
        "receiveBody": "Ontvang foto's, video's, pdf's, links en tekst van Android op je Mac.",
        "sendTitle": "Bestandsoverdracht van Mac naar Android",
        "sendBody": "Verstuur bestanden of klembordtekst vanuit de menubalk of Finder.",
        "qrTitle": "Verbinden met QR",
        "qrBody": "Als apparaten niet verschijnen, ga verder met een QR-code.",
        "plusTitle": "Ontvangen ontgrendelen",
        "plusBody": "Versturen vanaf Mac is gratis. Ontvangen vanaf Android vereist Pyonta+.",
    },
    "pl": {
        "subtitle": "Transfer plików Android",
        "receiveTitle": "Przesyłanie plików z Androida na Maca",
        "receiveBody": "Odbieraj na Macu zdjęcia, filmy, PDF-y, linki i tekst z Androida.",
        "sendTitle": "Przesyłanie plików z Maca na Androida",
        "sendBody": "Wysyłaj pliki lub tekst ze schowka z paska menu albo Findera.",
        "qrTitle": "Połącz przez QR",
        "qrBody": "Jeśli urządzenia się nie pojawią, kontynuuj z kodem QR.",
        "plusTitle": "Odblokuj odbieranie",
        "plusBody": "Wysyłanie z Maca jest bezpłatne. Odbieranie z Androida wymaga Pyonta+.",
    },
    "pt-BR": {
        "subtitle": "Transferência de arquivos Android",
        "receiveTitle": "Transferência de arquivos do Android para Mac",
        "receiveBody": "Receba fotos, vídeos, PDFs, links e texto do Android no seu Mac.",
        "sendTitle": "Transferência de arquivos do Mac para Android",
        "sendBody": "Envie arquivos ou texto da área de transferência pela barra de menus ou Finder.",
        "qrTitle": "Conectar com QR",
        "qrBody": "Se os dispositivos não aparecerem, continue com um código QR.",
        "plusTitle": "Desbloqueie o recebimento",
        "plusBody": "Enviar do Mac é grátis. Receber do Android requer Pyonta+.",
    },
    "pt-PT": {
        "subtitle": "Transferência de ficheiros Android",
        "receiveTitle": "Transferência de ficheiros do Android para Mac",
        "receiveBody": "Receba fotografias, vídeos, PDF, ligações e texto do Android no Mac.",
        "sendTitle": "Transferência de ficheiros do Mac para Android",
        "sendBody": "Envie ficheiros ou texto da área de transferência pela barra de menus ou Finder.",
        "qrTitle": "Ligar com QR",
        "qrBody": "Se os dispositivos não aparecerem, continue com um código QR.",
        "plusTitle": "Desbloquear receção",
        "plusBody": "Enviar do Mac é gratuito. Receber do Android requer Pyonta+.",
    },
    "ro": {
        "subtitle": "Transfer de fișiere Android",
        "receiveTitle": "Transfer de fișiere Android către Mac",
        "receiveBody": "Primește fotografii, video, PDF-uri, linkuri și text de pe Android pe Mac.",
        "sendTitle": "Transfer de fișiere Mac către Android",
        "sendBody": "Trimite fișiere sau text din clipboard din bara de meniu sau Finder.",
        "qrTitle": "Conectare cu QR",
        "qrBody": "Dacă dispozitivele nu apar, continuă cu un cod QR.",
        "plusTitle": "Deblochează primirea",
        "plusBody": "Trimiterea de pe Mac este gratuită. Primirea de pe Android necesită Pyonta+.",
    },
    "ru": {
        "subtitle": "Передача файлов Android",
        "receiveTitle": "Передача файлов с Android на Mac",
        "receiveBody": "Получайте фото, видео, PDF, ссылки и текст с Android на Mac.",
        "sendTitle": "Передача файлов с Mac на Android",
        "sendBody": "Отправляйте файлы или текст буфера из строки меню или Finder.",
        "qrTitle": "Подключение по QR",
        "qrBody": "Если устройства не видны, продолжайте с QR-кодом.",
        "plusTitle": "Откройте прием",
        "plusBody": "Отправка с Mac бесплатна. Прием с Android требует Pyonta+.",
    },
    "sk": {
        "subtitle": "Prenos súborov z Androidu",
        "receiveTitle": "Prenos súborov z Androidu do Macu",
        "receiveBody": "Prijímajte na Mac fotky, videá, PDF, odkazy a text z Androidu.",
        "sendTitle": "Prenos súborov z Macu do Androidu",
        "sendBody": "Posielajte súbory alebo text zo schránky z panela menu či Findera.",
        "qrTitle": "Pripojenie cez QR",
        "qrBody": "Ak sa zariadenia nezobrazia, pokračujte pomocou QR kódu.",
        "plusTitle": "Odomknite prijímanie",
        "plusBody": "Odosielanie z Macu je bezplatné. Príjem z Androidu vyžaduje Pyonta+.",
    },
    "sl": {
        "subtitle": "Prenos datotek Android",
        "receiveTitle": "Prenos datotek iz Androida v Mac",
        "receiveBody": "Na Mac prejmite fotografije, videe, PDF-je, povezave in besedilo iz Androida.",
        "sendTitle": "Prenos datotek iz Maca v Android",
        "sendBody": "Pošljite datoteke ali besedilo iz odložišča iz menijske vrstice ali Finderja.",
        "qrTitle": "Poveži s QR",
        "qrBody": "Če se naprave ne prikažejo, nadaljujte s kodo QR.",
        "plusTitle": "Odklenite prejemanje",
        "plusBody": "Pošiljanje iz Maca je brezplačno. Prejemanje iz Androida zahteva Pyonta+.",
    },
    "sr": {
        "subtitle": "Android пренос датотека",
        "receiveTitle": "Пренос датотека са Android-а на Mac",
        "receiveBody": "Примајте фотографије, видео, PDF, линкове и текст са Android-а на Mac.",
        "sendTitle": "Пренос датотека са Mac-а на Android",
        "sendBody": "Шаљите датотеке или текст из клипборда из менија или Finder-а.",
        "qrTitle": "Повежи преко QR",
        "qrBody": "Ако се уређаји не појаве, наставите помоћу QR кода.",
        "plusTitle": "Откључајте пријем",
        "plusBody": "Слање са Mac-а је бесплатно. Пријем са Android-а захтева Pyonta+.",
    },
    "sv": {
        "subtitle": "Android-filöverföring",
        "receiveTitle": "Filöverföring från Android till Mac",
        "receiveBody": "Ta emot bilder, videor, PDF:er, länkar och text från Android på din Mac.",
        "sendTitle": "Filöverföring från Mac till Android",
        "sendBody": "Skicka filer eller urklippstext från menyraden eller Finder.",
        "qrTitle": "Anslut med QR",
        "qrBody": "Om enheter inte visas kan du fortsätta med en QR-kod.",
        "plusTitle": "Lås upp mottagning",
        "plusBody": "Att skicka från Mac är gratis. Att ta emot från Android kräver Pyonta+.",
    },
    "th": {
        "subtitle": "โอนไฟล์ Android",
        "receiveTitle": "ถ่ายโอนไฟล์จาก Android ไปยัง Mac",
        "receiveBody": "รับรูปภาพ วิดีโอ PDF ลิงก์ และข้อความจาก Android บน Mac ของคุณ",
        "sendTitle": "ถ่ายโอนไฟล์จาก Mac ไปยัง Android",
        "sendBody": "ส่งไฟล์หรือข้อความในคลิปบอร์ดจากแถบเมนูหรือ Finder",
        "qrTitle": "เชื่อมต่อด้วย QR",
        "qrBody": "หากไม่พบอุปกรณ์ ให้ดำเนินการต่อด้วยรหัส QR",
        "plusTitle": "ปลดล็อกการรับ",
        "plusBody": "ส่งจาก Mac ได้ฟรี การรับจาก Android ต้องใช้ Pyonta+",
    },
    "tr": {
        "subtitle": "Android dosya aktarımı",
        "receiveTitle": "Android'den Mac'e dosya aktarımı",
        "receiveBody": "Android'den Mac'inize fotoğraf, video, PDF, bağlantı ve metin alın.",
        "sendTitle": "Mac'ten Android'e dosya aktarımı",
        "sendBody": "Menü çubuğu veya Finder'dan dosya ya da pano metni gönderin.",
        "qrTitle": "QR ile bağlan",
        "qrBody": "Cihazlar görünmezse QR koduyla devam edin.",
        "plusTitle": "Almayı aç",
        "plusBody": "Mac'ten göndermek ücretsizdir. Android'den almak için Pyonta+ gerekir.",
    },
    "uk": {
        "subtitle": "Передавання файлів Android",
        "receiveTitle": "Передавання файлів з Android на Mac",
        "receiveBody": "Отримуйте фото, відео, PDF, посилання й текст з Android на Mac.",
        "sendTitle": "Передавання файлів з Mac на Android",
        "sendBody": "Надсилайте файли або текст буфера з рядка меню чи Finder.",
        "qrTitle": "Підключення через QR",
        "qrBody": "Якщо пристрої не з'являються, продовжуйте з QR-кодом.",
        "plusTitle": "Розблокуйте отримання",
        "plusBody": "Надсилання з Mac безкоштовне. Отримання з Android потребує Pyonta+.",
    },
    "vi": {
        "subtitle": "Truyền tệp Android",
        "receiveTitle": "Chuyển tệp từ Android sang Mac",
        "receiveBody": "Nhận ảnh, video, PDF, liên kết và văn bản từ Android trên máy Mac.",
        "sendTitle": "Chuyển tệp từ Mac sang Android",
        "sendBody": "Gửi tệp hoặc văn bản trong bảng nhớ tạm từ thanh menu hoặc Finder.",
        "qrTitle": "Kết nối bằng QR",
        "qrBody": "Nếu thiết bị không xuất hiện, tiếp tục bằng mã QR.",
        "plusTitle": "Mở khóa nhận",
        "plusBody": "Gửi từ Mac miễn phí. Nhận từ Android cần Pyonta+.",
    },
    "zh-Hans": {
        "subtitle": "Android 文件传输",
        "receiveTitle": "Android 到 Mac 文件传输",
        "receiveBody": "在 Mac 上接收来自 Android 的照片、视频、PDF、链接和文本。",
        "sendTitle": "Mac 到 Android 文件传输",
        "sendBody": "从菜单栏或 Finder 发送文件或剪贴板文本。",
        "qrTitle": "用 QR 连接",
        "qrBody": "如果设备没有出现，可继续使用 QR 码。",
        "plusTitle": "解锁接收",
        "plusBody": "从 Mac 发送免费。从 Android 接收需要 Pyonta+。",
    },
    "zh-Hant": {
        "subtitle": "Android 檔案傳輸",
        "receiveTitle": "Android 到 Mac 檔案傳輸",
        "receiveBody": "在 Mac 上接收來自 Android 的照片、影片、PDF、連結和文字。",
        "sendTitle": "Mac 到 Android 檔案傳輸",
        "sendBody": "從選單列或 Finder 傳送檔案或剪貼簿文字。",
        "qrTitle": "用 QR 連接",
        "qrBody": "如果裝置沒有出現，可繼續使用 QR 碼。",
        "plusTitle": "解鎖接收",
        "plusBody": "從 Mac 傳送免費。從 Android 接收需要 Pyonta+。",
    },
}

BODY_COPY_OVERRIDES = {
    "ar": {
        "receiveBody": "استقبل الصور والفيديو وملفات PDF والنصوص وغيرها من Android على Mac.",
        "sendBody": "أرسل الصور والفيديو وملفات PDF والنصوص وغيرها من Mac إلى Android.",
    },
    "bg": {
        "receiveBody": "Получавайте снимки, видео, PDF файлове, текст и други от Android на Mac.",
        "sendBody": "Изпращайте снимки, видео, PDF файлове, текст и други от Mac към Android.",
    },
    "bn": {
        "receiveBody": "Android থেকে Mac-এ ছবি, ভিডিও, PDF, লেখা ইত্যাদি নিন।",
        "sendBody": "Mac থেকে Android-এ ছবি, ভিডিও, PDF, লেখা ইত্যাদি পাঠান।",
    },
    "ca": {
        "receiveBody": "Rep fotos, vídeos, PDF, text i més d'Android al Mac.",
        "sendBody": "Envia fotos, vídeos, PDF, text i més del Mac a Android.",
    },
    "cs": {
        "receiveBody": "Přijímejte fotky, videa, PDF, text a další z Androidu na Mac.",
        "sendBody": "Posílejte fotky, videa, PDF, text a další z Macu do Androidu.",
    },
    "da": {
        "receiveBody": "Modtag fotos, videoer, PDF'er, tekst og mere fra Android på din Mac.",
        "sendBody": "Send fotos, videoer, PDF'er, tekst og mere fra Mac til Android.",
    },
    "de": {
        "receiveBody": "Empfange Fotos, Videos, PDFs, Text und mehr von Android auf deinem Mac.",
        "sendBody": "Sende Fotos, Videos, PDFs, Text und mehr von deinem Mac an Android.",
    },
    "el": {
        "receiveBody": "Λάβετε φωτογραφίες, βίντεο, PDF, κείμενο και άλλα από Android στο Mac.",
        "sendBody": "Στείλτε φωτογραφίες, βίντεο, PDF, κείμενο και άλλα από Mac σε Android.",
    },
    "en": {
        "receiveBody": "Receive photos, videos, PDFs, text, and more from Android on your Mac.",
        "sendBody": "Send photos, videos, PDFs, text, and more from your Mac to Android.",
    },
    "es": {
        "receiveBody": "Recibe fotos, videos, PDF, texto y más de Android en tu Mac.",
        "sendBody": "Envía fotos, videos, PDF, texto y más de tu Mac a Android.",
    },
    "et": {
        "receiveBody": "Võta Macis vastu fotosid, videoid, PDF-e, teksti ja muud Androidist.",
        "sendBody": "Saada fotosid, videoid, PDF-e, teksti ja muud Macist Androidi.",
    },
    "fi": {
        "receiveBody": "Vastaanota kuvia, videoita, PDF:iä, tekstiä ja muuta Androidista Maciin.",
        "sendBody": "Lähetä kuvia, videoita, PDF:iä, tekstiä ja muuta Macista Androidiin.",
    },
    "fil": {
        "receiveBody": "Tumanggap ng larawan, video, PDF, text, at iba pa mula Android sa Mac.",
        "sendBody": "Magpadala ng larawan, video, PDF, text, at iba pa mula Mac papuntang Android.",
    },
    "fr": {
        "receiveBody": "Recevez photos, vidéos, PDF, texte et plus d'Android sur votre Mac.",
        "sendBody": "Envoyez photos, vidéos, PDF, texte et plus de votre Mac vers Android.",
    },
    "he": {
        "receiveBody": "קבל תמונות, סרטונים, PDF, טקסט ועוד מ-Android ב-Mac שלך.",
        "sendBody": "שלח תמונות, סרטונים, PDF, טקסט ועוד מה-Mac ל-Android.",
    },
    "hi": {
        "receiveBody": "Android से Mac पर फ़ोटो, वीडियो, PDF, टेक्स्ट वगैरह प्राप्त करें।",
        "sendBody": "Mac से Android पर फ़ोटो, वीडियो, PDF, टेक्स्ट वगैरह भेजें।",
    },
    "hr": {
        "receiveBody": "Primajte fotografije, videozapise, PDF-ove, tekst i više s Androida na Mac.",
        "sendBody": "Šaljite fotografije, videozapise, PDF-ove, tekst i više s Maca na Android.",
    },
    "hu": {
        "receiveBody": "Fogadj fotókat, videókat, PDF-eket, szöveget és mást Androidról a Macen.",
        "sendBody": "Küldj fotókat, videókat, PDF-eket, szöveget és mást Macről Androidra.",
    },
    "id": {
        "receiveBody": "Terima foto, video, PDF, teks, dan lainnya dari Android di Mac.",
        "sendBody": "Kirim foto, video, PDF, teks, dan lainnya dari Mac ke Android.",
    },
    "it": {
        "receiveBody": "Ricevi foto, video, PDF, testo e altro da Android sul tuo Mac.",
        "sendBody": "Invia foto, video, PDF, testo e altro dal Mac ad Android.",
    },
    "ko": {
        "receiveBody": "Android의 사진, 동영상, PDF, 텍스트 등을 Mac에서 받습니다.",
        "sendBody": "Mac에서 Android로 사진, 동영상, PDF, 텍스트 등을 보냅니다.",
    },
    "lt": {
        "receiveBody": "Gaukite nuotraukas, vaizdo įrašus, PDF, tekstą ir daugiau iš Android į Mac.",
        "sendBody": "Siųskite nuotraukas, vaizdo įrašus, PDF, tekstą ir daugiau iš Mac į Android.",
    },
    "lv": {
        "receiveBody": "Saņemiet fotoattēlus, video, PDF, tekstu un citu no Android savā Mac.",
        "sendBody": "Sūtiet fotoattēlus, video, PDF, tekstu un citu no Mac uz Android.",
    },
    "ms": {
        "receiveBody": "Terima foto, video, PDF, teks dan banyak lagi daripada Android pada Mac.",
        "sendBody": "Hantar foto, video, PDF, teks dan banyak lagi daripada Mac ke Android.",
    },
    "nb": {
        "receiveBody": "Motta bilder, videoer, PDF-er, tekst og mer fra Android på Macen.",
        "sendBody": "Send bilder, videoer, PDF-er, tekst og mer fra Mac til Android.",
    },
    "nl": {
        "receiveBody": "Ontvang foto's, video's, pdf's, tekst en meer van Android op je Mac.",
        "sendBody": "Verstuur foto's, video's, pdf's, tekst en meer van je Mac naar Android.",
    },
    "pl": {
        "receiveBody": "Odbieraj na Macu zdjęcia, filmy, PDF-y, tekst i więcej z Androida.",
        "sendBody": "Wysyłaj zdjęcia, filmy, PDF-y, tekst i więcej z Maca na Androida.",
    },
    "pt-BR": {
        "receiveBody": "Receba fotos, vídeos, PDFs, texto e mais do Android no seu Mac.",
        "sendBody": "Envie fotos, vídeos, PDFs, texto e mais do Mac para Android.",
    },
    "pt-PT": {
        "receiveBody": "Receba fotografias, vídeos, PDF, texto e mais do Android no Mac.",
        "sendBody": "Envie fotografias, vídeos, PDF, texto e mais do Mac para Android.",
    },
    "ro": {
        "receiveBody": "Primește fotografii, video, PDF-uri, text și altele de pe Android pe Mac.",
        "sendBody": "Trimite fotografii, video, PDF-uri, text și altele de pe Mac pe Android.",
    },
    "ru": {
        "receiveBody": "Получайте фото, видео, PDF, текст и другое с Android на Mac.",
        "sendBody": "Отправляйте фото, видео, PDF, текст и другое с Mac на Android.",
    },
    "sk": {
        "receiveBody": "Prijímajte na Mac fotky, videá, PDF, text a ďalšie z Androidu.",
        "sendBody": "Posielajte fotky, videá, PDF, text a ďalšie z Macu do Androidu.",
    },
    "sl": {
        "receiveBody": "Na Mac prejmite fotografije, videe, PDF-je, besedilo in drugo iz Androida.",
        "sendBody": "Pošljite fotografije, videe, PDF-je, besedilo in drugo iz Maca v Android.",
    },
    "sr": {
        "receiveBody": "Примајте фотографије, видео, PDF, текст и друго са Android-а на Mac.",
        "sendBody": "Шаљите фотографије, видео, PDF, текст и друго са Mac-а на Android.",
    },
    "sv": {
        "receiveBody": "Ta emot bilder, videor, PDF:er, text och mer från Android på din Mac.",
        "sendBody": "Skicka bilder, videor, PDF:er, text och mer från Mac till Android.",
    },
    "th": {
        "receiveBody": "รับรูปภาพ วิดีโอ PDF ข้อความ และอื่นๆ จาก Android บน Mac ของคุณ",
        "sendBody": "ส่งรูปภาพ วิดีโอ PDF ข้อความ และอื่นๆ จาก Mac ไปยัง Android",
    },
    "tr": {
        "receiveBody": "Android'den Mac'inize fotoğraf, video, PDF, metin ve daha fazlasını alın.",
        "sendBody": "Mac'ten Android'e fotoğraf, video, PDF, metin ve daha fazlasını gönderin.",
    },
    "uk": {
        "receiveBody": "Отримуйте фото, відео, PDF, текст та інше з Android на Mac.",
        "sendBody": "Надсилайте фото, відео, PDF, текст та інше з Mac на Android.",
    },
    "vi": {
        "receiveBody": "Nhận ảnh, video, PDF, văn bản và nhiều nội dung khác từ Android trên Mac.",
        "sendBody": "Gửi ảnh, video, PDF, văn bản và nhiều nội dung khác từ Mac sang Android.",
    },
    "zh-Hans": {
        "receiveBody": "在 Mac 上接收来自 Android 的照片、视频、PDF、文本等。",
        "sendBody": "从 Mac 向 Android 发送照片、视频、PDF、文本等。",
    },
    "zh-Hant": {
        "receiveBody": "在 Mac 上接收來自 Android 的照片、影片、PDF、文字等。",
        "sendBody": "從 Mac 向 Android 傳送照片、影片、PDF、文字等。",
    },
}

for locale_code, values in BODY_COPY_OVERRIDES.items():
    COPY[locale_code].update(values)

STORE_COPY_OVERRIDES = {
    "ar": {"qrTitle": "إرسال عبر QR أيضًا", "qrBody": "إذا لم يظهر Android، تابع الإرسال باستخدام QR.", "plusTitle": "افتح استقبال Android"},
    "bg": {"qrTitle": "Изпращане и с QR", "qrBody": "Ако Android не се показва, продължете изпращането с QR.", "plusTitle": "Отключете получаването от Android"},
    "bn": {"qrTitle": "QR দিয়েও পাঠান", "qrBody": "Android না দেখালে QR দিয়ে পাঠানো চালিয়ে যান।", "plusTitle": "Android থেকে গ্রহণ চালু করুন"},
    "ca": {"qrTitle": "Envia també amb QR", "qrBody": "Si Android no apareix, continua enviant amb QR.", "plusTitle": "Desbloqueja la recepció d'Android"},
    "cs": {"qrTitle": "Odeslat i přes QR", "qrBody": "Když se Android nezobrazí, pokračujte v odesílání přes QR.", "plusTitle": "Odemkněte příjem z Androidu"},
    "da": {"qrTitle": "Send også med QR", "qrBody": "Hvis Android ikke vises, kan du fortsætte afsendelsen med QR.", "plusTitle": "Lås modtagelse fra Android op"},
    "de": {"qrTitle": "Auch per QR senden", "qrBody": "Wenn Android nicht erscheint, sende mit QR weiter.", "plusTitle": "Empfang von Android freischalten"},
    "el": {"qrTitle": "Αποστολή και με QR", "qrBody": "Αν το Android δεν εμφανίζεται, συνεχίστε την αποστολή με QR.", "plusTitle": "Ξεκλείδωμα λήψης από Android"},
    "en": {"qrTitle": "Send with QR too", "qrBody": "If Android does not appear, keep sending with a QR code.", "plusTitle": "Unlock receiving from Android"},
    "es": {"qrTitle": "Envía también con QR", "qrBody": "Si Android no aparece, sigue enviando con un código QR.", "plusTitle": "Desbloquea la recepción desde Android"},
    "et": {"qrTitle": "Saada ka QR-iga", "qrBody": "Kui Androidi ei kuvata, jätka saatmist QR-koodiga.", "plusTitle": "Ava vastuvõtt Androidist"},
    "fi": {"qrTitle": "Lähetä myös QR:llä", "qrBody": "Jos Android ei näy, jatka lähettämistä QR-koodilla.", "plusTitle": "Avaa vastaanotto Androidista"},
    "fil": {"qrTitle": "Magpadala rin sa QR", "qrBody": "Kung hindi lumabas ang Android, magpatuloy sa pagpapadala gamit ang QR.", "plusTitle": "I-unlock ang pagtanggap mula Android"},
    "fr": {"qrTitle": "Envoyer aussi par QR", "qrBody": "Si Android n'apparaît pas, continuez l'envoi avec un QR.", "plusTitle": "Débloquer la réception Android"},
    "he": {"qrTitle": "שלח גם עם QR", "qrBody": "אם Android לא מופיע, המשך לשלוח בעזרת QR.", "plusTitle": "פתח קבלה מ-Android"},
    "hi": {"qrTitle": "QR से भी भेजें", "qrBody": "Android न दिखे तो QR कोड से भेजना जारी रखें।", "plusTitle": "Android से प्राप्ति अनलॉक करें"},
    "hr": {"qrTitle": "Pošalji i QR-om", "qrBody": "Ako se Android ne pojavi, nastavite slanje QR kodom.", "plusTitle": "Otključajte primanje s Androida"},
    "hu": {"qrTitle": "Küldés QR-rel is", "qrBody": "Ha az Android nem jelenik meg, folytasd a küldést QR-kóddal.", "plusTitle": "Android fogadás feloldása"},
    "id": {"qrTitle": "Kirim juga dengan QR", "qrBody": "Jika Android tidak muncul, lanjutkan pengiriman dengan QR.", "plusTitle": "Buka penerimaan dari Android"},
    "it": {"qrTitle": "Invia anche con QR", "qrBody": "Se Android non appare, continua l'invio con QR.", "plusTitle": "Sblocca ricezione da Android"},
    "ko": {"qrTitle": "QR로도 보내기", "qrBody": "Android가 보이지 않으면 QR 코드로 계속 보냅니다.", "plusTitle": "Android 수신 잠금 해제"},
    "lt": {"qrTitle": "Siųsti ir QR kodu", "qrBody": "Jei Android nerodomas, siųskite toliau QR kodu.", "plusTitle": "Atrakinkite gavimą iš Android"},
    "lv": {"qrTitle": "Sūtīt arī ar QR", "qrBody": "Ja Android neparādās, turpiniet sūtīšanu ar QR.", "plusTitle": "Atbloķēt saņemšanu no Android"},
    "ms": {"qrTitle": "Hantar juga dengan QR", "qrBody": "Jika Android tidak muncul, teruskan penghantaran dengan QR.", "plusTitle": "Buka penerimaan Android"},
    "nb": {"qrTitle": "Send også med QR", "qrBody": "Hvis Android ikke vises, fortsett sendingen med QR.", "plusTitle": "Lås opp mottak fra Android"},
    "nl": {"qrTitle": "Ook met QR sturen", "qrBody": "Als Android niet verschijnt, ga door met sturen via QR.", "plusTitle": "Ontvangen van Android ontgrendelen"},
    "pl": {"qrTitle": "Wyślij też przez QR", "qrBody": "Jeśli Android się nie pojawi, wysyłaj dalej kodem QR.", "plusTitle": "Odblokuj odbiór z Androida"},
    "pt-BR": {"qrTitle": "Enviar também com QR", "qrBody": "Se o Android não aparecer, continue enviando com QR.", "plusTitle": "Desbloqueie o recebimento do Android"},
    "pt-PT": {"qrTitle": "Enviar também com QR", "qrBody": "Se o Android não aparecer, continue a enviar com QR.", "plusTitle": "Desbloquear receção do Android"},
    "ro": {"qrTitle": "Trimite și cu QR", "qrBody": "Dacă Android nu apare, continuă trimiterea cu QR.", "plusTitle": "Deblochează primirea de pe Android"},
    "ru": {"qrTitle": "Отправка и по QR", "qrBody": "Если Android не виден, продолжайте отправку по QR.", "plusTitle": "Откройте прием с Android"},
    "sk": {"qrTitle": "Odoslať aj cez QR", "qrBody": "Ak sa Android nezobrazí, pokračujte v odosielaní cez QR.", "plusTitle": "Odomknite príjem z Androidu"},
    "sl": {"qrTitle": "Pošlji tudi s QR", "qrBody": "Če se Android ne prikaže, nadaljujte pošiljanje s QR.", "plusTitle": "Odklenite prejemanje iz Androida"},
    "sr": {"qrTitle": "Пошаљи и QR-ом", "qrBody": "Ако се Android не појави, наставите слање QR кодом.", "plusTitle": "Откључајте пријем са Android-а"},
    "sv": {"qrTitle": "Skicka även med QR", "qrBody": "Om Android inte visas kan du fortsätta skicka med QR.", "plusTitle": "Lås upp mottagning från Android"},
    "th": {"qrTitle": "ส่งด้วย QR ได้ด้วย", "qrBody": "หาก Android ไม่แสดง ให้ส่งต่อด้วยรหัส QR", "plusTitle": "ปลดล็อกการรับจาก Android"},
    "tr": {"qrTitle": "QR ile de gönder", "qrBody": "Android görünmezse QR koduyla göndermeye devam edin.", "plusTitle": "Android'den almayı aç"},
    "uk": {"qrTitle": "Надіслати й через QR", "qrBody": "Якщо Android не з'являється, надсилайте далі через QR.", "plusTitle": "Розблокуйте отримання з Android"},
    "vi": {"qrTitle": "Gửi cả bằng QR", "qrBody": "Nếu Android không xuất hiện, hãy tiếp tục gửi bằng QR.", "plusTitle": "Mở khóa nhận từ Android"},
    "zh-Hans": {"qrTitle": "也可用 QR 发送", "qrBody": "如果 Android 未出现，可继续用 QR 发送。", "plusTitle": "解锁来自 Android 的接收"},
    "zh-Hant": {"qrTitle": "也可用 QR 傳送", "qrBody": "如果 Android 未出現，可繼續用 QR 傳送。", "plusTitle": "解鎖來自 Android 的接收"},
}

for locale_code, values in STORE_COPY_OVERRIDES.items():
    COPY[locale_code].update(values)

MOCK_COPY = {
    "en": {
        "macReceiveTitle": "Receive files",
        "macReceiveSubtitle": "Downloads",
        "macSendTitle": "Send files",
        "macSendSubtitle": "Finder / Clipboard",
        "receiveAction": "Receive files",
        "sendAction": "Send files",
        "share": "Share",
        "receiving": "Receiving",
        "photos": "Photos",
        "videos": "Videos",
        "pdf": "PDF",
        "text": "Text",
        "quickShare": "Quick Share",
        "ready": "Ready to receive",
        "autoDiscovery": "Auto discovery",
        "planMonthly": "Monthly",
        "planYearly": "Yearly trial",
        "planLifetime": "Lifetime",
        "paidReceiveAction": "Receive with Pyonta+",
    },
    "ja": {
        "macReceiveTitle": "ファイル受信",
        "macReceiveSubtitle": "ダウンロード",
        "macSendTitle": "ファイル送信",
        "macSendSubtitle": "Finder / クリップボード",
        "receiveAction": "受信する",
        "sendAction": "送信する",
        "share": "共有",
        "receiving": "受信中",
        "photos": "写真",
        "videos": "動画",
        "pdf": "PDF",
        "text": "テキスト",
        "quickShare": "Quick Share",
        "ready": "受信準備OK",
        "autoDiscovery": "自動で見つかる",
        "planMonthly": "月額",
        "planYearly": "年額",
        "planLifetime": "買い切り",
        "paidReceiveAction": "Pyonta+で受信",
    },
}

MOCK_COPY.update({
    "ar": {"macReceiveSubtitle": "التنزيلات", "macSendTitle": "إرسال ملفات", "macSendSubtitle": "Finder / الحافظة", "receiveAction": "استلام", "sendAction": "إرسال", "share": "مشاركة", "receiving": "جارٍ الاستلام", "photos": "صور", "videos": "فيديو", "text": "نص", "ready": "جاهز للاستلام"},
    "bg": {"macReceiveSubtitle": "Изтегляния", "macSendTitle": "Изпращане", "macSendSubtitle": "Finder / клипборд", "receiveAction": "Получаване", "sendAction": "Изпращане", "share": "Споделяне", "receiving": "Получаване", "photos": "Снимки", "videos": "Видео", "text": "Текст", "ready": "Готово"},
    "bn": {"macReceiveSubtitle": "ডাউনলোড", "macSendTitle": "ফাইল পাঠান", "macSendSubtitle": "Finder / ক্লিপবোর্ড", "receiveAction": "গ্রহণ", "sendAction": "পাঠান", "share": "শেয়ার", "receiving": "গ্রহণ হচ্ছে", "photos": "ছবি", "videos": "ভিডিও", "text": "টেক্সট", "ready": "প্রস্তুত"},
    "ca": {"macReceiveSubtitle": "Baixades", "macSendTitle": "Envia fitxers", "macSendSubtitle": "Finder / porta-retalls", "receiveAction": "Rebre", "sendAction": "Enviar", "share": "Comparteix", "receiving": "Rebent", "photos": "Fotos", "videos": "Vídeos", "text": "Text", "ready": "A punt"},
    "cs": {"macReceiveSubtitle": "Stahování", "macSendTitle": "Odeslat soubory", "macSendSubtitle": "Finder / schránka", "receiveAction": "Přijmout", "sendAction": "Odeslat", "share": "Sdílet", "receiving": "Příjem", "photos": "Fotky", "videos": "Videa", "text": "Text", "ready": "Připraveno"},
    "da": {"macReceiveSubtitle": "Overførsler", "macSendTitle": "Send filer", "macSendSubtitle": "Finder / udklip", "receiveAction": "Modtag", "sendAction": "Send", "share": "Del", "receiving": "Modtager", "photos": "Fotos", "videos": "Videoer", "text": "Tekst", "ready": "Klar"},
    "de": {"macReceiveSubtitle": "Downloads", "macSendTitle": "Dateien senden", "macSendSubtitle": "Finder / Zwischenablage", "receiveAction": "Empfangen", "sendAction": "Senden", "share": "Teilen", "receiving": "Empfang", "photos": "Fotos", "videos": "Videos", "text": "Text", "ready": "Bereit"},
    "el": {"macReceiveSubtitle": "Λήψεις", "macSendTitle": "Αποστολή αρχείων", "macSendSubtitle": "Finder / πρόχειρο", "receiveAction": "Λήψη", "sendAction": "Αποστολή", "share": "Κοινή χρήση", "receiving": "Λήψη", "photos": "Φωτογραφίες", "videos": "Βίντεο", "text": "Κείμενο", "ready": "Έτοιμο"},
    "es": {"macReceiveSubtitle": "Descargas", "macSendTitle": "Enviar archivos", "macSendSubtitle": "Finder / portapapeles", "receiveAction": "Recibir", "sendAction": "Enviar", "share": "Compartir", "receiving": "Recibiendo", "photos": "Fotos", "videos": "Videos", "text": "Texto", "ready": "Listo"},
    "et": {"macReceiveSubtitle": "Allalaadimised", "macSendTitle": "Saada failid", "macSendSubtitle": "Finder / lõikelaud", "receiveAction": "Võta vastu", "sendAction": "Saada", "share": "Jaga", "receiving": "Vastuvõtt", "photos": "Fotod", "videos": "Videod", "text": "Tekst", "ready": "Valmis"},
    "fi": {"macReceiveSubtitle": "Lataukset", "macSendTitle": "Lähetä tiedostot", "macSendSubtitle": "Finder / leikepöytä", "receiveAction": "Vastaanota", "sendAction": "Lähetä", "share": "Jaa", "receiving": "Vastaanotto", "photos": "Kuvat", "videos": "Videot", "text": "Teksti", "ready": "Valmis"},
    "fil": {"macReceiveSubtitle": "Downloads", "macSendTitle": "Magpadala", "macSendSubtitle": "Finder / clipboard", "receiveAction": "Tumanggap", "sendAction": "Ipadala", "share": "Ibahagi", "receiving": "Tumatanggap", "photos": "Larawan", "videos": "Video", "text": "Text", "ready": "Handa"},
    "fr": {"macReceiveSubtitle": "Téléchargements", "macSendTitle": "Envoyer fichiers", "macSendSubtitle": "Finder / presse-papiers", "receiveAction": "Recevoir", "sendAction": "Envoyer", "share": "Partager", "receiving": "Réception", "photos": "Photos", "videos": "Vidéos", "text": "Texte", "ready": "Prêt"},
    "he": {"macReceiveSubtitle": "הורדות", "macSendTitle": "שליחת קבצים", "macSendSubtitle": "Finder / לוח", "receiveAction": "קבל", "sendAction": "שלח", "share": "שיתוף", "receiving": "מקבל", "photos": "תמונות", "videos": "וידאו", "text": "טקסט", "ready": "מוכן"},
    "hi": {"macReceiveSubtitle": "डाउनलोड", "macSendTitle": "फ़ाइलें भेजें", "macSendSubtitle": "Finder / क्लिपबोर्ड", "receiveAction": "प्राप्त करें", "sendAction": "भेजें", "share": "शेयर", "receiving": "प्राप्त हो रहा", "photos": "फ़ोटो", "videos": "वीडियो", "text": "टेक्स्ट", "ready": "तैयार"},
    "hr": {"macReceiveSubtitle": "Preuzimanja", "macSendTitle": "Pošalji datoteke", "macSendSubtitle": "Finder / međuspremnik", "receiveAction": "Primi", "sendAction": "Pošalji", "share": "Dijeli", "receiving": "Primanje", "photos": "Fotografije", "videos": "Video", "text": "Tekst", "ready": "Spremno"},
    "hu": {"macReceiveSubtitle": "Letöltések", "macSendTitle": "Fájlok küldése", "macSendSubtitle": "Finder / vágólap", "receiveAction": "Fogadás", "sendAction": "Küldés", "share": "Megosztás", "receiving": "Fogadás", "photos": "Fotók", "videos": "Videók", "text": "Szöveg", "ready": "Kész"},
    "id": {"macReceiveSubtitle": "Unduhan", "macSendTitle": "Kirim file", "macSendSubtitle": "Finder / papan klip", "receiveAction": "Terima", "sendAction": "Kirim", "share": "Bagikan", "receiving": "Menerima", "photos": "Foto", "videos": "Video", "text": "Teks", "ready": "Siap"},
    "it": {"macReceiveSubtitle": "Download", "macSendTitle": "Invia file", "macSendSubtitle": "Finder / appunti", "receiveAction": "Ricevi", "sendAction": "Invia", "share": "Condividi", "receiving": "Ricezione", "photos": "Foto", "videos": "Video", "text": "Testo", "ready": "Pronto"},
    "ko": {"macReceiveSubtitle": "다운로드", "macSendTitle": "파일 보내기", "macSendSubtitle": "Finder / 클립보드", "receiveAction": "받기", "sendAction": "보내기", "share": "공유", "receiving": "수신 중", "photos": "사진", "videos": "동영상", "text": "텍스트", "ready": "준비됨"},
    "lt": {"macReceiveSubtitle": "Atsisiuntimai", "macSendTitle": "Siųsti failus", "macSendSubtitle": "Finder / iškarpinė", "receiveAction": "Gauti", "sendAction": "Siųsti", "share": "Bendrinti", "receiving": "Gaunama", "photos": "Nuotraukos", "videos": "Vaizdo įr.", "text": "Tekstas", "ready": "Paruošta"},
    "lv": {"macReceiveSubtitle": "Lejupielādes", "macSendTitle": "Sūtīt failus", "macSendSubtitle": "Finder / starpliktuve", "receiveAction": "Saņemt", "sendAction": "Sūtīt", "share": "Kopīgot", "receiving": "Saņem", "photos": "Foto", "videos": "Video", "text": "Teksts", "ready": "Gatavs"},
    "ms": {"macReceiveSubtitle": "Muat turun", "macSendTitle": "Hantar fail", "macSendSubtitle": "Finder / papan klip", "receiveAction": "Terima", "sendAction": "Hantar", "share": "Kongsi", "receiving": "Menerima", "photos": "Foto", "videos": "Video", "text": "Teks", "ready": "Sedia"},
    "nb": {"macReceiveSubtitle": "Nedlastinger", "macSendTitle": "Send filer", "macSendSubtitle": "Finder / utklipp", "receiveAction": "Motta", "sendAction": "Send", "share": "Del", "receiving": "Mottar", "photos": "Bilder", "videos": "Videoer", "text": "Tekst", "ready": "Klar"},
    "nl": {"macReceiveSubtitle": "Downloads", "macSendTitle": "Bestanden sturen", "macSendSubtitle": "Finder / klembord", "receiveAction": "Ontvangen", "sendAction": "Versturen", "share": "Delen", "receiving": "Ontvangen", "photos": "Foto's", "videos": "Video's", "text": "Tekst", "ready": "Gereed"},
    "pl": {"macReceiveSubtitle": "Pobrane", "macSendTitle": "Wyślij pliki", "macSendSubtitle": "Finder / schowek", "receiveAction": "Odbierz", "sendAction": "Wyślij", "share": "Udostępnij", "receiving": "Odbieranie", "photos": "Zdjęcia", "videos": "Filmy", "text": "Tekst", "ready": "Gotowe"},
    "pt-BR": {"macReceiveSubtitle": "Downloads", "macSendTitle": "Enviar arquivos", "macSendSubtitle": "Finder / área de transferência", "receiveAction": "Receber", "sendAction": "Enviar", "share": "Compartilhar", "receiving": "Recebendo", "photos": "Fotos", "videos": "Vídeos", "text": "Texto", "ready": "Pronto"},
    "pt-PT": {"macReceiveSubtitle": "Descargas", "macSendTitle": "Enviar ficheiros", "macSendSubtitle": "Finder / área de transferência", "receiveAction": "Receber", "sendAction": "Enviar", "share": "Partilhar", "receiving": "A receber", "photos": "Fotos", "videos": "Vídeos", "text": "Texto", "ready": "Pronto"},
    "ro": {"macReceiveSubtitle": "Descărcări", "macSendTitle": "Trimite fișiere", "macSendSubtitle": "Finder / clipboard", "receiveAction": "Primește", "sendAction": "Trimite", "share": "Partajare", "receiving": "Se primește", "photos": "Fotografii", "videos": "Video", "text": "Text", "ready": "Gata"},
    "ru": {"macReceiveSubtitle": "Загрузки", "macSendTitle": "Отправить файлы", "macSendSubtitle": "Finder / буфер", "receiveAction": "Получить", "sendAction": "Отправить", "share": "Поделиться", "receiving": "Прием", "photos": "Фото", "videos": "Видео", "text": "Текст", "ready": "Готово"},
    "sk": {"macReceiveSubtitle": "Stiahnuté", "macSendTitle": "Odoslať súbory", "macSendSubtitle": "Finder / schránka", "receiveAction": "Prijať", "sendAction": "Odoslať", "share": "Zdieľať", "receiving": "Príjem", "photos": "Fotky", "videos": "Videá", "text": "Text", "ready": "Pripravené"},
    "sl": {"macReceiveSubtitle": "Prenosi", "macSendTitle": "Pošlji datoteke", "macSendSubtitle": "Finder / odložišče", "receiveAction": "Prejmi", "sendAction": "Pošlji", "share": "Deli", "receiving": "Prejemanje", "photos": "Fotografije", "videos": "Videi", "text": "Besedilo", "ready": "Pripravljeno"},
    "sr": {"macReceiveSubtitle": "Преузимања", "macSendTitle": "Пошаљи датотеке", "macSendSubtitle": "Finder / клипборд", "receiveAction": "Прими", "sendAction": "Пошаљи", "share": "Дели", "receiving": "Пријем", "photos": "Фотографије", "videos": "Видео", "text": "Текст", "ready": "Спремно"},
    "sv": {"macReceiveSubtitle": "Hämtade filer", "macSendTitle": "Skicka filer", "macSendSubtitle": "Finder / urklipp", "receiveAction": "Ta emot", "sendAction": "Skicka", "share": "Dela", "receiving": "Tar emot", "photos": "Bilder", "videos": "Videor", "text": "Text", "ready": "Klar"},
    "th": {"macReceiveSubtitle": "ดาวน์โหลด", "macSendTitle": "ส่งไฟล์", "macSendSubtitle": "Finder / คลิปบอร์ด", "receiveAction": "รับ", "sendAction": "ส่ง", "share": "แชร์", "receiving": "กำลังรับ", "photos": "รูปภาพ", "videos": "วิดีโอ", "text": "ข้อความ", "ready": "พร้อมรับ"},
    "tr": {"macReceiveSubtitle": "İndirilenler", "macSendTitle": "Dosya gönder", "macSendSubtitle": "Finder / pano", "receiveAction": "Al", "sendAction": "Gönder", "share": "Paylaş", "receiving": "Alınıyor", "photos": "Fotoğraflar", "videos": "Videolar", "text": "Metin", "ready": "Hazır"},
    "uk": {"macReceiveSubtitle": "Завантаження", "macSendTitle": "Надіслати файли", "macSendSubtitle": "Finder / буфер", "receiveAction": "Отримати", "sendAction": "Надіслати", "share": "Поділитися", "receiving": "Отримання", "photos": "Фото", "videos": "Відео", "text": "Текст", "ready": "Готово"},
    "vi": {"macReceiveSubtitle": "Tải xuống", "macSendTitle": "Gửi tệp", "macSendSubtitle": "Finder / bảng nhớ tạm", "receiveAction": "Nhận", "sendAction": "Gửi", "share": "Chia sẻ", "receiving": "Đang nhận", "photos": "Ảnh", "videos": "Video", "text": "Văn bản", "ready": "Sẵn sàng"},
    "zh-Hans": {"macReceiveSubtitle": "下载", "macSendTitle": "发送文件", "macSendSubtitle": "Finder / 剪贴板", "receiveAction": "接收", "sendAction": "发送", "share": "共享", "receiving": "正在接收", "photos": "照片", "videos": "视频", "text": "文本", "ready": "准备接收"},
    "zh-Hant": {"macReceiveSubtitle": "下載", "macSendTitle": "傳送檔案", "macSendSubtitle": "Finder / 剪貼簿", "receiveAction": "接收", "sendAction": "傳送", "share": "分享", "receiving": "正在接收", "photos": "照片", "videos": "影片", "text": "文字", "ready": "準備接收"},
})

MOCK_TITLE_COPY = {
    "ar": {"macReceiveTitle": "استلام ملفات", "macSendTitle": "إرسال ملفات"},
    "bg": {"macReceiveTitle": "Получаване на файлове", "macSendTitle": "Изпращане на файлове"},
    "bn": {"macReceiveTitle": "ফাইল গ্রহণ", "macSendTitle": "ফাইল পাঠান"},
    "ca": {"macReceiveTitle": "Rep fitxers", "macSendTitle": "Envia fitxers"},
    "cs": {"macReceiveTitle": "Přijmout soubory", "macSendTitle": "Odeslat soubory"},
    "da": {"macReceiveTitle": "Modtag filer", "macSendTitle": "Send filer"},
    "de": {"macReceiveTitle": "Dateien empfangen", "macSendTitle": "Dateien senden"},
    "el": {"macReceiveTitle": "Λήψη αρχείων", "macSendTitle": "Αποστολή αρχείων"},
    "es": {"macReceiveTitle": "Recibir archivos", "macSendTitle": "Enviar archivos"},
    "et": {"macReceiveTitle": "Võta failid vastu", "macSendTitle": "Saada failid"},
    "fi": {"macReceiveTitle": "Vastaanota tiedostot", "macSendTitle": "Lähetä tiedostot"},
    "fil": {"macReceiveTitle": "Tumanggap ng file", "macSendTitle": "Magpadala ng file"},
    "fr": {"macReceiveTitle": "Recevoir fichiers", "macSendTitle": "Envoyer fichiers"},
    "he": {"macReceiveTitle": "קבלת קבצים", "macSendTitle": "שליחת קבצים"},
    "hi": {"macReceiveTitle": "फ़ाइलें प्राप्त करें", "macSendTitle": "फ़ाइलें भेजें"},
    "hr": {"macReceiveTitle": "Primi datoteke", "macSendTitle": "Pošalji datoteke"},
    "hu": {"macReceiveTitle": "Fájlok fogadása", "macSendTitle": "Fájlok küldése"},
    "id": {"macReceiveTitle": "Terima file", "macSendTitle": "Kirim file"},
    "it": {"macReceiveTitle": "Ricevi file", "macSendTitle": "Invia file"},
    "ko": {"macReceiveTitle": "파일 받기", "macSendTitle": "파일 보내기"},
    "lt": {"macReceiveTitle": "Gauti failus", "macSendTitle": "Siųsti failus"},
    "lv": {"macReceiveTitle": "Saņemt failus", "macSendTitle": "Sūtīt failus"},
    "ms": {"macReceiveTitle": "Terima fail", "macSendTitle": "Hantar fail"},
    "nb": {"macReceiveTitle": "Motta filer", "macSendTitle": "Send filer"},
    "nl": {"macReceiveTitle": "Bestanden ontvangen", "macSendTitle": "Bestanden sturen"},
    "pl": {"macReceiveTitle": "Odbierz pliki", "macSendTitle": "Wyślij pliki"},
    "pt-BR": {"macReceiveTitle": "Receber arquivos", "macSendTitle": "Enviar arquivos"},
    "pt-PT": {"macReceiveTitle": "Receber ficheiros", "macSendTitle": "Enviar ficheiros"},
    "ro": {"macReceiveTitle": "Primește fișiere", "macSendTitle": "Trimite fișiere"},
    "ru": {"macReceiveTitle": "Получить файлы", "macSendTitle": "Отправить файлы"},
    "sk": {"macReceiveTitle": "Prijať súbory", "macSendTitle": "Odoslať súbory"},
    "sl": {"macReceiveTitle": "Prejmi datoteke", "macSendTitle": "Pošlji datoteke"},
    "sr": {"macReceiveTitle": "Прими датотеке", "macSendTitle": "Пошаљи датотеке"},
    "sv": {"macReceiveTitle": "Ta emot filer", "macSendTitle": "Skicka filer"},
    "th": {"macReceiveTitle": "รับไฟล์", "macSendTitle": "ส่งไฟล์"},
    "tr": {"macReceiveTitle": "Dosya al", "macSendTitle": "Dosya gönder"},
    "uk": {"macReceiveTitle": "Отримати файли", "macSendTitle": "Надіслати файли"},
    "vi": {"macReceiveTitle": "Nhận tệp", "macSendTitle": "Gửi tệp"},
    "zh-Hans": {"macReceiveTitle": "接收文件", "macSendTitle": "发送文件"},
    "zh-Hant": {"macReceiveTitle": "接收檔案", "macSendTitle": "傳送檔案"},
}

for locale_code, values in MOCK_TITLE_COPY.items():
    MOCK_COPY.setdefault(locale_code, {}).update(values)

MOCK_COPY_EXTRAS = {
    "ar": {"autoDiscovery": "اكتشاف تلقائي", "paidReceiveAction": "استلام عبر Pyonta+", "planMonthly": "شهري", "planYearly": "سنوي", "planLifetime": "مدى الحياة"},
    "bg": {"autoDiscovery": "Автооткриване", "paidReceiveAction": "С Pyonta+", "planMonthly": "Месечно", "planYearly": "Годишно", "planLifetime": "Доживотно"},
    "bn": {"autoDiscovery": "স্বয়ংক্রিয় খোঁজ", "paidReceiveAction": "Pyonta+ দিয়ে নিন", "planMonthly": "মাসিক", "planYearly": "বার্ষিক", "planLifetime": "আজীবন"},
    "ca": {"autoDiscovery": "Detectat sol", "paidReceiveAction": "Rep amb Pyonta+", "planMonthly": "Mensual", "planYearly": "Anual", "planLifetime": "De per vida"},
    "cs": {"autoDiscovery": "Automaticky", "paidReceiveAction": "Přijmout s Pyonta+", "planMonthly": "Měsíčně", "planYearly": "Ročně", "planLifetime": "Navždy"},
    "da": {"autoDiscovery": "Auto fundet", "paidReceiveAction": "Modtag med Pyonta+", "planMonthly": "Måned", "planYearly": "År", "planLifetime": "Livstid"},
    "de": {"autoDiscovery": "Automatisch", "paidReceiveAction": "Mit Pyonta+ empfangen", "planMonthly": "Monatlich", "planYearly": "Jährlich", "planLifetime": "Einmalig"},
    "el": {"autoDiscovery": "Αυτόματη εύρεση", "paidReceiveAction": "Λήψη με Pyonta+", "planMonthly": "Μηνιαίο", "planYearly": "Ετήσιο", "planLifetime": "Εφάπαξ"},
    "es": {"autoDiscovery": "Detección auto", "paidReceiveAction": "Recibir con Pyonta+", "planMonthly": "Mensual", "planYearly": "Anual", "planLifetime": "De por vida"},
    "et": {"autoDiscovery": "Leiab ise", "paidReceiveAction": "Võta vastu Pyonta+", "planMonthly": "Kuu", "planYearly": "Aasta", "planLifetime": "Eluaegne"},
    "fi": {"autoDiscovery": "Löytyy itse", "paidReceiveAction": "Vastaanota Pyonta+", "planMonthly": "Kuukausi", "planYearly": "Vuosi", "planLifetime": "Pysyvä"},
    "fil": {"autoDiscovery": "Auto hanap", "paidReceiveAction": "Tumanggap sa Pyonta+", "planMonthly": "Buwan", "planYearly": "Taon", "planLifetime": "Habambuhay"},
    "fr": {"autoDiscovery": "Détection auto", "paidReceiveAction": "Recevoir avec Pyonta+", "planMonthly": "Mensuel", "planYearly": "Annuel", "planLifetime": "À vie"},
    "he": {"autoDiscovery": "זיהוי אוטומטי", "paidReceiveAction": "קבל עם Pyonta+", "planMonthly": "חודשי", "planYearly": "שנתי", "planLifetime": "לכל החיים"},
    "hi": {"autoDiscovery": "अपने-आप मिला", "paidReceiveAction": "Pyonta+ से पाएं", "planMonthly": "मासिक", "planYearly": "वार्षिक", "planLifetime": "आजीवन"},
    "hr": {"autoDiscovery": "Automatski", "paidReceiveAction": "Primi uz Pyonta+", "planMonthly": "Mjesečno", "planYearly": "Godišnje", "planLifetime": "Doživotno"},
    "hu": {"autoDiscovery": "Automatikus", "paidReceiveAction": "Fogadás Pyonta+", "planMonthly": "Havi", "planYearly": "Éves", "planLifetime": "Örök"},
    "id": {"autoDiscovery": "Terdeteksi", "paidReceiveAction": "Terima dengan Pyonta+", "planMonthly": "Bulanan", "planYearly": "Tahunan", "planLifetime": "Seumur hidup"},
    "it": {"autoDiscovery": "Rilevamento auto", "paidReceiveAction": "Ricevi con Pyonta+", "planMonthly": "Mensile", "planYearly": "Annuale", "planLifetime": "A vita"},
    "ko": {"autoDiscovery": "자동 발견", "paidReceiveAction": "Pyonta+로 받기", "planMonthly": "월간", "planYearly": "연간", "planLifetime": "평생"},
    "lt": {"autoDiscovery": "Randa pats", "paidReceiveAction": "Gauti su Pyonta+", "planMonthly": "Mėnesio", "planYearly": "Metų", "planLifetime": "Visam laikui"},
    "lv": {"autoDiscovery": "Atrod autom.", "paidReceiveAction": "Saņemt ar Pyonta+", "planMonthly": "Mēnesī", "planYearly": "Gadā", "planLifetime": "Mūža"},
    "ms": {"autoDiscovery": "Auto jumpa", "paidReceiveAction": "Terima dengan Pyonta+", "planMonthly": "Bulanan", "planYearly": "Tahunan", "planLifetime": "Seumur hidup"},
    "nb": {"autoDiscovery": "Finnes auto", "paidReceiveAction": "Motta med Pyonta+", "planMonthly": "Månedlig", "planYearly": "Årlig", "planLifetime": "Livstid"},
    "nl": {"autoDiscovery": "Automatisch", "paidReceiveAction": "Ontvang met Pyonta+", "planMonthly": "Maandelijks", "planYearly": "Jaarlijks", "planLifetime": "Levenslang"},
    "pl": {"autoDiscovery": "Wykrywa samo", "paidReceiveAction": "Odbierz z Pyonta+", "planMonthly": "Miesięcznie", "planYearly": "Rocznie", "planLifetime": "Dożywotnio"},
    "pt-BR": {"autoDiscovery": "Detecção auto", "paidReceiveAction": "Receber com Pyonta+", "planMonthly": "Mensal", "planYearly": "Anual", "planLifetime": "Vitalício"},
    "pt-PT": {"autoDiscovery": "Deteção auto", "paidReceiveAction": "Receber com Pyonta+", "planMonthly": "Mensal", "planYearly": "Anual", "planLifetime": "Vitalício"},
    "ro": {"autoDiscovery": "Detectare auto", "paidReceiveAction": "Primește cu Pyonta+", "planMonthly": "Lunar", "planYearly": "Anual", "planLifetime": "Pe viață"},
    "ru": {"autoDiscovery": "Автопоиск", "paidReceiveAction": "Получить с Pyonta+", "planMonthly": "Месяц", "planYearly": "Год", "planLifetime": "Навсегда"},
    "sk": {"autoDiscovery": "Nájde samo", "paidReceiveAction": "Prijať s Pyonta+", "planMonthly": "Mesačne", "planYearly": "Ročne", "planLifetime": "Navždy"},
    "sl": {"autoDiscovery": "Samodejno", "paidReceiveAction": "Prejmi s Pyonta+", "planMonthly": "Mesečno", "planYearly": "Letno", "planLifetime": "Za vedno"},
    "sr": {"autoDiscovery": "Аутоматски", "paidReceiveAction": "Прими уз Pyonta+", "planMonthly": "Месечно", "planYearly": "Годишње", "planLifetime": "Заувек"},
    "sv": {"autoDiscovery": "Hittas auto", "paidReceiveAction": "Ta emot med Pyonta+", "planMonthly": "Månad", "planYearly": "År", "planLifetime": "Livstid"},
    "th": {"autoDiscovery": "พบอัตโนมัติ", "paidReceiveAction": "รับด้วย Pyonta+", "planMonthly": "รายเดือน", "planYearly": "รายปี", "planLifetime": "ตลอดชีพ"},
    "tr": {"autoDiscovery": "Otomatik bulur", "paidReceiveAction": "Pyonta+ ile al", "planMonthly": "Aylık", "planYearly": "Yıllık", "planLifetime": "Ömür boyu"},
    "uk": {"autoDiscovery": "Автопошук", "paidReceiveAction": "Отримати з Pyonta+", "planMonthly": "Місяць", "planYearly": "Рік", "planLifetime": "Назавжди"},
    "vi": {"autoDiscovery": "Tự tìm thấy", "paidReceiveAction": "Nhận bằng Pyonta+", "planMonthly": "Hàng tháng", "planYearly": "Hàng năm", "planLifetime": "Trọn đời"},
    "zh-Hans": {"autoDiscovery": "自动发现", "paidReceiveAction": "用 Pyonta+ 接收", "planMonthly": "月度", "planYearly": "年度", "planLifetime": "终身"},
    "zh-Hant": {"autoDiscovery": "自動發現", "paidReceiveAction": "用 Pyonta+ 接收", "planMonthly": "月付", "planYearly": "年付", "planLifetime": "終身"},
}

for locale_code, values in MOCK_COPY_EXTRAS.items():
    MOCK_COPY.setdefault(locale_code, {}).update(values)


SCRIPT_FONT = {
    "ar": "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
    "bn": "/System/Library/Fonts/KohinoorBangla.ttc",
    "he": "/System/Library/Fonts/SFHebrew.ttf",
    "hi": "/Library/Fonts/RODE Noto Sans Hindi R.ttf",
    "ja": "/Library/Fonts/RODE Noto Sans CJK SC R.otf",
    "ko": "/Library/Fonts/RODE Noto Sans CJK SC R.otf",
    "th": "/System/Library/Fonts/ThonburiUI.ttc",
    "zh-Hans": "/Library/Fonts/RODE Noto Sans CJK SC R.otf",
    "zh-Hant": "/Library/Fonts/RODE Noto Sans CJK SC R.otf",
}

SCRIPT_BOLD_FONT = {
    "ar": "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
    "bn": "/System/Library/Fonts/KohinoorBangla.ttc",
    "he": "/System/Library/Fonts/SFHebrew.ttf",
    "hi": "/Library/Fonts/RODE Noto Sans Hindi B.ttf",
    "ja": "/Library/Fonts/RODE Noto Sans CJK SC B.otf",
    "ko": "/Library/Fonts/RODE Noto Sans CJK SC B.otf",
    "th": "/System/Library/Fonts/ThonburiUI.ttc",
    "zh-Hans": "/Library/Fonts/RODE Noto Sans CJK SC B.otf",
    "zh-Hant": "/Library/Fonts/RODE Noto Sans CJK SC B.otf",
}

UNIVERSAL_FONT = Path("/System/Library/Fonts/Supplemental/Arial Unicode.ttf")
GENERAL_FONT_REG = Path("/System/Library/Fonts/Supplemental/Arial.ttf")
GENERAL_FONT_BOLD = Path("/System/Library/Fonts/Supplemental/Arial Bold.ttf")


def rtl_safe_text(locale: str, text: str) -> str:
    if locale in rtl_locale_codes():
        return text.replace("Pyonta+", "\u2066Pyonta+\u2069")
    return text


def copy(locale: str, key: str) -> str:
    return rtl_safe_text(locale, COPY[locale][key])


def mock_copy(locale: str, key: str) -> str:
    return rtl_safe_text(locale, MOCK_COPY.get(locale, {}).get(key, MOCK_COPY["en"][key]))


def local_font(locale: str, size: int, weight: str = "regular") -> ImageFont.FreeTypeFont:
    font_map = SCRIPT_BOLD_FONT if weight in ("bold", "medium") else SCRIPT_FONT
    path = Path(font_map.get(locale, ""))
    if path.exists():
        try:
            return ImageFont.truetype(str(path), size)
        except OSError:
            pass
    general = GENERAL_FONT_BOLD if weight in ("bold", "medium") else GENERAL_FONT_REG
    if general.exists():
        try:
            return ImageFont.truetype(str(general), size)
        except OSError:
            pass
    if UNIVERSAL_FONT.exists():
        return ImageFont.truetype(str(UNIVERSAL_FONT), size)
    return g.font(size, weight)


def use_core_text(locale: str) -> bool:
    return locale in CORE_TEXT_LOCALES and CORE_TEXT_SCRIPT.exists()


def needs_shaped_text(locale: str) -> bool:
    return locale in SHAPED_TEXT_LOCALES and CORE_TEXT_SCRIPT.exists()


def core_text_env() -> dict[str, str]:
    env = os.environ.copy()
    cache_dir = Path(tempfile.gettempdir()) / "pyonta-swift-module-cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    env["CLANG_MODULE_CACHE_PATH"] = str(cache_dir)
    return env


def ensure_core_text_binary(env: dict[str, str]) -> Path:
    if (
        not CORE_TEXT_BINARY.exists()
        or CORE_TEXT_BINARY.stat().st_mtime < CORE_TEXT_SCRIPT.stat().st_mtime
    ):
        subprocess.run(
            ["swiftc", str(CORE_TEXT_SCRIPT), "-o", str(CORE_TEXT_BINARY)],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
        )
    return CORE_TEXT_BINARY


def paste_core_text(
    img: Image.Image,
    xy: tuple[int, int],
    text: str,
    *,
    width: int,
    font_size: int,
    weight: str,
    fill: str,
    line_gap: int,
    rtl: bool,
    alignment: str = "natural",
) -> int:
    x, y = xy
    env = core_text_env()
    renderer = ensure_core_text_binary(env)
    with tempfile.TemporaryDirectory(prefix="pyonta-coretext-") as tmp:
        tmp_dir = Path(tmp)
        text_file = tmp_dir / "text.txt"
        output = tmp_dir / "text.png"
        text_file.write_text(text, encoding="utf-8")
        subprocess.run(
            [
                str(renderer),
                "--text-file",
                str(text_file),
                "--output",
                str(output),
                "--width",
                str(width),
                "--font-size",
                str(font_size),
                "--weight",
                weight,
                "--color",
                fill,
                "--line-spacing",
                str(line_gap),
                "--rtl",
                "1" if rtl else "0",
                "--alignment",
                alignment,
            ],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
        )
        rendered = Image.open(output).convert("RGBA")
        img.alpha_composite(rendered, (x, y))
        return y + rendered.height


def text_size(draw: ImageDraw.ImageDraw, text: str, fnt: ImageFont.FreeTypeFont) -> tuple[int, int]:
    box = draw.textbbox((0, 0), text, font=fnt)
    return box[2] - box[0], box[3] - box[1]


def wrapped_lines(draw: ImageDraw.ImageDraw, text: str, fnt: ImageFont.FreeTypeFont, max_width: int) -> list[str]:
    return g.wrap(draw, text, fnt, max_width)


def draw_text(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int],
    text: str,
    fnt: ImageFont.FreeTypeFont,
    fill: str,
    max_width: int,
    line_gap: int = 16,
) -> int:
    x, y = xy
    for line in wrapped_lines(draw, text, fnt, max_width):
        draw.text((x, y), line, font=fnt, fill=fill)
        y += text_size(draw, line or "A", fnt)[1] + line_gap
    return y


def draw_headline(
    img: Image.Image,
    draw: ImageDraw.ImageDraw,
    locale: str,
    xy: tuple[int, int],
    title: str,
    max_width: int,
) -> int:
    if "\n" in title and not use_core_text(locale):
        route, action = title.split("\n", 1)
        x, y = xy
        y = draw_text(draw, (x, y), route, local_font(locale, 82, "bold"), g.INK, max_width, 12)
        y += 10
        return draw_text(draw, (x, y), action, local_font(locale, 132, "bold"), g.INK, max_width, 18)
    if needs_shaped_text(locale):
        return paste_core_text(
            img,
            xy,
            title,
            width=max_width,
            font_size=112,
            weight="bold",
            fill=g.INK,
            line_gap=22,
            rtl=locale in rtl_locale_codes(),
        )
    return draw_text(draw, xy, title, local_font(locale, 112, "bold"), g.INK, max_width, 22)


def center_text(draw: ImageDraw.ImageDraw, rect, text: str, fnt: ImageFont.FreeTypeFont, fill: str) -> None:
    x1, y1, x2, y2 = rect
    tw, th = text_size(draw, text, fnt)
    draw.text((x1 + (x2 - x1 - tw) / 2, y1 + (y2 - y1 - th) / 2 - 2), text, font=fnt, fill=fill)


def dark_visual_center_offset(image: Image.Image) -> tuple[float, float]:
    rgba = image.convert("RGBA")
    pixels = rgba.load()
    xs: list[int] = []
    ys: list[int] = []
    for y in range(rgba.height):
        for x in range(rgba.width):
            r, g_, b, a = pixels[x, y]
            if a > 0 and (r < 128 or g_ < 128 or b < 128):
                xs.append(x)
                ys.append(y)
    if not xs or not ys:
        return rgba.width / 2, rgba.height / 2
    return (min(xs) + max(xs) + 1) / 2, (min(ys) + max(ys) + 1) / 2


def draw_locale_text(
    img: Image.Image,
    draw: ImageDraw.ImageDraw,
    locale: str,
    xy: tuple[int, int],
    text: str,
    *,
    width: int,
    font_size: int,
    weight: str,
    fill: str,
    line_gap: int = 2,
    alignment: str = "natural",
) -> int:
    if needs_shaped_text(locale):
        return paste_core_text(
            img,
            xy,
            text,
            width=width,
            font_size=font_size,
            weight=weight,
            fill=fill,
            line_gap=line_gap,
            rtl=locale in rtl_locale_codes(),
            alignment=alignment,
        )
    draw.text(xy, text, font=local_font(locale, font_size, weight), fill=fill)
    return xy[1] + text_size(draw, text or "A", local_font(locale, font_size, weight))[1]


def center_locale_text(
    img: Image.Image,
    draw: ImageDraw.ImageDraw,
    locale: str,
    rect,
    text: str,
    *,
    font_size: int,
    weight: str,
    fill: str,
) -> None:
    x1, y1, x2, y2 = rect
    width = x2 - x1
    if use_core_text(locale):
        rendered_top = y1 + max(0, (y2 - y1 - font_size - 8) // 2)
        paste_core_text(
            img,
            (x1, rendered_top),
            text,
            width=width,
            font_size=font_size,
            weight=weight,
            fill=fill,
            line_gap=0,
            rtl=locale in rtl_locale_codes(),
            alignment="center",
        )
        return
    fnt = local_font(locale, font_size, weight)
    bbox = draw.textbbox((0, 0), text, font=fnt)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    draw.text((x1 + (width - tw) / 2 - bbox[0], y1 + (y2 - y1 - th) / 2 - bbox[1]), text, font=fnt, fill=fill)


def center_locale_text_fitted(
    img: Image.Image,
    draw: ImageDraw.ImageDraw,
    locale: str,
    rect,
    text: str,
    *,
    font_size: int,
    min_size: int,
    weight: str,
    fill: str,
    padding: int = 18,
) -> None:
    x1, y1, x2, y2 = rect
    max_w = max(1, x2 - x1 - padding * 2)
    max_h = max(1, y2 - y1 - padding)
    best_size = min_size
    for size in range(font_size, min_size - 1, -2):
        fnt = local_font(locale, size, weight)
        bbox = draw.textbbox((0, 0), text, font=fnt)
        if bbox[2] - bbox[0] <= max_w and bbox[3] - bbox[1] <= max_h:
            best_size = size
            break
    center_locale_text(
        img,
        draw,
        locale,
        rect,
        text,
        font_size=best_size,
        weight=weight,
        fill=fill,
    )


def draw_centered_text(draw: ImageDraw.ImageDraw, y: int, text: str, fnt: ImageFont.FreeTypeFont, fill: str) -> None:
    tw, _ = text_size(draw, text, fnt)
    draw.text(((g.W - tw) / 2, y), text, font=fnt, fill=fill)


def wrapped_paragraph_lines(draw: ImageDraw.ImageDraw, text: str, fnt: ImageFont.FreeTypeFont, max_width: int) -> list[str]:
    lines: list[str] = []
    for paragraph in text.split("\n"):
        lines.extend(wrapped_lines(draw, paragraph, fnt, max_width) or [""])
    return lines


def text_block_height(
    draw: ImageDraw.ImageDraw,
    lines: list[str],
    fnt: ImageFont.FreeTypeFont,
    line_gap: int,
) -> int:
    if not lines:
        return 0
    height = 0
    for i, line in enumerate(lines):
        height += text_size(draw, line or "A", fnt)[1]
        if i < len(lines) - 1:
            height += line_gap
    return height


def draw_centered_wrapped_text(
    draw: ImageDraw.ImageDraw,
    y: int,
    text: str,
    fnt: ImageFont.FreeTypeFont,
    fill: str,
    max_width: int,
    line_gap: int,
) -> int:
    for line in wrapped_paragraph_lines(draw, text, fnt, max_width):
        bbox = draw.textbbox((0, 0), line or "A", font=fnt)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]
        draw.text(((g.W - tw) / 2 - bbox[0], y - bbox[1]), line, font=fnt, fill=fill)
        y += th + line_gap
    return y - line_gap


def draw_centered_wrapped_fitted(
    draw: ImageDraw.ImageDraw,
    y: int,
    text: str,
    locale: str,
    *,
    fill: str,
    max_width: int,
    sizes: tuple[int, ...],
    weight: str,
    line_gap: int,
    max_lines: int,
    max_height: int,
) -> int:
    chosen_font = local_font(locale, sizes[-1], weight)
    chosen_lines = wrapped_paragraph_lines(draw, text, chosen_font, max_width)
    for size in sizes:
        fnt = local_font(locale, size, weight)
        lines = wrapped_paragraph_lines(draw, text, fnt, max_width)
        if len(lines) <= max_lines and text_block_height(draw, lines, fnt, line_gap) <= max_height:
            chosen_font = fnt
            chosen_lines = lines
            break
        chosen_font = fnt
        chosen_lines = lines
    bottom = y
    for line in chosen_lines:
        bbox = draw.textbbox((0, 0), line or "A", font=chosen_font)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]
        draw.text(((g.W - tw) / 2 - bbox[0], bottom - bbox[1]), line, font=chosen_font, fill=fill)
        bottom += th + line_gap
    return bottom - line_gap


def ja_route_segments(route: str) -> list[tuple[str, ImageFont.FreeTypeFont]]:
    device_font = local_font("ja", 124, "bold")
    particle_font = local_font("ja", 92, "bold")
    if route == "AndroidからMacへ":
        return [("Android", device_font), ("から", particle_font), ("Mac", device_font), ("へ", particle_font)]
    if route == "MacからAndroidへ":
        return [("Mac", device_font), ("から", particle_font), ("Android", device_font), ("へ", particle_font)]
    return [(route, particle_font)]


def mixed_text_size(draw: ImageDraw.ImageDraw, segments: list[tuple[str, ImageFont.FreeTypeFont]]) -> tuple[int, int]:
    width = 0
    height = 0
    for text, fnt in segments:
        bbox = draw.textbbox((0, 0), text, font=fnt)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]
        width += tw
        height = max(height, th)
    return width, height


def draw_mixed_text(
    draw: ImageDraw.ImageDraw,
    xy: tuple[float, float],
    segments: list[tuple[str, ImageFont.FreeTypeFont]],
    fill: str,
) -> None:
    x, y = xy
    _, line_h = mixed_text_size(draw, segments)
    for text, fnt in segments:
        bbox = draw.textbbox((0, 0), text, font=fnt)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]
        draw.text((x - bbox[0], y + line_h - th - bbox[1]), text, font=fnt, fill=fill)
        x += tw


def draw_mixed_text_bottom(
    draw: ImageDraw.ImageDraw,
    x: float,
    bottom_y: float,
    segments: list[tuple[str, ImageFont.FreeTypeFont]],
    fill: str,
) -> None:
    for text, fnt in segments:
        bbox = draw.textbbox((0, 0), text, font=fnt)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]
        draw.text((x - bbox[0], bottom_y - th - bbox[1]), text, font=fnt, fill=fill)
        x += tw


def save(img: Image.Image, locale: str, name: str) -> None:
    out_dir = OUT / locale
    out_dir.mkdir(parents=True, exist_ok=True)
    img.convert("RGB").save(out_dir / f"{name}.png", optimize=True)


def base(locale: str, title: str, body: str, accent: str) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    img = Image.new("RGBA", (g.W, g.H), g.BG)
    d = ImageDraw.Draw(img)
    d.rectangle((0, 0, g.W, g.H), fill=g.BG)
    d.ellipse((-320, -250, 760, 720), fill=g.rgba(g.BG2, 255))
    d.ellipse((2120, 1160, 3260, 2220), fill=g.rgba("#EDF4EA", 255))

    img.alpha_composite(g.app_icon(165), (150, 145))
    d.text((345, 172), "Pyonta", font=g.font(62, "bold"), fill=g.INK)
    if use_core_text(locale):
        paste_core_text(
            img,
            (348, 252),
            copy(locale, "subtitle"),
            width=650,
            font_size=34,
            weight="medium",
            fill=g.MUTED,
            line_gap=6,
            rtl=locale in rtl_locale_codes(),
        )
    else:
        d.text((348, 252), copy(locale, "subtitle"), font=local_font(locale, 34, "medium"), fill=g.MUTED)
    d.rounded_rectangle((155, 365, 305, 421), radius=28, fill=accent)
    d.text((179, 377), "macOS", font=g.font(28, "bold"), fill="white")

    title_bottom = draw_headline(img, d, locale, (150, 510), title, 850)
    body_y = max(860, title_bottom + 42)
    if use_core_text(locale):
        paste_core_text(
            img,
            (154, body_y),
            body,
            width=760,
            font_size=43,
            weight="regular",
            fill=g.MUTED,
            line_gap=20,
            rtl=locale in rtl_locale_codes(),
        )
    else:
        draw_text(d, (154, body_y), body, local_font(locale, 43), g.MUTED, 760, 20)
    return img, d


def base_top_ja(title: str, body: str, accent: str) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    img = Image.new("RGBA", (g.W, g.H), g.BG)
    d = ImageDraw.Draw(img)
    d.rectangle((0, 0, g.W, g.H), fill=g.BG)
    d.ellipse((-320, -250, 760, 720), fill=g.rgba(g.BG2, 255))
    d.ellipse((2120, 1160, 3260, 2220), fill=g.rgba("#EDF4EA", 255))

    img.alpha_composite(g.app_icon(122), (150, 112))
    d.text((300, 128), "Pyonta", font=g.font(50, "bold"), fill=g.INK)
    d.text((302, 194), copy("ja", "subtitle"), font=local_font("ja", 30, "medium"), fill=g.MUTED)

    route, action = title.split("\n", 1)
    action_font = local_font("ja", 134, "bold")
    route_segments = ja_route_segments(route)
    spacer = 26
    route_w, _ = mixed_text_size(d, route_segments)
    action_w, _ = mixed_text_size(d, [(action, action_font)])
    x = (g.W - route_w - spacer - action_w) / 2
    headline_bottom_y = 405
    draw_mixed_text_bottom(d, x, headline_bottom_y, route_segments, g.INK)
    draw_mixed_text_bottom(d, x + route_w + spacer, headline_bottom_y, [(action, action_font)], g.INK)
    draw_centered_text(d, 456, body, local_font("ja", 41, "medium"), g.MUTED)
    return img, d


def base_top(locale: str, title: str, body: str, accent: str) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    if locale == "ja" and "\n" in title:
        return base_top_ja(title, body, accent)

    img = Image.new("RGBA", (g.W, g.H), g.BG)
    d = ImageDraw.Draw(img)
    d.rectangle((0, 0, g.W, g.H), fill=g.BG)
    d.ellipse((-320, -250, 760, 720), fill=g.rgba(g.BG2, 255))
    d.ellipse((2120, 1160, 3260, 2220), fill=g.rgba("#EDF4EA", 255))

    img.alpha_composite(g.app_icon(122), (150, 112))
    d.text((300, 128), "Pyonta", font=g.font(50, "bold"), fill=g.INK)
    if use_core_text(locale):
        paste_core_text(
            img,
            (302, 194),
            copy(locale, "subtitle"),
            width=740,
            font_size=30,
            weight="medium",
            fill=g.MUTED,
            line_gap=4,
            rtl=locale in rtl_locale_codes(),
        )
    else:
        d.text((302, 194), copy(locale, "subtitle"), font=local_font(locale, 30, "medium"), fill=g.MUTED)

    if use_core_text(locale):
        text_width = 2320
        text_x = (g.W - text_width) // 2
        title_bottom = paste_core_text(
            img,
            (text_x, 250),
            title,
            width=text_width,
            font_size=96,
            weight="bold",
            fill=g.INK,
            line_gap=14,
            rtl=locale in rtl_locale_codes(),
            alignment="center",
        )
        body_y = max(438, title_bottom + 24)
        paste_core_text(
            img,
            (text_x, body_y),
            body,
            width=text_width,
            font_size=41,
            weight="medium",
            fill=g.MUTED,
            line_gap=12,
            rtl=locale in rtl_locale_codes(),
            alignment="center",
        )
    else:
        title_sizes = (206, 198, 190, 182, 174, 166, 158) if locale == "ja" else (118, 110, 102, 94, 86, 78, 72)
        title_bottom = draw_centered_wrapped_fitted(
            d,
            230 if locale == "ja" else 244,
            title,
            locale,
            fill=g.INK,
            max_width=2320,
            sizes=title_sizes,
            weight="bold",
            line_gap=16,
            max_lines=2,
            max_height=205,
        )
        body_y = max(438, title_bottom + 24)
        draw_centered_wrapped_fitted(
            d,
            body_y,
            body,
            locale,
            fill=g.MUTED,
            max_width=2320,
            sizes=(41, 38, 35, 32),
            weight="medium",
            line_gap=10,
            max_lines=2,
            max_height=92,
        )
    return img, d


def paste_tinted_icon(img: Image.Image, icon_name: str, box, color: str) -> None:
    x1, y1, x2, y2 = box
    icon = Image.open(ASSET_DIR / f"{icon_name}.png").convert("RGBA")
    icon = icon.resize((x2 - x1, y2 - y1), Image.Resampling.LANCZOS)
    alpha = icon.getchannel("A")
    tinted = Image.new("RGBA", icon.size, color)
    tinted.putalpha(alpha)
    img.paste(tinted, (x1, y1), tinted)


def draw_file_row(
    img: Image.Image,
    d: ImageDraw.ImageDraw,
    locale: str,
    box,
    name: str,
    color: str,
) -> None:
    x1, y1, x2, y2 = box
    row_h = y2 - y1
    dot = min(50, row_h - 24)
    dot_y = y1 + (row_h - dot) / 2
    d.rounded_rectangle(box, radius=30, fill="#FFFFFF", outline=g.LINE, width=2)
    d.ellipse((x1 + 34, dot_y, x1 + 34 + dot, dot_y + dot), fill=color)
    draw_locale_text(
        img,
        d,
        locale,
        (x1 + 118, y1 + 17),
        name,
        width=x2 - x1 - 154,
        font_size=31,
        weight="bold",
        fill=g.INK,
    )


def draw_macbook_frame(img: Image.Image, d: ImageDraw.ImageDraw, screen) -> tuple[int, int, int, int]:
    g.shadow(img, screen, 44, 42)
    base_top_y = screen[3] - 2
    base_bottom_y = screen[3] + 96
    base_overhang = 82
    base_poly = (
        (screen[0] + 6, base_top_y),
        (screen[2] - 6, base_top_y),
        (screen[2] + base_overhang, base_bottom_y),
        (screen[0] - base_overhang, base_bottom_y),
    )
    d.polygon(base_poly, fill="#D3DBE2")
    d.line((base_poly[0], base_poly[1], base_poly[2], base_poly[3]), fill="#AAB7C1", width=4)
    d.rounded_rectangle(
        (screen[0] - base_overhang, screen[3] + 82, screen[2] + base_overhang, screen[3] + 122),
        radius=18,
        fill="#B6C2CB",
    )
    trackpad_w = 340
    trackpad = (
        (screen[0] + screen[2] - trackpad_w) // 2,
        screen[3] + 34,
        (screen[0] + screen[2] + trackpad_w) // 2,
        screen[3] + 68,
    )
    d.rounded_rectangle(trackpad, radius=14, fill="#E8EEF2", outline="#B5C1CA", width=2)
    d.rounded_rectangle(screen, radius=58, fill="#18212B")
    display = (screen[0] + 28, screen[1] + 34, screen[2] - 28, screen[3] - 34)
    d.rounded_rectangle(display, radius=42, fill="#F7FAFC")
    d.rounded_rectangle((display[0] + 30, display[1] + 24, display[2] - 30, display[1] + 92), radius=24, fill="#ECF3F7")
    d.rectangle((display[0] + 30, display[1] + 58, display[2] - 30, display[1] + 92), fill="#ECF3F7")
    notch_w = 190
    notch_h = 48
    notch_x = (display[0] + display[2] - notch_w) // 2
    notch = (notch_x, display[1] - 2, notch_x + notch_w, display[1] + notch_h)
    d.rounded_rectangle(notch, radius=18, fill="#18212B")
    d.rectangle((notch[0], notch[1], notch[2], notch[1] + 22), fill="#18212B")
    paste_tinted_icon(img, "monitor", (display[0] + 60, display[1] + 18, display[0] + 136, display[1] + 94), g.BLUE)
    d.text((display[0] + 160, display[1] + 29), "Mac", font=g.font(44, "bold"), fill="#677684")
    return display


def draw_android_phone_shell(img: Image.Image, d: ImageDraw.ImageDraw, phone) -> tuple[int, int, int, int]:
    g.shadow(img, phone, 52, 50)
    d.rounded_rectangle(phone, radius=70, fill="#18212B")
    content = (phone[0] + 28, phone[1] + 34, phone[2] - 28, phone[3] - 34)
    d.rounded_rectangle(content, radius=46, fill="#F8FAFC")
    d.text((phone[0] + 68, phone[1] + 78), "Android", font=g.font(74, "bold"), fill=g.INK)
    return content


def draw_product_transfer_mock(
    img: Image.Image,
    d: ImageDraw.ImageDraw,
    *,
    direction: str,
    locale: str,
    dx: int = 0,
    dy: int = 0,
    mac_screen: bool = False,
) -> None:
    is_receive = direction == "android-to-mac"
    mac = (1015 + dx, 455 + dy, 1945 + dx, 1338 + dy)
    if mac_screen:
        screen = (mac[0] - 260, mac[1] - 94, mac[2] + 115, mac[3] + 58)
        g.shadow(img, screen, 44, 42)
        base_top_y = screen[3] - 2
        base_bottom_y = screen[3] + 96
        base_overhang = 82
        base_poly = (
            (screen[0] + 6, base_top_y),
            (screen[2] - 6, base_top_y),
            (screen[2] + base_overhang, base_bottom_y),
            (screen[0] - base_overhang, base_bottom_y),
        )
        d.polygon(base_poly, fill="#D3DBE2")
        d.line((base_poly[0], base_poly[1], base_poly[2], base_poly[3]), fill="#AAB7C1", width=4)
        d.rounded_rectangle(
            (screen[0] - base_overhang, screen[3] + 82, screen[2] + base_overhang, screen[3] + 122),
            radius=18,
            fill="#B6C2CB",
        )
        trackpad_w = 340
        trackpad = (
            (screen[0] + screen[2] - trackpad_w) // 2,
            screen[3] + 34,
            (screen[0] + screen[2] + trackpad_w) // 2,
            screen[3] + 68,
        )
        d.rounded_rectangle(trackpad, radius=14, fill="#E8EEF2", outline="#B5C1CA", width=2)
        d.rounded_rectangle(screen, radius=58, fill="#18212B")
        display = (screen[0] + 28, screen[1] + 34, screen[2] - 28, screen[3] - 34)
        d.rounded_rectangle(display, radius=42, fill="#F7FAFC")
        d.rounded_rectangle((display[0] + 30, display[1] + 24, display[2] - 30, display[1] + 92), radius=24, fill="#ECF3F7")
        d.rectangle((display[0] + 30, display[1] + 58, display[2] - 30, display[1] + 92), fill="#ECF3F7")
        notch_w = 190
        notch_h = 48
        notch_x = (display[0] + display[2] - notch_w) // 2
        notch = (notch_x, display[1] - 2, notch_x + notch_w, display[1] + notch_h)
        d.rounded_rectangle(notch, radius=18, fill="#18212B")
        d.rectangle((notch[0], notch[1], notch[2], notch[1] + 22), fill="#18212B")
        paste_tinted_icon(img, "monitor", (display[0] + 60, display[1] + 18, display[0] + 136, display[1] + 94), g.BLUE)
        d.text((display[0] + 160, display[1] + 29), "Mac", font=g.font(44, "bold"), fill="#677684")
        mac_w = mac[2] - mac[0]
        mac_h = 830
        mac_x = int((display[0] + display[2] - mac_w) / 2)
        mac_y = display[1] + 120
        mac = (mac_x, mac_y, mac_x + mac_w, mac_y + mac_h)
    else:
        g.shadow(img, mac, 40, 36)
    d.rounded_rectangle(mac, radius=44, fill="#FFFFFF", outline="#D8E2EA", width=3)
    d.rounded_rectangle((mac[0], mac[1], mac[2], mac[1] + 92), radius=44, fill="#F4F8FA")
    d.rectangle((mac[0], mac[1] + 50, mac[2], mac[1] + 92), fill="#F4F8FA")
    for i, color in enumerate(("#FF6B6B", "#F5B94B", "#4FB163")):
        d.ellipse((mac[0] + 38 + i * 42, mac[1] + 34, mac[0] + 62 + i * 42, mac[1] + 58), fill=color)
    title_x = mac[0] + (82 if mac_screen else 190)
    if not mac_screen:
        paste_tinted_icon(img, "monitor", (mac[0] + 54, mac[1] + 142, mac[0] + 154, mac[1] + 242), g.BLUE)
    mac_title = mock_copy(locale, "macReceiveTitle" if is_receive else "macSendTitle")
    mac_subtitle = mock_copy(locale, "macReceiveSubtitle" if is_receive else "macSendSubtitle")
    if mac_screen and is_receive and locale == "ja":
        mac_subtitle = "Androidから受信"
    draw_locale_text(
        img,
        d,
        locale,
        (title_x, mac[1] + 132),
        mac_title,
        width=mac[2] - title_x - 70,
        font_size=68,
        weight="bold",
        fill=g.INK,
        line_gap=0,
    )
    draw_locale_text(
        img,
        d,
        locale,
        (title_x + 4, mac[1] + 220),
        mac_subtitle,
        width=mac[2] - title_x - 74,
        font_size=38,
        weight="medium",
        fill=g.MUTED,
        line_gap=0,
    )
    transfer_items = (
        (mock_copy(locale, "photos"), g.GREEN),
        (mock_copy(locale, "videos"), g.BLUE),
        (mock_copy(locale, "pdf"), g.AMBER),
        (mock_copy(locale, "text"), "#677684"),
    )
    row_h = 72
    row_gap = 18
    row_y = mac[1] + 318
    for i, (label, color) in enumerate(transfer_items):
        y = row_y + i * (row_h + row_gap)
        draw_file_row(img, d, locale, (mac[0] + 82, y, mac[2] - 82, y + row_h), label, color)
    action_y = mac[1] + 704
    d.rounded_rectangle((mac[0] + 82, action_y, mac[2] - 82, action_y + 76), radius=30, fill="#EAF6EE")
    action_text = mock_copy(locale, "paidReceiveAction" if is_receive else "sendAction")
    center_locale_text_fitted(
        img,
        d,
        locale,
        (mac[0] + 82, action_y, mac[2] - 82, action_y + 76),
        action_text,
        font_size=34,
        min_size=23,
        weight="bold",
        fill="#2F8B47",
    )

    phone_shift_x = 210 if mac_screen else 0
    phone = (2210 + dx + phone_shift_x, 488 + dy, 2638 + dx + phone_shift_x, 1370 + dy)
    g.shadow(img, phone, 52, 50)
    d.rounded_rectangle(phone, radius=70, fill="#18212B")
    d.rounded_rectangle((phone[0] + 28, phone[1] + 34, phone[2] - 28, phone[3] - 34), radius=46, fill="#F8FAFC")
    d.text((phone[0] + 68, phone[1] + 78), "Android", font=g.font(74, "bold"), fill=g.INK)
    draw_locale_text(
        img,
        d,
        locale,
        (phone[0] + 72, phone[1] + 214),
        mock_copy(locale, "share" if is_receive else "receiving"),
        width=phone[2] - phone[0] - 144,
        font_size=35,
        weight="bold",
        fill=g.MUTED,
    )
    labels = (
        (mock_copy(locale, "photos"), g.GREEN),
        (mock_copy(locale, "videos"), g.BLUE),
        (mock_copy(locale, "pdf"), g.AMBER),
        (mock_copy(locale, "text"), "#677684"),
    )
    for i, (label, color) in enumerate(labels):
        y = phone[1] + 286 + i * 94
        d.rounded_rectangle((phone[0] + 70, y, phone[2] - 70, y + 76), radius=24, fill="#FFFFFF", outline=g.LINE, width=2)
        d.ellipse((phone[0] + 96, y + 21, phone[0] + 130, y + 55), fill=color)
        draw_locale_text(
            img,
            d,
            locale,
            (phone[0] + 158, y + 17),
            label,
            width=phone[2] - phone[0] - 236,
            font_size=29,
            weight="bold",
            fill=g.INK,
        )
    d.rounded_rectangle((phone[0] + 70, phone[3] - 142, phone[2] - 70, phone[3] - 66), radius=24, fill="#EAF6EE")
    center_locale_text(
        img,
        d,
        locale,
        (phone[0] + 70, phone[3] - 142, phone[2] - 70, phone[3] - 66),
        mock_copy(locale, "quickShare" if is_receive else "ready"),
        font_size=28,
        weight="bold",
        fill="#2F8B47",
    )


def draw_transfer_arrow(d: ImageDraw.ImageDraw, start: tuple[int, int], end: tuple[int, int], color: str) -> None:
    sx, sy = start
    ex, ey = end
    if sx == ex:
        return

    direction = 1 if ex > sx else -1
    shaft_width = 64
    head_length = 124
    head_width = 150
    shaft_end_x = ex - direction * head_length

    shaft_left = min(sx, shaft_end_x)
    shaft_right = max(sx, shaft_end_x)
    d.rectangle(
        (shaft_left, sy - shaft_width // 2, shaft_right, sy + shaft_width // 2),
        fill=color,
    )
    d.polygon(
        (
            (ex, ey),
            (shaft_end_x, ey - head_width // 2),
            (shaft_end_x, ey + head_width // 2),
        ),
        fill=color,
    )


def draw_auto_discovery_chip(
    img: Image.Image,
    d: ImageDraw.ImageDraw,
    locale: str,
    *,
    center_x: int,
    top: int,
    icon_size: int = 182,
    label_half_width: int = 280,
    font_size: int = 37,
    min_size: int = 22,
) -> None:
    label = mock_copy(locale, "autoDiscovery")
    icon_box = (
        center_x - icon_size // 2,
        top,
        center_x + icon_size // 2,
        top + icon_size,
    )
    paste_tinted_icon(img, "wifi", icon_box, g.GREEN)

    center_locale_text_fitted(
        img,
        d,
        locale,
        (center_x - label_half_width, top + icon_size - 16, center_x + label_half_width, top + icon_size + 40),
        label,
        font_size=font_size,
        min_size=min_size,
        weight="bold",
        fill="#2F8B47",
    )


def draw_device_transfer_pair(
    img: Image.Image,
    d: ImageDraw.ImageDraw,
    *,
    direction: str,
    locale: str,
    dx: int = 0,
    dy: int = 0,
    mac_screen: bool = False,
) -> None:
    draw_product_transfer_mock(img, d, direction=direction, locale=locale, dx=dx, dy=dy, mac_screen=mac_screen)
    phone_shift_x = 210 if mac_screen else 0
    if mac_screen:
        gap_left = 2060 + dx + 55
        gap_right = 2210 + dx + phone_shift_x - 55
    else:
        gap_left = 1945 + dx + 40
        gap_right = 2210 + dx + phone_shift_x - 40
    if direction == "android-to-mac":
        draw_transfer_arrow(d, (gap_right, 930 + dy), (gap_left, 930 + dy), g.GREEN)
    else:
        draw_transfer_arrow(d, (gap_left, 930 + dy), (gap_right, 930 + dy), g.GREEN)
    if mac_screen:
        draw_auto_discovery_chip(
            img,
            d,
            locale,
            center_x=(gap_left + gap_right) // 2,
            top=620 + dy,
        )


def draw_receiving_mock(img: Image.Image, d: ImageDraw.ImageDraw, locale: str) -> None:
    draw_device_transfer_pair(img, d, direction="android-to-mac", locale=locale)


def screenshot_receive(locale: str) -> None:
    img, d = base_top(locale, copy(locale, "receiveTitle"), copy(locale, "receiveBody"), g.BLUE)
    draw_device_transfer_pair(img, d, direction="android-to-mac", locale=locale, dx=-315, dy=190, mac_screen=True)
    save(img, locale, "02-receive-from-android")


def screenshot_send(locale: str) -> None:
    img, d = base_top(locale, copy(locale, "sendTitle"), copy(locale, "sendBody"), g.GREEN)
    draw_device_transfer_pair(img, d, direction="mac-to-android", locale=locale, dx=-315, dy=190, mac_screen=True)
    save(img, locale, "01-send-to-android")


def screenshot_qr(locale: str) -> None:
    img, d = base_top(locale, copy(locale, "qrTitle"), copy(locale, "qrBody"), g.AMBER)
    screen = (440, 551, 1745, 1586)
    display = draw_macbook_frame(img, d, screen)
    panel = (display[0] + 140, display[1] + 150, display[2] - 140, display[3] - 125)
    g.shadow(img, panel, 26, 26)
    d.rounded_rectangle(panel, radius=34, fill="#FFFFFF", outline="#D8E2EA", width=2)
    d.text((panel[0] + 78, panel[1] + 58), "QR", font=g.font(60, "bold"), fill=g.INK)
    qr = g.qr_pattern(440)
    qr_pos = (round((panel[0] + panel[2] - 440) / 2), panel[1] + 150)
    g.shadow(img, (qr_pos[0], qr_pos[1], qr_pos[0] + 440, qr_pos[1] + 440), 20, 14)
    img.alpha_composite(qr, qr_pos)

    phone = (2105, 678, 2533, 1560)
    content = draw_android_phone_shell(img, d, phone)
    d.text((phone[0] + 80, phone[1] + 218), "QR", font=g.font(44, "bold"), fill=g.MUTED)
    scan_size = 280
    phone_center_x = (phone[0] + phone[2]) // 2
    scan = (phone_center_x - scan_size // 2, phone[1] + 360, phone_center_x + scan_size // 2, phone[1] + 360 + scan_size)
    d.rounded_rectangle(scan, radius=34, fill="#FFFFFF", outline=g.BLUE, width=10)
    d.line((scan[0] + 38, scan[1] + 38, scan[0] + 112, scan[1] + 38), fill=g.BLUE, width=8)
    d.line((scan[0] + 38, scan[1] + 38, scan[0] + 38, scan[1] + 112), fill=g.BLUE, width=8)
    d.line((scan[2] - 38, scan[1] + 38, scan[2] - 112, scan[1] + 38), fill=g.BLUE, width=8)
    d.line((scan[2] - 38, scan[1] + 38, scan[2] - 38, scan[1] + 112), fill=g.BLUE, width=8)
    d.line((scan[0] + 38, scan[3] - 38, scan[0] + 112, scan[3] - 38), fill=g.BLUE, width=8)
    d.line((scan[0] + 38, scan[3] - 38, scan[0] + 38, scan[3] - 112), fill=g.BLUE, width=8)
    d.line((scan[2] - 38, scan[3] - 38, scan[2] - 112, scan[3] - 38), fill=g.BLUE, width=8)
    d.line((scan[2] - 38, scan[3] - 38, scan[2] - 38, scan[3] - 112), fill=g.BLUE, width=8)
    mini_qr = g.qr_pattern(130)
    mini_center_x, mini_center_y = dark_visual_center_offset(mini_qr)
    img.alpha_composite(
        mini_qr,
        (
            round((scan[0] + scan[2]) / 2 - mini_center_x),
            round((scan[1] + scan[3]) / 2 - mini_center_y),
        ),
    )
    draw_transfer_arrow(d, (1815, 1015), (2050, 1015), g.AMBER)
    save(img, locale, "03-qr-fallback")


def draw_plus_alert(img: Image.Image, d: ImageDraw.ImageDraw, locale: str, rect) -> None:
    x1, y1, x2, _ = rect
    g.shadow(img, rect, 36, 55)
    g.rounded(d, rect, 36, g.PANEL, "#CCD6DE", 2)
    img.alpha_composite(g.app_icon(110), (x1 + 60, y1 + 58))
    d.text((x1 + 200, y1 + 60), "Pyonta+", font=g.font(56, "bold"), fill=g.INK)
    if use_core_text(locale):
        paste_core_text(
            img,
            (x1 + 200, y1 + 142),
            copy(locale, "plusBody"),
            width=x2 - x1 - 270,
            font_size=26,
            weight="regular",
            fill=g.MUTED,
            line_gap=6,
            rtl=locale in rtl_locale_codes(),
        )
    else:
        draw_text(d, (x1 + 200, y1 + 145), copy(locale, "plusBody"), local_font(locale, 27), g.MUTED, x2 - x1 - 270, 6)
    d.rounded_rectangle((x2 - 415, y1 + 310, x2 - 245, y1 + 370), radius=18, fill="#EEF3F7", outline=g.LINE)
    center_text(d, (x2 - 415, y1 + 310, x2 - 245, y1 + 370), "Cancel", g.font(26, "medium"), g.INK)
    d.rounded_rectangle((x2 - 225, y1 + 310, x2 - 50, y1 + 370), radius=18, fill=g.BLUE)
    center_text(d, (x2 - 225, y1 + 310, x2 - 50, y1 + 370), "OK", g.font(26, "bold"), "white")


def screenshot_plus(locale: str) -> None:
    img, d = base_top(locale, copy(locale, "plusTitle"), copy(locale, "plusBody"), g.BLUE)
    screen = (440, 551, 1745, 1586)
    display = draw_macbook_frame(img, d, screen)
    workspace = (display[0] + 95, display[1] + 140, display[2] - 95, display[3] - 125)
    d.rounded_rectangle(workspace, radius=34, fill="#F3F6F8", outline="#E1E7EC", width=2)
    alert = (workspace[0] + 92, workspace[1] + 138, workspace[2] - 92, workspace[1] + 560)
    draw_plus_alert(img, d, locale, alert)
    chips = (
        (mock_copy(locale, "planMonthly"), 245),
        (mock_copy(locale, "planYearly"), 350),
        (mock_copy(locale, "planLifetime"), 260),
    )
    chip_gap = 30
    total_chip_width = sum(width for _, width in chips) + chip_gap * (len(chips) - 1)
    x = round((workspace[0] + workspace[2] - total_chip_width) / 2)
    chip_y = workspace[3] - 112
    for chip, w in chips:
        d.rounded_rectangle((x, chip_y, x + w, chip_y + 76), radius=26, fill="#FFFFFF", outline=g.LINE, width=2)
        center_locale_text_fitted(
            img,
            d,
            locale,
            (x, chip_y, x + w, chip_y + 76),
            chip,
            font_size=30,
            min_size=18,
            weight="bold",
            fill=g.BLUE,
        )
        x += w + chip_gap
    phone = (2105, 678, 2533, 1560)
    draw_android_phone_shell(img, d, phone)
    draw_locale_text(
        img,
        d,
        locale,
        (phone[0] + 74, phone[1] + 220),
        mock_copy(locale, "share"),
        width=phone[2] - phone[0] - 148,
        font_size=34,
        weight="bold",
        fill=g.MUTED,
    )
    transfer_items = (
        (mock_copy(locale, "photos"), g.GREEN),
        (mock_copy(locale, "videos"), g.BLUE),
        (mock_copy(locale, "pdf"), g.AMBER),
        (mock_copy(locale, "text"), "#677684"),
    )
    for i, (label, color) in enumerate(transfer_items):
        y = phone[1] + 286 + i * 94
        d.rounded_rectangle((phone[0] + 76, y, phone[2] - 76, y + 76), radius=24, fill="#FFFFFF", outline=g.LINE, width=2)
        d.ellipse((phone[0] + 102, y + 21, phone[0] + 136, y + 55), fill=color)
        draw_locale_text(img, d, locale, (phone[0] + 164, y + 17), label, width=phone[2] - phone[0] - 242, font_size=28, weight="bold", fill=g.INK)
    d.rounded_rectangle((phone[0] + 70, phone[3] - 142, phone[2] - 70, phone[3] - 66), radius=24, fill="#EAF6EE")
    center_locale_text(
        img,
        d,
        locale,
        (phone[0] + 70, phone[3] - 142, phone[2] - 70, phone[3] - 66),
        mock_copy(locale, "quickShare"),
        font_size=28,
        weight="bold",
        fill="#2F8B47",
    )
    draw_auto_discovery_chip(
        img,
        d,
        locale,
        center_x=1925,
        top=810,
    )
    draw_transfer_arrow(d, (2050, 1120), (1800, 1120), g.BLUE)
    save(img, locale, "04-pyonta-plus")


def review_screenshot(locale: str) -> None:
    img = Image.new("RGBA", (g.W, g.H), g.BG)
    d = ImageDraw.Draw(img)
    d.ellipse((-320, -250, 760, 720), fill=g.rgba(g.BG2, 255))
    d.ellipse((2120, 1160, 3260, 2220), fill=g.rgba("#EDF4EA", 255))
    display = draw_macbook_frame(img, d, (610, 300, 2270, 1505))
    workspace = (display[0] + 120, display[1] + 160, display[2] - 120, display[3] - 170)
    d.rounded_rectangle(workspace, radius=34, fill="#F3F6F8", outline="#E1E7EC", width=2)
    draw_plus_alert(img, d, locale, (workspace[0] + 145, workspace[1] + 170, workspace[2] - 145, workspace[1] + 590))
    out_dir = OUT / "review"
    out_dir.mkdir(parents=True, exist_ok=True)
    img.convert("RGB").save(out_dir / f"pyonta-plus-required-{locale}-2880x1800.png", optimize=True)


def main() -> None:
    missing = sorted(locale.code for locale in TARGET_LOCALES if locale.code not in COPY)
    if missing:
        raise SystemExit("Missing screenshot copy for: " + ", ".join(missing))
    for locale in TARGET_LOCALES:
        code = locale.code
        screenshot_receive(code)
        screenshot_send(code)
        screenshot_qr(code)
        screenshot_plus(code)
        review_screenshot(code)
    print(f"Generated next-release screenshots for {len(TARGET_LOCALES)} locale IDs in {OUT}")


if __name__ == "__main__":
    main()
