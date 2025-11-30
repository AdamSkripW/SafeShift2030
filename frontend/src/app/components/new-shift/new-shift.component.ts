import { Component, OnInit, ChangeDetectorRef, NgZone } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import { Router, ActivatedRoute } from '@angular/router';
import { NavbarComponent } from '../../components/navbar/navbar.component';
import { ShiftService } from '../../services/shift.service';
import { ShiftFormData, ShiftType } from '../../models/shift.model';
import { HttpClient } from '@angular/common/http';

@Component({
  selector: 'app-new-shift',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, NavbarComponent],
  templateUrl: './new-shift.component.html',
  styleUrls: ['./new-shift.component.css']
})
export class NewShiftComponent implements OnInit {
  shiftForm: FormGroup;
  submitted = false;
  loading = false;
  errorMessage = '';
  isEditMode = false;
  shiftId: number | null = null;

  shiftTypes: ShiftType[] = ['day', 'night'];
  stressLevels = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10];

  // Voice dictation with Whisper API
  isRecording = false;
  mediaRecorder: MediaRecorder | null = null;
  audioChunks: Blob[] = [];
  transcript = '';
  isProcessingVoice = false;
  voiceError = '';
  silenceTimeout: any = null;
  audioContext: AudioContext | null = null;
  analyser: AnalyserNode | null = null;
  missingFields: string[] = [];
  voicePrompt = '';

  constructor(
    private fb: FormBuilder,
    private shiftService: ShiftService,
    private router: Router,
    private route: ActivatedRoute,
    private http: HttpClient,
    private cdr: ChangeDetectorRef,
    private zone: NgZone
  ) {
    this.shiftForm = this.fb.group({
      shiftDate: [this.getTodayDate(), Validators.required],
      hoursSleptBefore: [7, [Validators.required, Validators.min(0), Validators.max(24)]],
      shiftType: ['day', Validators.required],
      shiftLengthHours: [8, [Validators.required, Validators.min(1), Validators.max(24)]],
      patientsCount: [0, [Validators.required, Validators.min(0)]],
      stressLevel: [5, [Validators.required, Validators.min(1), Validators.max(10)]],
      shiftNote: ['']
    });
  }

  ngOnInit(): void {
    // Check if we're in edit mode
    const id = this.route.snapshot.paramMap.get('id');
    if (id) {
      this.isEditMode = true;
      this.shiftId = parseInt(id, 10);
      this.loadShiftData(this.shiftId);
    }
  }

  /**
   * Load shift data for editing
   */
  loadShiftData(shiftId: number): void {
    this.loading = true;
    this.shiftService.getShiftById(shiftId).subscribe({
      next: (shift) => {
        console.log('Loaded shift data:', shift);
        
        // Format date to YYYY-MM-DD for input[type="date"]
        let formattedDate = this.getTodayDate();
        if (shift.ShiftDate) {
          formattedDate = shift.ShiftDate.includes('T') 
            ? shift.ShiftDate.split('T')[0] 
            : shift.ShiftDate;
        }
        
        this.shiftForm.patchValue({
          shiftDate: formattedDate,
          hoursSleptBefore: shift.HoursSleptBefore,
          shiftType: shift.ShiftType,
          shiftLengthHours: shift.ShiftLengthHours,
          patientsCount: shift.PatientsCount,
          stressLevel: shift.StressLevel,
          shiftNote: shift.ShiftNote || ''
        });
        this.loading = false;
        this.cdr.detectChanges();
      },
      error: (error) => {
        console.error('Error loading shift:', error);
        this.errorMessage = 'Failed to load shift data';
        this.loading = false;
        this.cdr.detectChanges();
      }
    });
  }
  /**
   * Start voice recording using MediaRecorder
   */
  async startVoiceRecording(): Promise<void> {
    try {
      console.log('🎤 Starting voice recording...');
      
      // Clear previous errors and prompts (but keep form data for incremental updates)
      this.transcript = '';
      this.voiceError = '';
      this.voicePrompt = '';
      this.audioChunks = [];
      
      // Request microphone access
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      console.log('✅ Microphone access granted');
      
      // Setup audio context for silence detection
      this.audioContext = new AudioContext();
      const source = this.audioContext.createMediaStreamSource(stream);
      this.analyser = this.audioContext.createAnalyser();
      this.analyser.fftSize = 2048;
      source.connect(this.analyser);
      
      // Create MediaRecorder with proper options
      const options: MediaRecorderOptions = {
        mimeType: 'audio/webm;codecs=opus'
      };
      
      this.mediaRecorder = new MediaRecorder(stream, options);
      
      console.log(`✅ MediaRecorder created with ${options.mimeType}`);
      
      // Collect audio chunks
      this.mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          this.audioChunks.push(event.data);
          console.log(`📦 Audio chunk: ${event.data.size} bytes`);
        }
      };
      
      // When recording stops, process audio
      this.mediaRecorder.onstop = () => {
        this.zone.run(() => {
          console.log('⏹️ Recording stopped, processing...');
          this.isRecording = false;
          this.cdr.detectChanges(); // Force update
          console.log('🔴 Recording stopped - isRecording =', this.isRecording);
          this.processRecording();
        });
        
        // Stop all tracks to release microphone
        stream.getTracks().forEach(track => track.stop());
      };
      
      // Start recording
      this.mediaRecorder.start();
      this.zone.run(() => {
        this.isRecording = true;
        this.cdr.detectChanges(); // Force update UI
        console.log('🔴 Recording started - isRecording =', this.isRecording);
        
        // Start monitoring for silence AFTER isRecording is true
        this.monitorSilence();
      });
      
    } catch (error: any) {
      console.error('❌ Microphone error:', error);
      this.voiceError = 'Cannot access microphone. Please allow microphone permissions.';
      this.isRecording = false;
      this.cdr.detectChanges();
    }
  }

  /**
   * Stop voice recording
   */
  stopVoiceRecording(): void {
    if (this.mediaRecorder && this.mediaRecorder.state === 'recording') {
      console.log('⏹️ Stopping voice recording...');
      this.mediaRecorder.stop();
    }
    
    // Clear silence detection
    if (this.silenceTimeout) {
      clearTimeout(this.silenceTimeout);
      this.silenceTimeout = null;
    }
    
    // Close audio context
    if (this.audioContext) {
      this.audioContext.close();
      this.audioContext = null;
    }
  }

  /**
   * Monitor audio levels and auto-stop on silence
   */
  private monitorSilence(): void {
    if (!this.analyser || !this.isRecording) {
      console.log('⚠️ Monitoring stopped - analyser:', !!this.analyser, 'isRecording:', this.isRecording);
      return;
    }
    
    const bufferLength = this.analyser.frequencyBinCount;
    const dataArray = new Uint8Array(bufferLength);
    this.analyser.getByteTimeDomainData(dataArray);
    
    // Calculate volume (RMS)
    let sum = 0;
    for (let i = 0; i < bufferLength; i++) {
      const value = (dataArray[i] - 128) / 128;
      sum += value * value;
    }
    const rms = Math.sqrt(sum / bufferLength);
    const volume = rms * 100;
    
    // Log volume for debugging (every 10 frames)
    if (Math.random() < 0.1) {
      console.log('🔊 Volume:', volume.toFixed(2));
    }
    
    // If volume is below threshold (silence), start countdown
    if (volume < 5) {  // Increased threshold from 2 to 5 for better detection
      if (!this.silenceTimeout) {
        console.log('🤫 Silence detected, starting 3-second countdown...');
        this.silenceTimeout = setTimeout(() => {
          console.log('🔇 3 seconds of silence - auto-stopping recording');
          this.stopVoiceRecording();
        }, 3000); // 3 seconds of silence
      }
    } else {
      // Voice detected, clear timeout
      if (this.silenceTimeout) {
        console.log('🗣️ Voice detected - canceling auto-stop');
        clearTimeout(this.silenceTimeout);
        this.silenceTimeout = null;
      }
    }
    
    // Continue monitoring
    if (this.isRecording) {
      requestAnimationFrame(() => this.monitorSilence());
    }
  }

  /**
   * Process recorded audio and send to backend
   */
  private processRecording(): void {
    if (this.audioChunks.length === 0) {
      console.error('❌ No audio chunks recorded');
      this.voiceError = 'No audio recorded. Try again.';
      this.cdr.detectChanges();
      return;
    }

    this.zone.run(() => {
      this.isProcessingVoice = true;
      this.isRecording = false;
      this.voiceError = '';
      this.cdr.detectChanges(); // Force update to show processing state
      console.log('⚙️ Processing started - isProcessingVoice =', this.isProcessingVoice);
    });

    // Create audio blob
    const audioBlob = new Blob(this.audioChunks, { type: 'audio/webm' });
    console.log(`📦 Audio blob created: ${audioBlob.size} bytes`);
    
    // Create FormData
    const formData = new FormData();
    formData.append('audio', audioBlob, 'recording.webm');
    console.log('📤 Sending to backend...');
    
    // Send to backend using Observable (not Promise)
    this.http.post<any>('http://localhost:5000/api/shifts/parse-voice', formData).subscribe({
      next: (response) => {
        this.zone.run(() => {
          console.log('✅ Backend response:', response);
          
          if (response.success) {
            this.transcript = response.transcript;
            this.fillFormFromVoiceData(response.data);
            console.log('✅ Form filled successfully!');
            this.voiceError = '';
          } else {
            console.error('❌ Backend returned error:', response.error);
            this.voiceError = response.error || 'Failed to process voice';
          }
          this.isProcessingVoice = false;
          this.cdr.detectChanges(); // Force update to hide processing state
        });
      },
      error: (error) => {
        this.zone.run(() => {
          console.error('❌ HTTP error:', error);
          this.voiceError = error.error?.error || error.message || 'Failed to process voice. Check backend.';
          this.isProcessingVoice = false;
          this.cdr.detectChanges();
        });
      },
      complete: () => {
        console.log('✅ Request completed - isProcessingVoice =', this.isProcessingVoice);
      }
    });
  }

  /**
   * Fill form with voice data (incremental - only updates provided fields)
   */
  private fillFormFromVoiceData(data: any): void {
    console.log('📝 Filling form with voice data:', data);
    
    // Only update fields that were provided (incremental update)
    // IMPORTANT: Preserve existing date if not explicitly mentioned in voice
    const currentDate = this.shiftForm.value.shiftDate;
    if (data.shiftDate) {
      // Only update if it's a specific date (not the default today)
      if (!currentDate || data.shiftDate !== this.getTodayDate()) {
        this.shiftForm.patchValue({ shiftDate: data.shiftDate });
        console.log('📅 Date updated to:', data.shiftDate);
      } else {
        console.log('📅 Preserving existing date:', currentDate);
      }
    }
    
    if (data.hoursSleptBefore != null) {
      // Rounding rules: 0-60 min → 1 hour, round to whole, cap at 24
      let roundedSleep = Math.round(data.hoursSleptBefore);
      if (roundedSleep === 0 && data.hoursSleptBefore > 0) roundedSleep = 1; // 0-60 min → 1
      if (roundedSleep > 24) roundedSleep = 24; // Cap at 24
      this.shiftForm.patchValue({ hoursSleptBefore: roundedSleep });
      console.log(`😴 Sleep hours: ${data.hoursSleptBefore} → ${roundedSleep}`);
    }
    if (data.shiftType) this.shiftForm.patchValue({ shiftType: data.shiftType });
    if (data.shiftLengthHours != null) {
      // Rounding rules: 0-60 min → 1 hour, round to whole, cap at 24
      let roundedLength = Math.round(data.shiftLengthHours);
      if (roundedLength === 0 && data.shiftLengthHours > 0) roundedLength = 1; // 0-60 min → 1
      if (roundedLength > 24) roundedLength = 24; // Cap at 24
      this.shiftForm.patchValue({ shiftLengthHours: roundedLength });
      console.log(`⏱️ Shift length: ${data.shiftLengthHours} → ${roundedLength}`);
    }
    if (data.patientsCount != null) this.shiftForm.patchValue({ patientsCount: data.patientsCount });
    if (data.stressLevel != null) this.shiftForm.patchValue({ stressLevel: data.stressLevel });
    if (data.shiftNote) {
      // Append to existing note if present
      const currentNote = this.shiftForm.value.shiftNote || '';
      const newNote = currentNote ? `${currentNote} ${data.shiftNote}` : data.shiftNote;
      this.shiftForm.patchValue({ shiftNote: newNote });
    }
    
    // Check for missing required fields
    this.checkMissingFields();
    
    console.log('✅ Form updated incrementally!');
  }

  /**
   * Check for missing required fields and generate voice prompt
   */
  private checkMissingFields(): void {
    const formValues = this.shiftForm.value;
    this.missingFields = [];
    
    // Check required fields
    if (!formValues.shiftLengthHours || formValues.shiftLengthHours === 0) {
      this.missingFields.push('shift length');
    }
    if (!formValues.patientsCount && formValues.patientsCount !== 0) {
      this.missingFields.push('patients count');
    }
    if (!formValues.stressLevel) {
      this.missingFields.push('stress level');
    }
    
    // Generate voice prompt if fields are missing
    if (this.missingFields.length > 0) {
      const missingFieldsSk = this.missingFields.map(field => {
        switch(field) {
          case 'shift length': return 'dĺžku zmeny';
          case 'patients count': return 'počet pacientov';
          case 'stress level': return 'úroveň stresu';
          default: return field;
        }
      });
      
      this.voicePrompt = `⚠️ Chýbajúce údaje: ${missingFieldsSk.join(', ')}. Nahraj znova a doplň ich.`;
      console.log('⚠️ Missing fields:', this.missingFields);
      console.log('💬 Voice prompt:', this.voicePrompt);
      
      // Speak the prompt using Web Speech API
      if ('speechSynthesis' in window) {
        const utterance = new SpeechSynthesisUtterance(this.voicePrompt);
        utterance.lang = 'sk-SK';
        utterance.rate = 0.9;
        utterance.pitch = 1.0;
        window.speechSynthesis.speak(utterance);
        console.log('🔊 Speaking prompt');
      }
    } else {
      this.voicePrompt = '';
      console.log('✅ All required fields filled!');
    }
  }

  /**
   * Get today's date in YYYY-MM-DD format
   */
  private getTodayDate(): string {
    const today = new Date();
    return today.toISOString().split('T')[0];
  }

  /**
   * Getter for easy access to form controls
   */
  get f() {
    return this.shiftForm.controls;
  }

  /**
   * Handle form submission
   */
  onSubmit(): void {
    this.submitted = true;
    this.errorMessage = '';

    if (this.shiftForm.invalid) {
      return;
    }

    this.loading = true;

    const shiftData: ShiftFormData = {
      ShiftDate: this.shiftForm.value.shiftDate,
      HoursSleptBefore: Number(this.shiftForm.value.hoursSleptBefore),
      ShiftType: this.shiftForm.value.shiftType,
      ShiftLengthHours: Number(this.shiftForm.value.shiftLengthHours),
      PatientsCount: Number(this.shiftForm.value.patientsCount),
      StressLevel: Number(this.shiftForm.value.stressLevel),
      ShiftNote: this.shiftForm.value.shiftNote?.trim() || undefined
    };

    const serviceCall = this.isEditMode && this.shiftId
      ? this.shiftService.updateShift(this.shiftId, shiftData)
      : this.shiftService.createShift(shiftData);

    serviceCall.subscribe({
      next: (shift) => {
        console.log(`Shift ${this.isEditMode ? 'updated' : 'created'} successfully:`, shift);
        // Navigate to shifts dashboard
        this.router.navigate(['/shifts']);
      },
      error: (error) => {
        console.error(`Error ${this.isEditMode ? 'updating' : 'creating'} shift:`, error);
        this.errorMessage = error.error?.message || `Failed to ${this.isEditMode ? 'update' : 'create'} shift. Please try again.`;
        this.loading = false;
      },
      complete: () => {
        this.loading = false;
      }
    });
  }

  /**
   * Cancel and go back
   */
  onCancel(): void {
    this.router.navigate(['/shifts']);
  }
}
