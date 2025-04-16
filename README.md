# LinkedIn Jobs Scraper

LinkedIn iş ilanlarını otomatik olarak çeken bir Python scripti. Belirtilen arama kriterlerine (iş unvanı, konum) göre iş ilanlarını toplar ve JSON veya CSV formatında kaydeder.

## Özellikler

- Belirtilen arama kriterlerine göre LinkedIn iş ilanlarını otomatik olarak çeker
- Detay panelini atlamak veya kullanmak için iki farklı çalışma modu
- JSON ve CSV formatlarında çıktı alma
- Özelleştirilebilir sayıda iş ilanı toplama (varsayılan: 50)
- Headless (arka planda) veya normal tarayıcı modu seçeneği

## Gereksinimler

- Python 3.6+
- Chrome tarayıcısı
- ChromeDriver
- Selenium ve diğer gerekli paketler

```bash
pip install selenium webdriver-manager
```

## Kurulum

1. Repo'yu klonlayın:
```bash
git clone https://github.com/yourusername/Linkedin-Jobs-Scraper.git
cd Linkedin-Jobs-Scraper
```

2. Gerekli Python paketlerini yükleyin:
```bash
pip install -r requirements.txt
```

3. ChromeDriver'ı kurun (macOS için):
```bash
brew install --cask chromedriver
xattr -d com.apple.quarantine $(which chromedriver)
```

## Kullanım

### Temel Kullanım

```bash
python Linkedin_jobs_scraper.py --job-title "data scientist" --location "Istanbul"
```

### Hızlı Mod (Detay Panelini Atla)

```bash
python Linkedin_jobs_scraper.py --job-title "data scientist" --location "Istanbul" --skip-details
```

### Tüm Parametreler

```bash
python Linkedin_jobs_scraper.py --job-title "data scientist" \
                           --location "Istanbul" \
                           --max-jobs 100 \
                           --max-scrolls 20 \
                           --output-format json \
                           --output-file "my_jobs_data" \
                           --headless \
                           --username "YourName" \
                           --skip-details
```

| Parametre | Açıklama | Varsayılan Değer |
|-----------|----------|-----------------|
| `--job-title` | Aranacak iş unvanı | (Zorunlu) |
| `--location` | Aranacak konum | (Zorunlu) |
| `--max-jobs` | Toplanacak maksimum iş ilanı sayısı | 50 |
| `--max-scrolls` | Yapılacak maksimum scroll sayısı | 20 |
| `--output-format` | Çıktı formatı (json, csv, both) | json |
| `--output-file` | Çıktı dosyası adı (uzantısız) | (Otomatik oluşturulur) |
| `--headless` | Tarayıcıyı arka planda çalıştır | False |
| `--username` | Atıf için kullanıcı adı | None |
| `--skip-details` | Detay paneline tıklamadan temel bilgileri çek | False |

## Örnek Çıktı

```json
[
  {
    "id": "3574136587",
    "title": "Data Scientist",
    "company": "Example Company",
    "location": "Istanbul, Turkey",
    "job_type": "Full-time",
    "description": "We are looking for a Data Scientist to join our team...",
    "apply_link": "https://www.linkedin.com/jobs/view/3574136587",
    "date_posted": "2 days ago",
    "scraped_date": "2023-08-15T14:30:45.123456",
    "source": "LinkedIn Jobs",
    "attribution": "Collected via LinkedIn Jobs scraper"
  }
]
```

## Notlar

- LinkedIn'in yapısı zamanla değişebilir, bu nedenle script çalışmazsa lütfen bir issue açın
- LinkedIn, otomatik scraping'i engellemek için çeşitli önlemler alabilir. Aşırı kullanımdan kaçının
- Bu script sadece eğitim ve kişisel amaçlar için kullanılmalıdır

## Lisans

MIT 