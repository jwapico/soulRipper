export interface AudiofileMetadata {
    filepath: string;
    file_size: number;
    created: number;
    modified: number;
    duration_secs: number;
    bit_rate: number | null;
    sample_rate: number | null;
    bit_depth: number | null;
    channels: number | null;
    tags: Record<string, string>;
}