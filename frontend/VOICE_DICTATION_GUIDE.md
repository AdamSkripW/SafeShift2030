# 🎤 Voice Dictation Feature - User Guide (Whisper API)

## ✨ Čo to robí?

**Hlasové diktovanie** pomocou **OpenAI Whisper API** - profesionálne speech-to-text riešenie!

### Ako to funguje:
1. **Klikneš na mikrofón** 🎤
2. **Nadiktuješ** svoje údaje (nahrávka v browseri)
3. **Audio sa pošle na backend**
4. **Whisper API** transkribuje hlas → text
5. **GPT-4o-mini** parsuje text → štruktúrované dáta
6. **Automaticky vyplní** formulár

---

## 🚀 TECHNOLÓGIA:

### Backend Flow:
```
Audio (webm) → Flask endpoint → Whisper API → Transcript
                                               ↓
                                         GPT-4o-mini
                                               ↓
                                         JSON data → Frontend
```

### Frontend:
- **MediaRecorder API** - nahrávanie audia (funguje vo všetkých browseroch!)
- **FormData** - posielanie audio súboru
- **HTTP POST** - `/api/shifts/parse-voice`

### Backend:
- **Whisper API** - speech-to-text (slovenčina podporovaná)
- **GPT-4o-mini** - parsovanie textu na JSON
- **VoiceService** - orchestrácia

---

## 📝 Príklad použitia:

**Povieš (môžeš hovoriť VŠETKO):**
> "Včera som mal nočnú zmenu dvanásť hodín, spal som len štyri hodiny, dvadsať pacientov, stres deväť, boli kritické prípady a urgentné situácie"

**Whisper transkribuje:**
> "včera som mal nočnú zmenu dvanásť hodín spal som len štyri hodiny dvadsať pacientov stres deväť boli kritické prípady a urgentné situácie"

**GPT parsuje:**
```json
{
  "shiftDate": "2025-11-29",  // Včera!
  "shiftType": "night",        // Nočná
  "hoursSleptBefore": 4,
  "shiftLengthHours": 12,
  "patientsCount": 20,
  "stressLevel": 9,
  "shiftNote": "boli kritické prípady a urgentné situácie"
}
```

**Formulár sa vyplní automaticky - VŠETKY POLIA!** ✨

---

## 🗣️ ČO VŠETKO MÔŽEŠ POVEDAŤ:

### 📅 **Shift Date** (dátum zmeny):
- "dnes" → dnes
- "včera" → včera  
- "tridsiatého novembra" → 30.11.2025
- Ak nespomínaš → použije sa dnes

### 🌙 **Shift Type** (typ zmeny):
- "denná" / "denná zmena" / "cez deň" → DAY
- "nočná" / "nočná zmena" / "cez noc" → NIGHT

### 😴 **Hours Slept** (spánok):
- "spal som 7 hodín" → 7
- "spánok 4 hodiny" → 4
- "sedem hodín" (slovom) → 7

### ⏱️ **Shift Length** (dĺžka zmeny):
- "zmena 8 hodín" → 8
- "pracoval som 12 hodín" → 12
- "osemhodinová zmena" → 8

### 👥 **Patients Count** (pacienti):
- "15 pacientov" → 15
- "dvadsať pacientov" → 20
- "veľa pacientov" → AI odhadne (20+)
- "málo pacientov" → AI odhadne (5-10)

### 😰 **Stress Level** (stres):

**Môžeš povedať ČÍSLOM:**
- "stres 6" → 6
- "úroveň stresu 9" → 9

**ALEBO SLOVAMI (AI rozumie kontextu!):**

**VYSOKÝ STRES (8-10):**
- "veľmi vystresovaný" → 9
- "extrémne vystresovaný" → 9
- "veľký stres" → 8
- "hrozný stres" / "strašný stres" → 10
- "náročné" / "ťažké" / "vyčerpávajúce" → 8
- Z kontextu: "kritické prípady" → 9

