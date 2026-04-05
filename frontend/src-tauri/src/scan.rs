use std::collections::HashMap;
use std::{os::unix::fs::MetadataExt};
use lofty::file::{AudioFile, TaggedFileExt};
use serde_json::json;
use walkdir::WalkDir;
use tauri::Emitter;
use log::error;

const AUDIO_EXTENSIONS: [&str; 8] = [
    "mp3", 
    "flac", 
    "wav", 
    "ogg", 
    "m4a", 
    "aac", 
    "wma", 
    "opus"
];

#[derive(serde::Serialize)]
pub struct AudioFileMetadata {
    pub path: String,
    pub file_size: u64,
    pub created: f64,
    pub modified: f64,
    pub duration_secs: u64,
    pub bit_rate: Option<u32>,
    pub sample_rate: Option<u32>,
    pub bit_depth: Option<u8>,
    pub channels: Option<u8>,
    pub tags: HashMap<String, String>,
}

#[tauri::command]
pub fn scan_dir(root: String, app_handle: tauri::AppHandle) {
    // scan every file in the directory and emit an event with all it's metadata 
    for entry in WalkDir::new(root)
        .follow_links(true)
        .into_iter()
        .filter_map(|e| e.ok()) {
            if entry.file_type().is_file() {
                // get general os file metadata
                let os_metadata = entry.metadata().unwrap();
                let file_size = os_metadata.size();
                let created = os_metadata.created().unwrap().duration_since(std::time::UNIX_EPOCH).map(|d| d.as_secs_f64()).unwrap_or(0.0);
                let modified = os_metadata.modified().unwrap().duration_since(std::time::UNIX_EPOCH).map(|d| d.as_secs_f64()).unwrap_or(0.0);

                // check if file is audio file
                let path = entry.path();
                if let Some(ext) = path.extension() {
                    if let Some(ext_str) = ext.to_str() {
                        if AUDIO_EXTENSIONS.contains(&ext_str) {
                            // extract audio file metadata with lofty
                            let tagged_file = lofty::read_from_path(path).unwrap();
                            let file_props = tagged_file.properties();

                            // intrinsic properties
                            let duration_secs = file_props.duration().as_secs();
                            let bit_rate = file_props.audio_bitrate();
                            let sample_rate = file_props.sample_rate();
                            let bit_depth = file_props.bit_depth();
                            let channels = file_props.channels();

                            // these are optional and arbitrary tags attached to the file by users
                            let mut tags = HashMap::new();
                            if let Some(tag) = tagged_file.primary_tag() {
                                let _ = tag.items().map(|item| {
                                    let key = format!("{:?}", item.key());
                                    let value = item.value().text().map(|s| s.to_string()).unwrap_or_default();
                                    tags.insert(key, value);
                                });
                            }

                            // emit scan event with the metadata and log error if error
                            if let Err(e) = app_handle.emit("scan://file", json!(AudioFileMetadata {
                                path: String::from(path.to_str().unwrap()),
                                file_size,
                                created,
                                modified,
                                duration_secs,
                                channels,
                                sample_rate,
                                bit_rate,
                                bit_depth,
                                tags
                            })) {
                                error!("Failed to emit scan event: {}", e);
                            }
                        }
                    }
                }
            }
    }
}