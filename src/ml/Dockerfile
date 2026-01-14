# Wir nutzen ein schlankes Python Image
FROM python:3.9-slim

# Arbeitsverzeichnis im Container setzen
WORKDIR /app

# System-Abhängigkeiten für OpenCV installieren (WICHTIG!)
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Requirements kopieren und installieren
COPY requirements.txt .
# Tipp: --no-cache-dir spart Platz im Image
RUN pip install --no-cache-dir -r requirements.txt

# Den restlichen Code kopieren
COPY . .

# Port 8000 freigeben
EXPOSE 8000

# Server starten
# host 0.0.0.0 ist wichtig, damit er von außen erreichbar ist
CMD ["uvicorn", "inference_service:app", "--host", "0.0.0.0", "--port", "8000"]