**STREDNÝ STRES (4-6):**
- "stredný stres" / "normálne" → 5
- "trochu stresujúce" / "mierny stres" → 4
- "dosť náročné" → 6

**NÍZKY STRES (1-3):**
- "málo vystresovaný" → 3
- "v pohode" / "v pohode bolo" → 2
- "žiadny stres" / "bez stresu" / "pokojne" → 1
- "ľahké" / "jednoduché" → 2

**PRÍKLADY:**
- "veľmi som vystresovaný" → AI dá stres 9
- "bolo to v pohode žiadny stres" → AI dá stres 1
- "trochu náročné ale v pohode" → AI dá stres 4-5
- "kritické situácie urgentné prípady" → AI dá stres 9 + pridá do notes

### 📝 **Shift Note** (poznámky):
AI automaticky extrahuje čokoľvek navyše:
- "boli kritické situácie"
- "urgentný prípad na JIS-ke"
- "komplikácie pri operácii"
- "veľa práce unavený som"
- "rušno bolo celú zmenu"

---

## 🎯 VÝHODY oproti Web Speech API:

| Web Speech API | Whisper API |
|----------------|-------------|
| ❌ Len Chrome/Edge | ✅ **Všetky browsery** |
| ❌ Client-side | ✅ **Server-side** (bezpečnejšie) |
| ❌ Nestabilné | ✅ **Produkt grade** |
| ❌ Limitované jazyky | ✅ **99+ jazykov perfektne** |
| ❌ Bez kontextu | ✅ **AI context understanding** |

---

## 🔧 Implementácia:

### Backend (`voice_service.py`):
```python
def process_audio_to_shift_data(audio_file):
    # 1. Whisper transcription
    transcript = client.audio.transcriptions.create(
        model="whisper-1",
        file=audio_file,
        language="sk"
    )
    
    # 2. GPT parsing
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{
            "content": f"Parse: {transcript}"
        }]
    )
    
    return parsed_data
```

### Frontend (`new-shift.component.ts`):
```typescript
async startVoiceRecording() {
  const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
  this.mediaRecorder = new MediaRecorder(stream);
  this.mediaRecorder.start();
}

stopVoiceRecording() {
  this.mediaRecorder.stop();
  // Auto-upload audio to backend
}
```

### API Endpoint:
```
POST /api/shifts/parse-voice
Content-Type: multipart/form-data

Body:
  audio: <audio_blob> (webm format)

Response:
{
  "success": true,
  "transcript": "mal som dennú zmenu...",
  "data": {
    "shiftDate": "2025-11-30",
    "hoursSleptBefore": 7,
    ...
  }
}
```

---

## 💡 Demo scenár:

1. **Otvor** New Shift formulár
2. **Klikni** "🎙️ Start Voice Dictation" 
   - Button sa zmení na **ČERVENÝ** s blikajúcou 🔴
3. **Hovor:** "Včera nočná zmena dvanásť hodín, spal som len štyri hodiny, dvadsať pacientov, stres deväť, boli kritické prípady"
4. **Klikni** "🔴 Recording... Click to STOP"
   - Button sa zmení na **MODRÝ** s točiacou sa ⚙️
5. **Počkaj** 2-3 sekundy (Whisper + GPT processing)
   - Uvidíš "⏳ Processing with Whisper API..."
6. **BOOM!** Všetky polia vyplnené! 🎉
   - Dátum: Včera
   - Typ: Nočná
   - Spánok: 4h
   - Dĺžka: 12h
   - Pacienti: 20
   - Stres: 9
   - Poznámka: "boli kritické prípady"

---

## 🌟 Prečo je to WOW:

- ✅ **Funguje všade** (Chrome, Firefox, Safari, Edge)
- ✅ **Whisper = industry standard** (používa to Spotify, Discord...)
- ✅ **Slovenčina perfektne** (Whisper má 99%+ accuracy)
