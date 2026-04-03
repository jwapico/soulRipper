use rodio::{Decoder, DeviceSinkBuilder, DeviceSinkError, MixerDeviceSink, Player, Source};
use rodio::source::SeekError;
use rodio::decoder::symphonia::SeekError as SymphoniaSeekError;
use serde_json::json;
use std::sync::{Arc, Mutex};
use std::time::{Duration, Instant};
use std::thread;
use tauri::{AppHandle, Emitter, Manager};

// Buffer offset to account for audio‑device latency (in milliseconds)
const BUFFER_OFFSET_MS: u64 = 50;

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
enum PlaybackState {
    Stopped,
    Playing,
    Paused,
}

struct PlayerState {
    state: PlaybackState,
    track_start_instant: Option<Instant>,
    track_position_at_start: Duration,
    track_duration: Option<Duration>,
    current_filepath: Option<String>,
    is_seeking: bool,
}

impl PlayerState {
    fn new() -> Self {
        Self {
            state: PlaybackState::Stopped,
            track_start_instant: None,
            track_position_at_start: Duration::ZERO,
            track_duration: None,
            current_filepath: None,
            is_seeking: false,
        }
    }

    fn current_position(&self) -> Duration {
        match self.state {
            PlaybackState::Playing => {
                let start = self.track_start_instant.expect("playing without start instant");
                self.track_position_at_start + start.elapsed()
            }
            PlaybackState::Paused | PlaybackState::Stopped => self.track_position_at_start,
        }
    }

    fn start_playback(&mut self, filepath: String, duration: Option<Duration>) {
        self.state = PlaybackState::Playing;
        self.track_start_instant = Some(Instant::now());
        self.track_position_at_start = Duration::ZERO;
        self.track_duration = duration;
        self.current_filepath = Some(filepath);
    }

    fn pause(&mut self) {
        if self.state == PlaybackState::Playing {
            // Subtract a small buffer offset to compensate for audio‑device latency
            let raw_position = self.current_position();
            let adjusted = raw_position.saturating_sub(Duration::from_millis(BUFFER_OFFSET_MS));
            self.state = PlaybackState::Paused;
            self.track_position_at_start = adjusted;
            self.track_start_instant = None;
        }
    }

    fn resume(&mut self) {
        if self.state == PlaybackState::Paused {
            self.state = PlaybackState::Playing;
            self.track_start_instant = Some(Instant::now());
        }
    }

    fn seek(&mut self, position: Duration) {
        self.track_position_at_start = position;
        if self.state == PlaybackState::Playing {
            self.track_start_instant = Some(Instant::now());
        }
    }

    fn stop(&mut self) {
        self.state = PlaybackState::Stopped;
        self.track_start_instant = None;
        self.track_position_at_start = Duration::ZERO;
    }
}

struct AudioState {
    #[allow(dead_code)]
    sink_handle: MixerDeviceSink,
    player: Player,
    app_handle: AppHandle,
    player_state: Mutex<PlayerState>,
}

#[tauri::command]
fn play_audio(filepath: String, state: tauri::State<Arc<AudioState>>) -> Result<(), String> {
    state.player.stop();
    
    let file = std::fs::File::open(&filepath)
        .map_err(|e| e.to_string())?;
    let file_len = file.metadata().map(|m| m.len()).ok();
    let mut builder = Decoder::builder()
        .with_data(file)
        .with_coarse_seek(true);
    if let Some(len) = file_len {
        builder = builder.with_byte_len(len);
    }
    let source = builder.build()
        .map_err(|e| e.to_string())?;
    
    let duration = source.total_duration();
    
    let mut ps = state.player_state.lock().map_err(|e| e.to_string())?;
    ps.start_playback(filepath, duration);
    
    state.player.append(source);
    // Ensure the player is not paused when starting a new track
    state.player.play();
    Ok(())
}

#[tauri::command]
fn pause_audio(state: tauri::State<Arc<AudioState>>) -> Result<(), String> {
    let mut ps = state.player_state.lock().map_err(|e| e.to_string())?;
    if ps.state == PlaybackState::Playing {
        state.player.pause();
        ps.pause();
    }
    Ok(())
}

#[tauri::command]
fn resume_audio(state: tauri::State<Arc<AudioState>>) -> Result<(), String> {
    let mut ps = state.player_state.lock().map_err(|e| e.to_string())?;
    if ps.state == PlaybackState::Paused {
        state.player.play();
        ps.resume();
    }
    Ok(())
}

