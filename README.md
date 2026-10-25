# Ninja Game

Pygame ile geliştirilmiş, altı bölümlük 2D ninja platform oyunu. Uzun keşif rotaları, düşman çatışmaları, duvara tırmanma, çift zıplama ve atılma hareketleri içerir. Harita editörü de projeye dahildir.

## Oyunu çalıştırma

Python 3.10 veya üzerini kurduktan sonra proje klasöründe:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python game.py
```

Linux veya macOS'ta sanal ortamı `source .venv/bin/activate` ile etkinleştirin.

## Kontroller

| İşlem | Varsayılan tuş |
| --- | --- |
| Hareket | Sol / Sağ ok |
| Zıpla ve duvara tırman | Yukarı ok |
| Atılma | X |
| Duraklat / geri | Esc |
| Menüde gezin / seç | Yukarı-aşağı ok, Enter |

Oyuncu ikinci bir kez zıplayabilir ve üç cana sahiptir. Hasar aldıktan sonra kısa süreliğine yeniden hasar görmez. Atılma kullanımdan sonra kısa bir dolum süresi bekler; ekrandaki göstergeler canı, tırmanış enerjisini, atılmayı ve kullanılabilir zıplamaları gösterir. Kontroller ve müzik/ses seviyesi Ayarlar menüsünden değiştirilebilir.

İlerleme ve tercihler Windows'ta `%USERPROFILE%\.ninjagame\save.json` konumuna kaydedilir.

## Harita editörü

```powershell
python editor/editor.py
```

WASD ile görünümü kaydırın. G ızgaralı/serbest yerleşimi değiştirir, T otomatik döşemeyi uygular. O haritayı `editor/world.json` konumuna kaydeder; Ctrl+Z ve Ctrl+Y geri al/yinele işlemleridir.

Haritayı oyunda denemek için:

```powershell
python game.py --map editor/world.json
```

## Windows için dağıtım

`build.bat` dosyasını çalıştırın. PyInstaller, çalıştırılabilir dosyayı ve oyun varlıklarını `dist/NinjaGame/` klasöründe hazırlar. Bu klasörün tamamını oyuncularla paylaşın; oyun `NinjaGame.exe` üzerinden başlatılır.

## Proje yapısı

- `game.py`: ana menü, oyun döngüsü, kayıt ve seviye akışı
- `scripts/`: oyuncu, düşman, fizik, animasyon ve harita kodu
- `data/maps/`: altı numaralı bölüm haritası
- `data/images/`, `data/sfx/`, `data/music.wav`: oyun görselleri ve sesleri
- `editor/`: harita düzenleyici
