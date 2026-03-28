export async function load() {
    // TODO: some way to cache tracks to not perform large query every time switch
    //  - maybe can have each table keep a hash on the backend that frontend can query
    //      - probably sophisticated ways of doing this to localize/speed up changes/queries
    const response = await fetch("http://127.0.0.1:8000/tracks")
    const tracks = await response.json()
    return { tracks }
}