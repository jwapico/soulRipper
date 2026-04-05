fn main() {
    // Set rustflags for Android to link C++ stdlib
    if std::env::var("TARGET").map_or(false, |t| t.contains("aarch64-linux-android")) {
        println!("cargo:rustc-link-arg=-lc++_shared");
    }
    tauri_build::build()
}
