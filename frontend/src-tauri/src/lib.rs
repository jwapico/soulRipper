use std::time::{Duration};
use tauri::{Emitter, Manager};
use serde_json::json;
use std::thread;
use std::sync::{Arc, Mutex};

mod audio;
use audio::{
    PlaybackManager, 
    AppAudioState, 
    PlayerState, 
    play_audio, 
    pause_audio,
    resume_audio,
    seek_audio,
    get_playback_state,
};

const FRONTEND_POLLING_INTERVAL_MS: u64 = 100;

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .setup(|app| {
            // create handle to the default OS output device
            let sink_handle = rodio::DeviceSinkBuilder::open_default_sink()
                .map_err(|e: rodio::DeviceSinkError| e.to_string())?;

            // create a player for the sink and a handle to the tauri app (so we can emit ui updates)
            let player = rodio::Player::connect_new(sink_handle.mixer());
            let app_handle = app.handle().clone();
            let audio_state = Arc::new(AppAudioState {
                sink_handle,
                rodio_player: player,
                app_handle,
                playback_state: Mutex::new(PlaybackManager::new()),
            });
            
            // spawn a new thread to watch the PlayerState and emit upates to the ui
            let thread_audio_state = Arc::clone(&audio_state);
            thread::spawn(move || {
                loop {
                    thread::sleep(Duration::from_millis(FRONTEND_POLLING_INTERVAL_MS));
                    
                    // grab the PlayerState rq and extract current state
                    let (position, duration, current_state, is_seeking) = {
                        let mut ps = thread_audio_state.playback_state.lock().unwrap();
                        let position = ps.get_current_position();
                        let duration = ps.total_duration;
                        let current_state = ps.player_state;
                        let is_seeking = ps.is_seeking;

                        // cleanup if audio is done
                        let track_ended = ps.player_state == PlayerState::Playing && thread_audio_state.rodio_player.empty();
                        if track_ended {
                            thread_audio_state.rodio_player.stop();
                            ps.stop();

                            // send update to ui
                            let end_payload = json!({ "filepath": ps.filepath.clone() });
                            let _ = thread_audio_state.app_handle.emit("audio://track_ended", end_payload);

                            drop(ps);
                        } (position, duration, current_state, is_seeking)
                    };
                    
                    let position_f64 = position.as_secs_f64();
                    let duration_f64 = duration.map(|d| d.as_secs_f64());
                    
                    // send state to UI for update if user not interacting 
                    if !is_seeking {
                        let payload = json!({
                            "position": position_f64,
                            "duration": duration_f64,
                            "state": format!("{:?}", current_state).to_lowercase(),
                        });
                        let _ = thread_audio_state.app_handle.emit("audio://position_update", payload);
                    }
                }
            });

            // store our AudioState in tauri's state so we can accept it in functions called by tauri when invoked by ts
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
