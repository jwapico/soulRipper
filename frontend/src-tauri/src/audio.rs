use std::time::{Duration, Instant};
use serde_json::json;
use rodio::decoder::symphonia::SeekError as SymphoniaSeekError;
use rodio::source::SeekError;
use rodio::Source;
use tauri::Emitter;
use std::sync::{Arc, Mutex};

const BUFFER_OFFSET_MS: u64 = 64;

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum PlayerState {
    Stopped,
    Playing,
    Paused,
}

pub struct PlaybackManager {
    pub player_state: PlayerState,
    pub start_instant: Option<Instant>,
    pub position: Duration,
    pub total_duration: Option<Duration>,
    pub filepath: Option<String>,
    pub is_seeking: bool,
}

impl PlaybackManager {
    pub fn new() -> Self {
        Self {
            player_state: PlayerState::Stopped,
            start_instant: None,
            position: Duration::ZERO,
            total_duration: None,
            filepath: None,
            is_seeking: false,
        }
    }

    fn start(&mut self, filepath: String, total_duration: Option<Duration>) {
        self.player_state = PlayerState::Playing;
        self.start_instant = Some(Instant::now());
        self.position = Duration::ZERO;
        self.total_duration = total_duration;
        self.filepath = Some(filepath);
    }

    pub fn stop(&mut self) {
        self.player_state = PlayerState::Stopped;
        self.start_instant = None;
        self.position = Duration::ZERO;
    }

    fn pause(&mut self) {
        if self.player_state == PlayerState::Playing {
            let raw_position = self.get_current_position();
            let adjusted_pos = raw_position.saturating_sub(Duration::from_millis(BUFFER_OFFSET_MS));
            self.player_state = PlayerState::Paused;
            self.position = adjusted_pos;
            self.start_instant = None;
        }
    }

    fn resume(&mut self) {
        if self.player_state == PlayerState::Paused {
            self.player_state = PlayerState::Playing;
            self.start_instant = Some(Instant::now());
        }
    }

    fn seek(&mut self, position: Duration) {
        self.is_seeking = true;
        self.position = position;
        if self.player_state == PlayerState::Playing {
            self.start_instant = Some(Instant::now());
        }
    }

    pub fn get_current_position(&self) -> Duration {
        match self.player_state {
            PlayerState::Playing => self.position + self.start_instant.expect("playing without start instant").elapsed(),
            PlayerState::Paused | PlayerState::Stopped => self.position,
        }
    }
}

pub struct AppAudioState {
    #[allow(dead_code)]
    pub sink_handle: rodio::MixerDeviceSink,
    pub rodio_player: rodio::Player,
    pub app_handle: tauri::AppHandle,
    pub playback_state: Mutex<PlaybackManager>,
}

// =======================================================
//    tauri commands accessible via invoke in frontend
// =======================================================

#[tauri::command]
pub fn play_audio(filepath: String, state: tauri::State<Arc<AppAudioState>>) -> Result<(), String> {
    // stop existing playback
    state.rodio_player.stop();

    // init rodios Decoder builder
    let file = std::fs::File::open(&filepath).map_err(|e| e.to_string())?;
    let file_len = file.metadata().map(|m| m.len()).ok();
    let mut builder = rodio::Decoder::builder()
        .with_data(file)
        .with_coarse_seek(true);

    // need for seeking
    if let Some(len) = file_len {
        builder = builder.with_byte_len(len);
    }

    let audio_source = builder.build().map_err(|e| e.to_string())?;

    // update state in PlaybackManager
    let mut playback_manager = state.playback_state.lock().map_err(|e| e.to_string())?;
    playback_manager.start(filepath, audio_source.total_duration());
    
    // add source to Player and play
    state.rodio_player.append(audio_source);
    state.rodio_player.play();
    Ok(())
}

#[tauri::command]
pub fn pause_audio(state: tauri::State<Arc<AppAudioState>>) -> Result<(), String> {
    let mut playback_manager = state.playback_state.lock().map_err(|e| e.to_string())?;

    if playback_manager.player_state == PlayerState::Playing {
        state.rodio_player.pause();
        playback_manager.pause();
    }

    Ok(())
}

