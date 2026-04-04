use std::time::{Duration, Instant};

const BUFFER_OFFSET_MS: u64 = 64;

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum PlaybackState {
    Stopped,
    Playing,
    Paused,
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

    pub fn start_playback(&mut self, filepath: String, duration: Option<Duration>) {
        self.state = PlaybackState::Playing;
        self.track_start_instant = Some(Instant::now());
        self.track_position_at_start = Duration::ZERO;
        self.track_duration = duration;
        self.current_filepath = Some(filepath);
    }

    pub fn pause(&mut self) {
        if self.state == PlaybackState::Playing {
            let raw_position = self.current_position();
            let adjusted = raw_position.saturating_sub(Duration::from_millis(BUFFER_OFFSET_MS));
            self.state = PlaybackState::Paused;
            self.track_position_at_start = adjusted;
            self.track_start_instant = None;
        }
    }

    pub fn resume(&mut self) {
        if self.state == PlaybackState::Paused {
            self.state = PlaybackState::Playing;
            self.track_start_instant = Some(Instant::now());
        }
    }

    pub fn seek(&mut self, position: Duration) {
        self.track_position_at_start = position;
        if self.state == PlaybackState::Playing {
            self.track_start_instant = Some(Instant::now());
        }
    }

    pub fn stop(&mut self) {
        self.state = PlaybackState::Stopped;
        self.track_start_instant = None;
        self.track_position_at_start = Duration::ZERO;
    }
}