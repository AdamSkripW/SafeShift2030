# 🎤 Voice Button - Visual States Guide

## 3 DISTINCT STATES

### 1️⃣ **IDLE** (Čakanie)
```
┌─────────────────────────────────────┐
│   🎤  🎙️ Start Voice Dictation   │
│                                     │
│   Color: White/Purple               │
│   Animation: Hover effect           │
│   Click: Starts recording           │
└─────────────────────────────────────┘
```
**Visual:**
- Icon: 🎤 (statický mikrofón)
- Background: `rgba(255, 255, 255, 0.2)` (priehľadná biela)
- Border: `rgba(255, 255, 255, 0.5)`
- Text: "🎙️ Start Voice Dictation"
- Cursor: `pointer`

**User sees:**
> "Môžem začať nahrávať"

---

### 2️⃣ **RECORDING** (Nahrávam)
```
┌─────────────────────────────────────┐
│   🔴  Recording... Click to STOP   │
│                                     │
│   Color: RED (pulsing)              │
│   Animation: Blink + Pulse          │
│   Click: Stops recording            │
└─────────────────────────────────────┘
```
**Visual:**
- Icon: 🔴 (blikajúci červený bod)
- Background: `rgba(239, 68, 68, 0.4)` (červená)
- Border: `rgba(239, 68, 68, 0.8)` (tmavo červená)
- Text: "🔴 Recording... Click to STOP"
- Animation: 
  - **Icon blinks**: opacity 1 → 0.2 → 1 (1s loop)
  - **Button pulses**: scale 1 → 1.02 + shadow grows (1.5s loop)
- Cursor: `pointer`

**User sees:**
> "NAHRÁVAM! 🔴 Hovorím do mikrofónu"

**CSS Animation:**
```css
@keyframes pulse-recording {
  0%, 100% {
    box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.7);
    transform: scale(1);
  }
  50% {
    box-shadow: 0 0 0 10px rgba(239, 68, 68, 0);
    transform: scale(1.02);
  }
}

@keyframes blink {
  0%, 50%, 100% { opacity: 1; }
  25%, 75% { opacity: 0.2; }
}
```

---

### 3️⃣ **PROCESSING** (Spracúvam)
```
┌─────────────────────────────────────┐
│  ⚙️  ⏳ Processing with Whisper... │
│                                     │
│   Color: BLUE (pulsing)             │
│   Animation: Spin + Pulse           │
│   Click: DISABLED                   │
└─────────────────────────────────────┘
```
**Visual:**
- Icon: ⚙️ (točiace sa koliesko)
- Background: `rgba(59, 130, 246, 0.4)` (modrá)
- Border: `rgba(59, 130, 246, 0.8)` (tmavo modrá)
- Text: "⏳ Processing with Whisper API..."
- Animation:
  - **Icon spins**: 360° rotation (2s linear loop)
  - **Button pulses**: shadow grows (2s loop)
- Cursor: `not-allowed`
- Disabled: `true`

**User sees:**
> "Čakám... AI spracúva môj hlas 🤖"

**CSS Animation:**
```css
@keyframes pulse-processing {
  0%, 100% {
    box-shadow: 0 0 0 0 rgba(59, 130, 246, 0.6);
  }
  50% {
    box-shadow: 0 0 0 8px rgba(59, 130, 246, 0);
  }
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
```

---

## 🔄 STATE FLOW

```
     USER CLICKS          RECORDING DONE        WHISPER+GPT DONE
IDLE ───────────> RECORDING ────────────> PROCESSING ───────────> IDLE
 🎤                  🔴                      ⚙️                      🎤
                                                                     ↓
                                                              ✅ Form filled!
```

---

## 🎨 COLOR CODING

| State | Background Color | Meaning |
|-------|------------------|---------|
| **IDLE** | White/Purple (`rgba(255,255,255,0.2)`) | Ready to use |
| **RECORDING** | **RED** (`rgba(239,68,68,0.4)`) | Active mic! Speaking now |
| **PROCESSING** | **BLUE** (`rgba(59,130,246,0.4)`) | AI working, please wait |

---

## 💡 USER EXPERIENCE

### What user sees during full workflow:

1. **Sees**: 🎤 "Start Voice Dictation" (white)
   - **Thinks**: "I can start"
   
2. **Clicks** → Button turns **RED** 🔴
   - **Sees**: Blinking red dot + pulsing button
   - **Thinks**: "It's recording! I'm talking now"
   
3. **Clicks STOP** → Button turns **BLUE** ⚙️
   - **Sees**: Spinning gear + pulsing blue
   - **Thinks**: "Processing... waiting for AI"
   
4. **After 2-3s** → Button returns to **WHITE** 🎤
   - **Sees**: ✅ "Whisper Detected: ..." + form auto-filled
   - **Thinks**: "WOW! It worked! 🎉"

---

## 🔊 COMPLETE EXAMPLE

**User workflow:**

```
[User opens New Shift form]

Button: 🎤 Start Voice Dictation (white/purple)
User: *clicks*

Button: 🔴 Recording... Click to STOP (RED, blinking)
User: "Včera nočná zmena dvanásť hodín, veľmi vystresovaný som, boli kritické prípady"
User: *clicks STOP*

Button: ⚙️ Processing with Whisper API... (BLUE, spinning, DISABLED)
[Whisper transcribes in 1-2s]
[GPT parses in 1s]

Button: 🎤 Start Voice Dictation (back to white/purple)
Transcript appears: ✅ "včera nočná zmena dvanásť hodín veľmi vystresovaný som boli kritické prípady"

Form auto-fills:
  ✅ Date: 2025-11-29 (včera)
  ✅ Type: night (nočná)
  ✅ Length: 12h
  ✅ Stress: 9 (veľmi vystresovaný)
  ✅ Note: "boli kritické prípady"

User: 🎉 "AMAZING!"
```

---

## ✅ VŠETKO JE UŽ IMPLEMENTOVANÉ!

Všetky 3 stavy sú už hotové v kóde:
- ✅ HTML: `[class.recording]` a `[class.processing]`
- ✅ CSS: Animácie pre obe triedy
- ✅ TypeScript: `isRecording` a `isProcessingVoice` flags
- ✅ Icons: 🎤 → 🔴 → ⚙️

**Stačí reštartovať frontend a FUNGUJE TO!** 🚀
