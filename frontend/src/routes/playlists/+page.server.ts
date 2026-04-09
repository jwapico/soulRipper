export async function load() {
    const response = await fetch("http://127.0.0.1:8000/playlists")
    const playlist_tracks = await response.json()
    return { playlist_tracks }
}