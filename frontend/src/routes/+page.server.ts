export async function load() {
    const response = await fetch("http://127.0.0.1:8000/tracks/10")
    const track = await response.json()
    return { track }
}