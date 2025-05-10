-- Optimierungsskript für die Anime-Loads Dashboard Datenbank
-- Erstellt am 09.05.2025 von Cascade AI

-- Indizes für häufig abgefragte Spalten in der animes-Tabelle
ALTER TABLE animes ADD INDEX idx_anime_name (name);
ALTER TABLE animes ADD INDEX idx_anime_directory (directory_path);

-- Indizes für die seasons-Tabelle
ALTER TABLE seasons ADD INDEX idx_season_name (name);
ALTER TABLE seasons ADD INDEX idx_season_directory (directory_path);
ALTER TABLE seasons ADD INDEX idx_season_number (season_number);

-- Indizes für die episodes-Tabelle
ALTER TABLE episodes ADD INDEX idx_episode_name (name);
ALTER TABLE episodes ADD INDEX idx_episode_file_path (file_path);
ALTER TABLE episodes ADD INDEX idx_episode_video_codec (video_codec);
ALTER TABLE episodes ADD INDEX idx_episode_resolution (resolution_width, resolution_height);
ALTER TABLE episodes ADD INDEX idx_episode_hdr (hdr_format);
ALTER TABLE episodes ADD INDEX idx_episode_audio_lang (audio_language);

-- Optimieren von Tabellen nach der Indexerstellung
OPTIMIZE TABLE animes;
OPTIMIZE TABLE seasons;
OPTIMIZE TABLE episodes;