#[tauri::command]
fn seek_audio(position_secs: f64, state: tauri::State<Arc<AudioState>>) -> Result<(), String> {
    let mut ps = state.player_state.lock().map_err(|e| e.to_string())?;
    let position = Duration::from_secs_f64(position_secs);
    
    if let Some(duration) = ps.track_duration {
        if position > duration {
            return Err("Seek position exceeds track duration".into());
        }
    }
    
    ps.is_seeking = true;
    
    // Try normal seek first
    match state.player.try_seek(position) {
        Ok(()) => {
            ps.seek(position);
            // Emit immediate position update
            let position_f64 = position.as_secs_f64();
            let duration_f64 = ps.track_duration.map(|d| d.as_secs_f64());
            let payload = json!({
                "position": position_f64,
                "duration": duration_f64,
                "state": format!("{:?}", ps.state).to_lowercase(),
            });
            state.app_handle.emit("audio://position_update", payload)
                .map_err(|e| e.to_string())?;
            ps.is_seeking = false;
            Ok(())
        }
        Err(SeekError::SymphoniaDecoder(SymphoniaSeekError::RandomAccessNotSupported)) |
        Err(SeekError::SymphoniaDecoder(SymphoniaSeekError::AccurateSeekNotSupported)) => {
            // Fallback: restart decoder and skip to target position
            let filepath = match ps.current_filepath.clone() {
                Some(fp) => fp,
                None => {
                    ps.is_seeking = false;
                    return Err("No current filepath".into());
                }
            };
            let was_playing = ps.state == PlaybackState::Playing;
            // Stop current player
            state.player.stop();
            // Create new decoder
            let file = std::fs::File::open(&filepath)
                .map_err(|e| e.to_string())?;
            let file_len = file.metadata().map(|m| m.len()).ok();
            let mut builder = Decoder::builder()
                .with_data(file)
                .with_coarse_seek(true);
            if let Some(len) = file_len {
                builder = builder.with_byte_len(len);
            }
            let source = builder.build().map_err(|e| e.to_string())?;
            let skipped = source.skip_duration(position);
            let duration = skipped.total_duration();
            // Update player state
            ps.track_duration = duration;
            ps.track_position_at_start = position;
            if was_playing {
                ps.track_start_instant = Some(Instant::now());
                ps.state = PlaybackState::Playing;
            } else {
                ps.track_start_instant = None;
                ps.state = PlaybackState::Paused;
            }
            // Append new source
            state.player.append(skipped);
            // Ensure the player is playing (if it was playing before)
            if was_playing {
                state.player.play();
            }
            // Emit position update
            let position_f64 = position.as_secs_f64();
            let duration_f64 = duration.map(|d| d.as_secs_f64());
            let payload = json!({
                "position": position_f64,
                "duration": duration_f64,
                "state": format!("{:?}", ps.state).to_lowercase(),
            });
            state.app_handle.emit("audio://position_update", payload)
                .map_err(|e| e.to_string())?;
            ps.is_seeking = false;
            Ok(())
        }
        Err(e) => {
            ps.is_seeking = false;
            Err(e.to_string())
        }
    }
}

#[tauri::command]
fn get_playback_state(state: tauri::State<Arc<AudioState>>) -> Result<serde_json::Value, String> {
    let ps = state.player_state.lock().map_err(|e| e.to_string())?;
    let position = ps.current_position().as_secs_f64();
    let duration = ps.track_duration.map(|d| d.as_secs_f64());
    
    Ok(json!({
        "state": format!("{:?}", ps.state).to_lowercase(),
        "position": position,
        "duration": duration,
        "filepath": ps.current_filepath,
    }))
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .setup(|app| {
            // Open default audio sink and create a player
            let sink_handle = DeviceSinkBuilder::open_default_sink()
                .map_err(|e: DeviceSinkError| e.to_string())?;
            let player = Player::connect_new(sink_handle.mixer());
            
            let app_handle = app.handle().clone();
            let audio_state = Arc::new(AudioState {
                sink_handle,
                player,
                app_handle,
                player_state: Mutex::new(PlayerState::new()),
            });
            
            let thread_state = Arc::clone(&audio_state);
            
            thread::spawn(move || {
                loop {
                    thread::sleep(Duration::from_millis(100));
                    
                    let (position, duration, current_state, track_ended, is_seeking) = {
                        let ps = thread_state.player_state.lock().unwrap();
                        let position = ps.current_position();
                        let duration = ps.track_duration;
                        let track_ended = ps.state == PlaybackState::Playing 
                            && thread_state.player.empty();
                        (position, duration, ps.state, track_ended, ps.is_seeking)
                    };
                    
                    let position_f64 = position.as_secs_f64();
                    let duration_f64 = duration.map(|d| d.as_secs_f64());
                    
                    if !is_seeking {
                        let payload = json!({
                            "position": position_f64,
                            "duration": duration_f64,
                            "state": format!("{:?}", current_state).to_lowercase(),
                        });
                        let _ = thread_state.app_handle.emit("audio://position_update", payload);
                    }
                    
                    if track_ended {
                        let mut ps = thread_state.player_state.lock().unwrap();
                        if ps.state == PlaybackState::Playing && thread_state.player.empty() {
                            thread_state.player.stop();
                            ps.stop();
                            let end_payload = json!({
                                "filepath": ps.current_filepath.clone(),
                            });
                            drop(ps);
                            let _ = thread_state.app_handle.emit("audio://track_ended", end_payload);
                        }
                    }
                }
            });
            
            app.manage(audio_state);
            Ok(())
        })
        .invoke_handler(tauri::generate_handler![
            play_audio,
            pause_audio,
            resume_audio,
            seek_audio,
            get_playback_state
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
