use serde_json::json;
use std::time::{Duration, Instant};
use rodio::{Decoder, MixerDeviceSink, Player, Source};
use rodio::decoder::symphonia::SeekError as SymphoniaSeekError;
use rodio::source::SeekError;
use std::sync::{Arc, Mutex};
use tauri::{AppHandle, Emitter};

const BUFFER_OFFSET_MS: u64 = 64;

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum PlaybackState {
    Stopped,
    Playing,
    Paused,
}

pub struct AudioState {
    #[allow(dead_code)]
    pub sink_handle: MixerDeviceSink,
    pub player: Player,
    pub app_handle: AppHandle,
    pub player_state: Mutex<PlayerState>,
}

pub struct PlayerState {
    pub state: PlaybackState,
    pub track_start_instant: Option<Instant>,
    pub track_position_at_start: Duration,
    pub track_duration: Option<Duration>,
    pub current_filepath: Option<String>,
    pub is_seeking: bool,
}

impl PlayerState {
    pub fn new() -> Self {
        Self {
            state: PlaybackState::Stopped,
            track_start_instant: None,
            track_position_at_start: Duration::ZERO,
            track_duration: None,
            current_filepath: None,
            is_seeking: false,
        }
    }
    
    pub fn current_position(&self) -> Duration {
        match self.state {
            PlaybackState::Playing => {
                let start = self.track_start_instant.expect("playing without start instant");
                self.track_position_at_start + start.elapsed()
            }
            PlaybackState::Paused | PlaybackState::Stopped => self.track_position_at_start,
        }
    }

    pub fn stop(&mut self) {
        self.state = PlaybackState::Stopped;
        self.track_start_instant = None;
        self.track_position_at_start = Duration::ZERO;
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
}

// ======================================================
// tauri commands accessible via invoke in ts frontend
// ======================================================

#[tauri::command]
pub fn play_audio(filepath: String, state: tauri::State<Arc<AudioState>>) -> Result<(), String> {
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
    state.player.play();
    Ok(())
}

#[tauri::command]
pub fn pause_audio(state: tauri::State<Arc<AudioState>>) -> Result<(), String> {
    let mut ps = state.player_state.lock().map_err(|e| e.to_string())?;
    if ps.state == PlaybackState::Playing {
        state.player.pause();
        ps.pause();
    }
    Ok(())
}

#[tauri::command]
pub fn resume_audio(state: tauri::State<Arc<AudioState>>) -> Result<(), String> {
    let mut ps = state.player_state.lock().map_err(|e| e.to_string())?;
    if ps.state == PlaybackState::Paused {
        state.player.play();
        ps.resume();
    }
    Ok(())
}

#[tauri::command]
pub fn seek_audio(position_secs: f64, state: tauri::State<Arc<AudioState>>) -> Result<(), String> {
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
pub fn get_playback_state(state: tauri::State<Arc<AudioState>>) -> Result<serde_json::Value, String> {
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