#[tauri::command]
pub fn resume_audio(state: tauri::State<Arc<AppAudioState>>) -> Result<(), String> {
    let mut playback_manager = state.playback_state.lock().map_err(|e| e.to_string())?;
    
    if playback_manager.player_state == PlayerState::Paused {
        state.rodio_player.play();
        playback_manager.resume();
    }

    Ok(())
}

#[tauri::command]
pub fn seek_audio(position_secs: f64, state: tauri::State<Arc<AppAudioState>>) -> Result<(), String> {
    let mut playback_manager = state.playback_state.lock().map_err(|e| e.to_string())?;
    
    let position = Duration::from_secs_f64(position_secs);
    if let Some(duration) = playback_manager.total_duration {
        if position > duration {
            return Err("Seek position exceeds track duration".into());
        }
    }
    
    match state.rodio_player.try_seek(position) {
        Ok(()) => {
            // update state in pm
            playback_manager.seek(position);

            // create and emit frontend update msg
            let position_f64 = position.as_secs_f64();
            let duration_f64 = playback_manager.total_duration.map(|d| d.as_secs_f64());
            let payload = json!({
                "position": position_f64,
                "duration": duration_f64,
                "state": format!("{:?}", playback_manager.player_state).to_lowercase(),
            });
            state.app_handle.emit("audio://position_update", payload).map_err(|e| e.to_string())?;

            playback_manager.is_seeking = false;
            Ok(())
        }
        // if symphonia rejects seeking, build entirely new source and skip forward
        Err(SeekError::SymphoniaDecoder(SymphoniaSeekError::RandomAccessNotSupported)) |
        Err(SeekError::SymphoniaDecoder(SymphoniaSeekError::AccurateSeekNotSupported)) => {
            state.rodio_player.stop();
            
            // init new builder
            let filepath = playback_manager.filepath.clone().ok_or("no filepath")?;
            let file = std::fs::File::open(&filepath).map_err(|e| e.to_string())?;
            let file_len = file.metadata().map(|m| m.len()).ok();
            let mut builder = rodio::Decoder::builder()
                .with_data(file)
                .with_coarse_seek(true);
            if let Some(len) = file_len {
                builder = builder.with_byte_len(len);
            }

            // build source then skip forward to seeked position
            let source = builder.build().map_err(|e| e.to_string())?;
            let source_seeked = source.skip_duration(position);
            let seeked_duration = source_seeked.total_duration();

            // update PlaybackManager state
            playback_manager.total_duration = seeked_duration;
            playback_manager.position = position;
            let was_playing = playback_manager.player_state == PlayerState::Playing;
            if was_playing {
                playback_manager.start_instant = Some(Instant::now());
                playback_manager.player_state = PlayerState::Playing;
            } else {
                playback_manager.start_instant = None;
                playback_manager.player_state = PlayerState::Paused;
            }

            // update the rodio_player with the new source
            state.rodio_player.append(source_seeked);
            if was_playing {
                state.rodio_player.play();
            }

            // create and emit frontend message
            let position_f64 = position.as_secs_f64();
            let duration_f64 = seeked_duration.map(|d: Duration| d.as_secs_f64());
            let payload = json!({
                "position": position_f64,
                "duration": duration_f64,
                "state": format!("{:?}", playback_manager.player_state).to_lowercase(),
            });
            state.app_handle.emit("audio://position_update", payload).map_err(|e| e.to_string())?;

            playback_manager.is_seeking = false;
            Ok(())
        }
        Err(e) => {
            playback_manager.is_seeking = false;
            Err(e.to_string())
        }
    }
}

#[tauri::command]
pub fn get_playback_state(state: tauri::State<Arc<AppAudioState>>) -> Result<serde_json::Value, String> {
    let playback_manager = state.playback_state.lock().map_err(|e| e.to_string())?;

    let position = playback_manager.get_current_position().as_secs_f64();
    let duration = playback_manager.total_duration.map(|d| d.as_secs_f64());
    
    Ok(json!({
        "state": format!("{:?}", playback_manager.player_state).to_lowercase(),
        "position": position,
        "duration": duration,
        "filepath": playback_manager.filepath,
    }))
}