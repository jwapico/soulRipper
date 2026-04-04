use std::time::{Duration};
use tauri::{Emitter, Manager};
use rodio::{DeviceSinkBuilder, DeviceSinkError, Player};
use serde_json::json;
use std::thread;
use std::sync::{Arc, Mutex};

mod audio_player;
use audio_player::{
    PlayerState, 
    AudioState, 
    PlaybackState, 
    play_audio, 
    pause_audio,
    resume_audio,
    seek_audio,
    get_playback_state,
};

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
