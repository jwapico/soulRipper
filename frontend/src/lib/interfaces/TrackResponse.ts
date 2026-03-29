export interface TrackResponse {
    id: number;
    title?: string;
    artists?: string[];
    filepath?: string;
    album?: string;
    release_date?: string;
    date_added?: string;
    comments?: string;
    explicit?: boolean;
    spotify_id?: string;
}