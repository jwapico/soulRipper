import type { TrackResponse } from "./TrackResponse"

export interface PlaylistTracksResponse {
    playlist_id: number
    spotift_id?: number
    name: string
    description?: string
    tracks: TrackResponse[]
}