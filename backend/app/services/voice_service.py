"""
Voice Service - Whisper API + GPT parsing
Converts audio to shift data
"""

import os
from openai import OpenAI
import json
from datetime import date

class VoiceService:
    """Process voice audio and extract shift data"""
    
    def __init__(self):
        api_key = os.getenv('OPENAI_API_KEY')
        if api_key:
            self.client = OpenAI(api_key=api_key)
            self.enabled = True
        else:
            self.client = None
            self.enabled = False
            print("[VOICE] Warning: OPENAI_API_KEY not set. Voice features disabled.")
    
    def process_audio_to_shift_data(self, audio_file):
        """
        Process audio file and extract shift data
        
        Args:
            audio_file: Audio file (mp3, wav, webm, etc.)
        
        Returns:
            dict: Parsed shift data or error
        """
        
        if not self.enabled:
            return {
                'success': False,
                'error': 'Voice service not configured'
            }
        
        try:
            # Step 1: Transcribe audio with Whisper
            print("[VOICE] Transcribing audio with Whisper...")
            transcript = self._transcribe_audio(audio_file)
            
            if not transcript:
                return {
                    'success': False,
                    'error': 'No speech detected in audio'
                }
            
            print(f"[VOICE] Transcript: {transcript}")
            
            # Step 2: Parse transcript with GPT
            print("[VOICE] Parsing transcript with GPT...")
            shift_data = self._parse_transcript_to_shift_data(transcript)
            
            return {
                'success': True,
                'transcript': transcript,
                'data': shift_data
            }
        
        except Exception as e:
            print(f"[VOICE] Error: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _transcribe_audio(self, audio_file):
        """
        Transcribe audio using Whisper API
        
        Args:
            audio_file: FileStorage object from Flask
        
        Returns:
            str: Transcribed text
        """
        
        try:
            # OpenAI Python SDK requires tuple format for file uploads
            # Format: (filename, file_bytes)
            # Reset file pointer to start (important!)
            audio_file.seek(0)
            
            # Get filename with proper extension
            filename = audio_file.filename or 'recording.webm'
            if not any(filename.endswith(ext) for ext in ['.webm', '.mp3', '.wav', '.m4a', '.ogg']):
                filename = 'recording.webm'
            
            print(f"[VOICE] Transcribing file: {filename}")
            print(f"[VOICE] Content type: {audio_file.content_type}")
            
            # Read audio bytes
            audio_bytes = audio_file.read()
            print(f"[VOICE] Audio size: {len(audio_bytes)} bytes")
            
            if len(audio_bytes) == 0:
                raise ValueError("Audio file is empty")
            
            # Create tuple for OpenAI API
            audio_tuple = (filename, audio_bytes)
            
            # Force Slovak language (prevents Ukrainian confusion)
            response = self.client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_tuple,
                language="sk"  # Slovak - prevents misdetection as Ukrainian
            )
            
            return response.text
        
        except Exception as e:
            print(f"[VOICE] Whisper error: {str(e)}")
            import traceback
            traceback.print_exc()
            raise
    
    def _parse_transcript_to_shift_data(self, transcript):
        """
        Parse transcript into structured shift data using GPT
        
        Args:
            transcript: Text from voice
        
        Returns:
            dict: Structured shift data
        """
        
        from datetime import datetime, timedelta
        
        # Calculate date references
        today = date.today()
        yesterday = today - timedelta(days=1)
        
        prompt = f"""You are a form-filling AI assistant for healthcare workers logging their shifts. Parse this voice dictation (in SLOVAK or ENGLISH language) and extract structured data.

Voice transcript: "{transcript}"

TODAY'S DATE: {today.isoformat()}
YESTERDAY'S DATE: {yesterday.isoformat()}

Extract ALL these fields (set to null if not mentioned):

1. **shiftDate**: Date in YYYY-MM-DD format
   - Slovak: "dnes" / English: "today" = {today.isoformat()}
   - Slovak: "včera" / English: "yesterday" = {yesterday.isoformat()}
   - Specific dates WITH YEAR: "30. novembra 2025" / "November 30, 2025" = 2025-11-30
   - Specific dates WITHOUT YEAR (USE CURRENT YEAR {today.year}):
     * Slovak: "30. novembra" / "tridsiatého novembra" = {today.year}-11-30
     * English: "November 30th" / "30th of November" = {today.year}-11-30
     * Slovak: "pätnásteho decembra" = {today.year}-12-15
     * Slovak: "prvého januára" = {today.year}-01-01
   - Month names in Slovak:
     * január=01, február=02, marec=03, apríl=04, máj=05, jún=06
     * júl=07, august=08, september=09, október=10, november=11, december=12
   - Month names in English: January=01, February=02, March=03, April=04, May=05, June=06, July=07, August=08, September=09, October=10, November=11, December=12
   - If ONLY day and month mentioned → ADD CURRENT YEAR ({today.year})
   - **IMPORTANT**: If date is NOT mentioned at all in the transcript → return null (do NOT default to today)
   - Only return today's date if explicitly said "dnes" or "today"

2. **shiftType**: "day" or "night"
   - Slovak: "denná" / "denná zmena" / "cez deň" = "day"
   - Slovak: "nočná" / "nočná zmena" / "cez noc" = "night"
   - English: "day shift" / "morning shift" / "day" = "day"
   - English: "night shift" / "overnight" / "night" = "night"
   - If not mentioned: null

3. **hoursSleptBefore**: number (1-24, WHOLE NUMBERS ONLY)
   - "spal som X hodín" = X
   - "spánok X hodín" = X
   - "spal som X minút" = 1 (any minutes from 0-60 = 1 hour)
   - Slovak number words: "sedem" = 7, "osem" = 8, etc.
   - IMPORTANT: 
     * 0-60 minutes → 1 hour
     * Always return WHOLE numbers, never decimals (5.5 → 6, 7.3 → 7)
     * Maximum 24 hours (anything above → 24)
   - If not mentioned: null

4. **shiftLengthHours**: number (1-24, WHOLE NUMBERS ONLY)
   - "zmena X hodín" = X
   - "pracoval som X hodín" = X
   - "osemhodinová zmena" = 8
   - "X minút" = 1 (any minutes from 0-60 = 1 hour)
   - IMPORTANT: 
     * 0-60 minutes → 1 hour
     * Always return WHOLE numbers, never decimals (8.5 → 9, 12.2 → 12)
     * Maximum 24 hours (anything above → 24)
   - If not mentioned: null

5. **patientsCount**: number (0+)
   - "X pacientov" = X
   - "staral som sa o X pacientov" = X
   - "veľa pacientov" = estimate higher number (20+)
   - "málo pacientov" = estimate lower number (5-10)
   - If not mentioned: null

6. **stressLevel**: number (1-10)
   - Direct numbers: "stres 5" / "úroveň stresu 8" = that number
   - Slovak descriptive phrases (SMART CONTEXT UNDERSTANDING):
     * VYSOKÝ STRES (7-10):
       - "veľký stres" / "veľmi stresujúce" = 8
       - "veľmi vystresovaný" / "extrémne vystresovaný" = 9
       - "hrozný stres" / "strašný stres" = 10
       - "kritická situácia" / "urgentné" = 9
       - "náročné" / "ťažké" / "vyčerpávajúce" = 8
     * STREDNÝ STRES (4-6):
       - "stredný stres" / "normálne" = 5
       - "trochu stresujúce" / "mierny stres" = 4
       - "dosť náročné" = 6
     * NÍZKY STRES (1-3):
       - "malý stres" / "málo vystresovaný" = 3
       - "v pohode" / "v pohode bolo" = 2
       - "žiadny stres" / "bez stresu" / "pokojne" = 1
       - "ľahké" / "jednoduché" = 2
   - Context-based inference:
     * If mentions "kritické prípady" + no stress number → assume 8-9
     * If mentions "unavený" + no stress → assume 6-7
     * If mentions "v pohode" + no stress → assume 2-3
   - If not mentioned at all: null

7. **shiftNote**: string (any additional observations, events, comments)
   - Anything not fitting other fields
   - Critical events: "kritická situácia", "urgentný prípad", "komplikácie"
   - General notes: "bolo rušno", "dosť práce", "unavený"
   - If not mentioned: null

SLOVAK LANGUAGE UNDERSTANDING:
- Numbers: jeden=1, dva=2, tri=3, štyri=4, päť=5, šesť=6, sedem=7, osem=8, deväť=9, desať=10, jedenásť=11, dvanásť=12, pätnásť=15, dvadsať=20, tridsať=30
- Ordinal numbers for dates: prvého=1st, druhého=2nd, tretieho=3rd, štvrtého=4th, piateho=5th, šiesteho=6th, siedmeho=7th, ôsmeho=8th, deviateho=9th, desiateho=10th, jedenásteho=11th, dvanásteho=12th, trinásteho=13th, štrnásteho=14th, pätnásteho=15th, dvadsiateho=20th, dvadsiateho prvého=21st, tridsiatého=30th, tridsiatého prvého=31st
- Months: január/januára=01, február/februára=02, marec/marca=03, apríl/apríla=04, máj/mája=05, jún/júna=06, júl/júla=07, august/augusta=08, september/septembra=09, október/októbra=10, november/novembra=11, december/decembra=12
- IMPORTANT: If year is NOT mentioned, ALWAYS use current year {today.year}
- Day/Night: denná=day, nočná=night, deň=day, noc=night
- Time: hodín=hours, hodiny=hours
- Patients: pacient=patient, pacienti=patients, pacientov=patients
- Stress phrases:
  * HIGH (8-10): veľmi vystresovaný, extrémne vystresovaný, hrozný stres, veľký stres, kritické, urgentné, náročné, ťažké, vyčerpávajúce
  * MEDIUM (4-6): stredný stres, normálne, trochu stresujúce, mierny stres, dosť náročné
  * LOW (1-3): málo vystresovaný, v pohode, žiadny stres, bez stresu, pokojne, ľahké, jednoduché
- Notes: kritický=critical, urgentný=urgent, komplikácie=complications, rušno=busy, unavený=tired

RESPOND WITH ONLY VALID JSON. NO OTHER TEXT.

Example outputs:

Input: "dnes som mal dennú zmenu osem hodín, spal som sedem hodín, pätnásť pacientov, stres šesť"
Output:
{{
  "shiftDate": "{today.isoformat()}",
  "shiftType": "day",
  "hoursSleptBefore": 7,
  "shiftLengthHours": 8,
  "patientsCount": 15,
  "stressLevel": 6,
  "shiftNote": null
}}

Input: "včera nočná zmena dvanásť hodín, spal som len štyri hodiny, dvadsať pacientov, stres deväť, boli kritické prípady"
Output:
{{
  "shiftDate": "{yesterday.isoformat()}",
  "shiftType": "night",
  "hoursSleptBefore": 4,
  "shiftLengthHours": 12,
  "patientsCount": 20,
  "stressLevel": 9,
  "shiftNote": "boli kritické prípady"
}}

Input: "denná zmena veľa práce unavený som"
Output:
{{
  "shiftDate": null,
  "shiftType": "day",
  "hoursSleptBefore": null,
  "shiftLengthHours": null,
  "patientsCount": null,
  "stressLevel": null,
  "shiftNote": "veľa práce unavený som"
}}

Input: "dvanásť hodín pracoval som, dvadsať pacientov, stres osem"
Output:
{{
  "shiftDate": null,
  "shiftType": "day",
  "hoursSleptBefore": null,
  "shiftLengthHours": null,
  "patientsCount": null,
  "stressLevel": null,
Input: "prvého decembra nočná zmena stres osem"
Output:
{{
  "shiftDate": "{today.year}-12-01",
  "shiftType": "night",
  "hoursSleptBefore": null,
  "shiftLengthHours": null,
  "patientsCount": null,
  "stressLevel": 8,
  "shiftNote": null
}}

Input: "pätnásteho novembra denná zmena osem hodín"
Output:
{{
  "shiftDate": "{today.year}-11-15",
  "shiftType": "day",
  "hoursSleptBefore": null,
  "shiftLengthHours": 8,
  "patientsCount": null,
  "stressLevel": null,
  "shiftNote": null
}}

Input: "nočná zmena veľmi som vystresovaný boli urgentné prípady"
Output:

Input: "nočná zmena veľmi som vystresovaný boli urgentné prípady"
Output:
{{
  "shiftDate": "{today.isoformat()}",
  "shiftType": "night",
  "hoursSleptBefore": null,
  "shiftLengthHours": null,
  "patientsCount": null,
  "stressLevel": 9,
  "shiftNote": "boli urgentné prípady"
}}

Input: "denná osem hodín v pohode bolo žiadny stres päť pacientov"
Output:
{{
  "shiftDate": "{today.isoformat()}",
  "shiftType": "day",
  "hoursSleptBefore": null,
  "shiftLengthHours": 8,
  "patientsCount": 5,
  "stressLevel": 1,
  "shiftNote": null
}}

Input: "málo vystresovaný som trochu unavený"
Output:
{{
  "shiftDate": "{today.isoformat()}",
  "shiftType": null,
  "hoursSleptBefore": null,
  "shiftLengthHours": null,
  "patientsCount": null,
  "stressLevel": 3,
  "shiftNote": "trochu unavený"
}}

Now parse the transcript and respond with JSON only:"""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful assistant that extracts structured data from healthcare worker voice dictation in Slovak language. Always respond with valid JSON only. Never add explanations or other text."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.2,  # Lower temperature for more consistent parsing
                max_tokens=500
            )
            
            ai_response = response.choices[0].message.content
            print(f"[VOICE] GPT response: {ai_response}")
            
            # Parse JSON
            parsed_data = json.loads(ai_response)
            
            return parsed_data
        
        except json.JSONDecodeError as e:
            print(f"[VOICE] JSON parse error: {str(e)}")
            raise ValueError("Failed to parse AI response as JSON")
        
        except Exception as e:
            print(f"[VOICE] GPT error: {str(e)}")
            raise
