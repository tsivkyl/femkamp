# femkamp
Utvecklat för att räkna ut och spara resultat från femkamper på Dalarö

## Kom igång

Projektet har script som skapar en virtuell Python-miljö, installerar allt i
`requirements.txt` och startar Flask-servern.

Scriptet aktiverar venv medan servern körs. Om du vill att venv ska vara aktiv
kvar i terminalen efteråt behöver du aktivera den manuellt.

### Linux/macOS

```bash
./script.sh
```

Om scriptet inte går att köra kan du först ge det rättigheter:

```bash
chmod +x script.sh
./script.sh
```

Aktivera venv manuellt på Linux/macOS:

```bash
source .venv/bin/activate
```

Lägg in sample data:

```bash
python server/databasesetup.py
```

### Windows

I Command Prompt:

```bat
script.bat
```

I PowerShell:

```powershell
.\script.bat
```

Aktivera venv manuellt på Windows:

```bat
.venv\Scripts\activate
```

Lägg in sample data:

```bat
python server\databasesetup.py
```
