import librosa
import numpy as np
import crepe


class MelodicContourGenerator:
    def __init__(self,
                 sr=16000,
                 chunk_duration_seconds=15.0,
                 hop_duration_seconds=5.0,
                 crepe_step_size=50,
                 crepe_confidence_threshold=0.3):
        self.sr = sr
        self.__chunk_len = int(chunk_duration_seconds * sr)
        self.__hop_len = int(hop_duration_seconds * sr)
        self.__crepe_step_size = crepe_step_size
        self.__crepe_confidence_threshold = crepe_confidence_threshold

    def extract_features(self, wav_io):
        y, sr = librosa.load(wav_io, sr=self.sr)

        chunk_id = 0
        all_features = []

        for start in range(0, max(len(y), 240000) - self.__chunk_len + 1, self.__hop_len):
            end = start + self.__chunk_len
            y_chunk = y[start:end]

            pitch = self.__extract_pitch_crepe(y_chunk, self.sr)
            pitch = self.__clean_pitch(pitch)
            pitch = np.nan_to_num(12 * np.log2(pitch / 440.0))
            delta_pitches = np.diff(pitch)
            dp_mean = np.mean(delta_pitches)
            dp_std = np.std(delta_pitches)
            delta_pitches = (delta_pitches - dp_mean) / (dp_std + 1e-6)

            all_features.append({'delta_pitches': delta_pitches.tolist(),
                                 'dp_mean': dp_mean,
                                 'dp_std': dp_std,
                                 'chunk_index': chunk_id})

            chunk_id += 1

        return all_features

    def compare(self, song_features, user_features):
        D, wp = librosa.sequence.dtw(X=song_features, Y=user_features, metric='euclidean', subseq=True)

        dtw_distance = D[-1].min()
        final_score = np.abs(dtw_distance - 1.5 * self.__correlation_score(song_features, user_features))

        return final_score

    @staticmethod
    def __correlation_score(a, b):
        corr = np.correlate(a, b, mode='valid')
        return corr.max()

    def __extract_pitch_crepe(self, y, sr):
        _, frequency, confidence, _ = crepe.predict(y, sr,
                                                    viterbi=True,
                                                    step_size=self.__crepe_step_size,
                                                    model_capacity='small')
        frequency = np.squeeze(frequency)
        confidence = np.squeeze(confidence)

        frequency[confidence < self.__crepe_confidence_threshold] = 0

        return frequency

    @staticmethod
    def __clean_pitch(pitch_array):
        pitch_array = np.array(pitch_array)
        pitch_array[pitch_array == 0] = np.nan

        if np.all(np.isnan(pitch_array)):
            return np.zeros_like(pitch_array)

        not_nan = np.flatnonzero(~np.isnan(pitch_array))
        if len(not_nan) < 2:
            return np.zeros_like(pitch_array)

        interpolated = np.interp(
            np.arange(len(pitch_array)),
            not_nan,
            pitch_array[not_nan]
        )

        return interpolated
