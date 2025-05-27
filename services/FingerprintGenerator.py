import hashlib
import librosa
import numpy as np
import scipy


class FingerprintGenerator:
    def __init__(self,
                 fan_value = 10,
                 max_time_delta = 200,
                 neighborhood_size = (20, 5),
                 threshold_rel_db = 10,
                 sr = 5512,
                 n_fft = 256,
                 hop_length = 64,
                 frames_per_fingerprint = 128):
        self.fan_value = fan_value
        self.max_time_delta = max_time_delta
        self.neighborhood_size = neighborhood_size
        self.threshold_rel_db = threshold_rel_db

        self.sr = sr
        self.n_fft = n_fft
        self.hop_length = hop_length

        self.samples_per_fingerprint = frames_per_fingerprint * self.hop_length

    def extract_hashes_from_audio(self, wav_io):
        y, sr = librosa.load(wav_io, sr=self.sr)

        all_hashes = []
        num_chunks = len(y) // self.samples_per_fingerprint

        for i in range(num_chunks):
            y_chunk = y[i * self.samples_per_fingerprint: (i + 1) * self.samples_per_fingerprint]
            hashes = self.__process_chunk(y_chunk, chunk_index=i)
            all_hashes.extend(hashes)

        return all_hashes

    def __process_chunk(self, y_chunk, chunk_index):
        D = librosa.stft(y_chunk, n_fft=self.n_fft, hop_length=self.hop_length)
        s_db = librosa.amplitude_to_db(np.abs(D), ref=np.max(y_chunk))

        frequencies = librosa.fft_frequencies(sr=self.sr, n_fft=self.n_fft)
        freq_mask = (frequencies >= 300) & (frequencies <= 2000)
        s_db_filtered = s_db[freq_mask, :]
        filtered_frequencies = frequencies[freq_mask]

        s_db_log = self.__compress_to_log_bins(s_db_filtered, filtered_frequencies)
        peaks = self.__find_peaks(s_db_log)
        chunk_hashes = self.__generate_hashes(peaks)

        offset = chunk_index * (self.samples_per_fingerprint // self.hop_length)
        return [(h, t + offset) for h, t in chunk_hashes]

    @staticmethod
    def __compress_to_log_bins(s_db_filtered, filtered_frequencies):
        log_bins = np.geomspace(300, 2000, num=33)
        bin_masks = np.array([
            (filtered_frequencies >= f_low) & (filtered_frequencies < f_high)
            for f_low, f_high in zip(log_bins[:-1], log_bins[1:])
        ])
        s_db_log = np.max(
            np.where(bin_masks[:, :, np.newaxis], s_db_filtered[np.newaxis, :, :], -80),
            axis=1
        )
        return s_db_log

    def __find_peaks(self, s_db_log):
        local_max = scipy.ndimage.maximum_filter(s_db_log, size=self.neighborhood_size) == s_db_log

        adaptive_thresholds = np.median(s_db_log, axis=0) + self.threshold_rel_db
        threshold_mask = s_db_log > adaptive_thresholds[np.newaxis, :]

        detected_peaks = local_max & threshold_mask
        peak_coords = np.argwhere(detected_peaks)
        return peak_coords

    def __generate_hashes(self, peaks):
        hashes = []
        peaks = sorted(peaks, key=lambda x: x[1])
        for i in range(len(peaks)):
            freq1, t1 = peaks[i]
            for j in range(1, self.fan_value + 1):
                if i + j < len(peaks):
                    freq2, t2 = peaks[i + j]
                    delta_t = t2 - t1
                    if 0 < delta_t <= self.max_time_delta:
                        hash_input = f"{freq1}|{freq2}|{delta_t}"
                        h = hashlib.sha1(hash_input.encode('utf-8')).hexdigest()[:20]
                        hashes.append((h, t1))
        return hashes
