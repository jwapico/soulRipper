// all numbers seconds
export interface PlaybackState {
  state: 'playing' | 'paused' | 'stopped';
  position: number;
  duration: number | null;
  filepath: string | null;
}
