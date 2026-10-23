# Ninja Game

Pygame ile geliştirilmiş, bölüm tabanlı bir 2D platform oyunu. Projede oyunun yanında özel bir harita editörü de bulunur.

## Gereksinimler

- Python 3.10 veya üzeri
- Pygame (requirements.txt içinden kurulur)

## Kurulum

Proje klasöründe sanal ortam oluşturup bağımlılıkları yükleyin:

```bash
python -m venv .venv
```

Windows:

```powershell
.venv\Scripts\Activate.ps1
```

macOS/Linux:

```bash
source .venv/bin/activate
```

Ardından:

```bash
python -m pip install -r requirements.txt
```

## Oyunu başlatma

Proje kök dizininden:

```bash
python game.py
```

Varsayılan kontroller sol/sağ ok ile hareket, yukarı ok ile zıplama ve duvara tutunurken tırmanma, X ile atılmadır. Tırmanış enerjisi yerde yenilenir. Esc ile oyunu duraklatıp kontrolleri yeniden atayabilir ve müzik/ses efekt düzeylerini değiştirebilirsiniz.

İlerleme ve ses tercihleri kullanıcı profilindeki `.ninjagame/save.json` dosyasına kaydedilir.

## Harita editörü

```bash
python editor/editor.py
```

WASD ile görünümü kaydırın. G ile ızgaralı/serbest yerleştirme arasında geçiş yapın, T ile otomatik döşeme uygulayın ve O ile haritayı `editor/world.json` konumuna kaydedin. Ctrl+Z ve Ctrl+Y geri al/yinele işlemleridir. Ekranın altındaki durum metni kaydedilmemiş değişiklikleri gösterir. Shift ile fare tekerleği varyant seçer; Shift olmadan tekerlek döşeme grubunu değiştirir.

Son düzenlediğiniz haritayı oyunda önizlemek için proje kökünden çalıştırın:

```bash
python game.py --map editor/world.json
```

## Windows uygulaması oluşturma

Bağımlılıkları kurduktan sonra proje kökünde `build.bat` dosyasını çalıştırın. Uygulama `dist/NinjaGame/` klasörüne oluşturulur; klasörün tamamını birlikte taşıyın.

## Proje yapısı

- `game.py`: oyun döngüsü ve seviye akışı
- `scripts/`: varlıklar, karakterler, fizik ve harita işleme
- `data/maps/`: oyun seviyeleri (numaralı JSON dosyaları)
- `data/images/`, `data/sfx/`, `data/music.wav`: oyun varlıkları
- `editor/`: harita editörü ve düzenlenen harita
