/**
 * Hauptskript für das Anime-Loads Dashboard
 */

// DOM-Elemente erst nach vollständigem Laden ansprechen
document.addEventListener('DOMContentLoaded', function() {
    
    // Tooltips initialisieren
    initTooltips();
    
    // Filter-Funktionalität (wenn auf Filter-Seite)
    if (document.getElementById('filterForm')) {
        initFilters();
    }
    
    // Suchfunktionalität (wenn auf der Suchseite)
    if (document.getElementById('searchForm')) {
        initSearchForm();
    }
    
    // Fortschrittsbalkenfunktionalität
    updateProgressBars();
    
    // Carousel-Intervall erhöhen
    adjustCarouselInterval();
});

/**
 * Initialisiert Bootstrap-Tooltips
 */
function initTooltips() {
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

/**
 * Initialisiert Filter-Funktionalität
 */
function initFilters() {
    const filterForm = document.getElementById('filterForm');
    const animeSelect = document.getElementById('animeSelect');
    const seasonSelect = document.getElementById('seasonSelect');
    
    // Bei Änderung des Anime-Select werden passende Staffeln nachgeladen
    if (animeSelect) {
        animeSelect.addEventListener('change', function() {
            const animeId = this.value;
            
            if (!animeId) {
                // Alle Optionen außer der ersten entfernen, wenn kein Anime ausgewählt ist
                while (seasonSelect.options.length > 1) {
                    seasonSelect.remove(1);
                }
                seasonSelect.disabled = true;
                return;
            }
            
            // Staffeln zum ausgewählten Anime laden
            fetchSeasons(animeId);
        });
    }
    
    // Filter-Reset-Button
    const resetButton = document.getElementById('resetFilters');
    if (resetButton) {
        resetButton.addEventListener('click', function(e) {
            e.preventDefault();
            filterForm.reset();
            
            // Select-Felder zurücksetzen
            if (seasonSelect) {
                while (seasonSelect.options.length > 1) {
                    seasonSelect.remove(1);
                }
                seasonSelect.disabled = true;
            }
        });
    }
}

/**
 * Lädt die Staffeln für einen bestimmten Anime
 * @param {number} animeId - ID des Animes
 */
function fetchSeasons(animeId) {
    const seasonSelect = document.getElementById('seasonSelect');
    
    // Zurücksetzen und Ladestatus anzeigen
    while (seasonSelect.options.length > 1) {
        seasonSelect.remove(1);
    }
    
    const loadingOption = document.createElement('option');
    loadingOption.text = 'Lädt...';
    loadingOption.disabled = true;
    seasonSelect.add(loadingOption);
    seasonSelect.disabled = true;
    
    // Staffeln via API laden
    fetch(`/api/anime/${animeId}`)
        .then(response => response.json())
        .then(data => {
            // Lade-Option entfernen
            seasonSelect.remove(1);
            
            if (data.seasons && data.seasons.length > 0) {
                // Staffeln hinzufügen
                data.seasons.forEach(season => {
                    const option = document.createElement('option');
                    option.value = season.id;
                    option.text = season.name;
                    seasonSelect.add(option);
                });
                
                seasonSelect.disabled = false;
            } else {
                const noSeasonsOption = document.createElement('option');
                noSeasonsOption.text = 'Keine Staffeln gefunden';
                noSeasonsOption.disabled = true;
                seasonSelect.add(noSeasonsOption);
            }
        })
        .catch(error => {
            console.error('Fehler beim Laden der Staffeln:', error);
            const errorOption = document.createElement('option');
            errorOption.text = 'Fehler beim Laden der Staffeln';
            errorOption.disabled = true;
            
            // Lade-Option entfernen
            seasonSelect.remove(1);
            seasonSelect.add(errorOption);
        });
}

/**
 * Initialisiert das Suchformular
 */
function initSearchForm() {
    const searchForm = document.getElementById('searchForm');
    const searchResults = document.getElementById('searchResults');
    const searchInput = document.getElementById('searchInput');
    const searchTypeSelect = document.getElementById('searchType');
    
    if (searchForm) {
        searchForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const query = searchInput.value.trim();
            if (query.length < 2) {
                showSearchError('Die Suchanfrage muss mindestens 2 Zeichen enthalten.');
                return;
            }
            
            const searchType = searchTypeSelect.value;
            
            // Anzeige des Ladezustands
            searchResults.innerHTML = `
                <div class="text-center py-4">
                    <div class="spinner-border text-primary" role="status">
                        <span class="visually-hidden">Suche läuft...</span>
                    </div>
                    <p class="mt-2">Suche läuft...</p>
                </div>
            `;
            
            // API-Anfrage für die Suche
            fetch(`/api/search?q=${encodeURIComponent(query)}&type=${searchType}`)
                .then(response => response.json())
                .then(data => {
                    displaySearchResults(data);
                })
                .catch(error => {
                    console.error('Fehler bei der Suche:', error);
                    showSearchError('Ein Fehler ist bei der Suche aufgetreten. Bitte versuche es später erneut.');
                });
        });
        
        // Automatische Suche, wenn der URL-Parameter 'q' vorhanden ist
        const urlParams = new URLSearchParams(window.location.search);
        const queryParam = urlParams.get('q');
        
        if (queryParam && queryParam.length >= 2) {
            searchInput.value = queryParam;
            searchForm.dispatchEvent(new Event('submit'));
        }
    }
}

/**
 * Zeigt einen Suchfehler an
 * @param {string} message - Fehlermeldung
 */
function showSearchError(message) {
    const searchResults = document.getElementById('searchResults');
    searchResults.innerHTML = `
        <div class="alert alert-danger" role="alert">
            <i class="fas fa-exclamation-circle me-2"></i>${message}
        </div>
    `;
}

/**
 * Zeigt Suchergebnisse an
 * @param {Object} data - Suchergebnisdaten
 */
function displaySearchResults(data) {
    const searchResults = document.getElementById('searchResults');
    let resultsHtml = '';
    
    const animeCount = data.animes ? data.animes.length : 0;
    const seasonCount = data.seasons ? data.seasons.length : 0;
    const episodeCount = data.episodes ? data.episodes.length : 0;
    const totalCount = animeCount + seasonCount + episodeCount;
    
    if (totalCount === 0) {
        resultsHtml = `
            <div class="alert alert-info" role="alert">
                <i class="fas fa-info-circle me-2"></i>Keine Ergebnisse gefunden.
            </div>
        `;
    } else {
        resultsHtml = `
            <div class="mb-4">
                <h4>Suchergebnisse (${totalCount})</h4>
                <div class="text-muted mb-3">Gefunden: ${animeCount} Animes, ${seasonCount} Staffeln, ${episodeCount} Episoden</div>
                
                <ul class="nav nav-tabs" id="resultTabs" role="tablist">
                    <li class="nav-item" role="presentation">
                        <button class="nav-link active" id="anime-tab" data-bs-toggle="tab" data-bs-target="#anime-results" 
                                type="button" role="tab" aria-controls="anime-results" aria-selected="true">
                            Animes (${animeCount})
                        </button>
                    </li>
                    <li class="nav-item" role="presentation">
                        <button class="nav-link" id="season-tab" data-bs-toggle="tab" data-bs-target="#season-results" 
                                type="button" role="tab" aria-controls="season-results" aria-selected="false">
                            Staffeln (${seasonCount})
                        </button>
                    </li>
                    <li class="nav-item" role="presentation">
                        <button class="nav-link" id="episode-tab" data-bs-toggle="tab" data-bs-target="#episode-results" 
                                type="button" role="tab" aria-controls="episode-results" aria-selected="false">
                            Episoden (${episodeCount})
                        </button>
                    </li>
                </ul>
                
                <div class="tab-content border border-top-0 p-3 rounded-bottom" id="resultTabsContent">
                    <div class="tab-pane fade show active" id="anime-results" role="tabpanel" aria-labelledby="anime-tab">
                        ${renderAnimeResults(data.animes)}
                    </div>
                    <div class="tab-pane fade" id="season-results" role="tabpanel" aria-labelledby="season-tab">
                        ${renderSeasonResults(data.seasons)}
                    </div>
                    <div class="tab-pane fade" id="episode-results" role="tabpanel" aria-labelledby="episode-tab">
                        ${renderEpisodeResults(data.episodes)}
                    </div>
                </div>
            </div>
        `;
    }
    
    searchResults.innerHTML = resultsHtml;
}

/**
 * Rendert Anime-Suchergebnisse
 * @param {Array} animes - Array von Anime-Objekten
 * @returns {string} HTML-Markup für die Ergebnisliste
 */
function renderAnimeResults(animes) {
    if (!animes || animes.length === 0) {
        return '<div class="text-center py-3">Keine Anime-Ergebnisse gefunden.</div>';
    }
    
    let html = '<div class="list-group">';
    
    animes.forEach(anime => {
        html += `
            <a href="/anime/${anime.id}" class="list-group-item list-group-item-action">
                <div class="d-flex w-100 justify-content-between">
                    <h5 class="mb-1">${anime.name}</h5>
                </div>
                <p class="mb-1 text-muted">
                    <i class="fas fa-folder me-2"></i>${anime.directory_path}
                </p>
            </a>
        `;
    });
    
    html += '</div>';
    return html;
}

/**
 * Rendert Staffel-Suchergebnisse
 * @param {Array} seasons - Array von Staffel-Objekten
 * @returns {string} HTML-Markup für die Ergebnisliste
 */
function renderSeasonResults(seasons) {
    if (!seasons || seasons.length === 0) {
        return '<div class="text-center py-3">Keine Staffel-Ergebnisse gefunden.</div>';
    }
    
    let html = '<div class="list-group">';
    
    seasons.forEach(season => {
        html += `
            <a href="/season/${season.id}" class="list-group-item list-group-item-action">
                <div class="d-flex w-100 justify-content-between">
                    <h5 class="mb-1">${season.name}</h5>
                </div>
                <p class="mb-1 text-muted">
                    <i class="fas fa-folder me-2"></i>${season.directory_path}
                </p>
            </a>
        `;
    });
    
    html += '</div>';
    return html;
}

/**
 * Rendert Episoden-Suchergebnisse
 * @param {Array} episodes - Array von Episoden-Objekten
 * @returns {string} HTML-Markup für die Ergebnisliste
 */
function renderEpisodeResults(episodes) {
    if (!episodes || episodes.length === 0) {
        return '<div class="text-center py-3">Keine Episoden-Ergebnisse gefunden.</div>';
    }
    
    let html = '<div class="list-group">';
    
    episodes.forEach(episode => {
        const resolutionText = episode.resolution_width && episode.resolution_height ? 
            `${episode.resolution_width}x${episode.resolution_height}` : 'Unbekannt';
        
        html += `
            <a href="/episode/${episode.id}" class="list-group-item list-group-item-action">
                <div class="d-flex w-100 justify-content-between">
                    <h5 class="mb-1">${episode.name}</h5>
                    <span class="badge bg-info">${resolutionText}</span>
                </div>
                <p class="mb-1">
                    <span class="badge bg-secondary me-2">${episode.video_codec || 'Unbekannter Codec'}</span>
                    <span class="badge bg-secondary me-2">${episode.file_extension}</span>
                    ${episode.hdr_format ? `<span class="badge bg-warning text-dark me-2">${episode.hdr_format}</span>` : ''}
                </p>
                <p class="mb-1 text-muted small">
                    <i class="fas fa-file-video me-2"></i>${episode.file_path}
                </p>
            </a>
        `;
    });
    
    html += '</div>';
    return html;
}

/**
 * Aktualisiert alle Fortschrittsbalken auf der Seite
 */
function updateProgressBars() {
    const progressBars = document.querySelectorAll('.progress-bar[data-percentage]');
    
    progressBars.forEach(bar => {
        const percentage = bar.getAttribute('data-percentage');
        
        // Animation für den Fortschrittsbalken
        setTimeout(() => {
            bar.style.width = percentage + '%';
        }, 100);
    });
}

/**
 * Passt das Intervall für Karusselle an
 */
function adjustCarouselInterval() {
    const carousels = document.querySelectorAll('.carousel');
    
    carousels.forEach(carousel => {
        // Zeit auf 8 Sekunden erhöhen
        const carouselInstance = new bootstrap.Carousel(carousel, {
            interval: 8000
        });
    });
}

/**
 * Formatiert Bytes zu einem lesbaren String (KB, MB, GB, TB)
 * @param {number} bytes - Byte-Anzahl
 * @param {number} decimals - Anzahl der Dezimalstellen
 * @returns {string} Formatierte Größe
 */
function formatBytes(bytes, decimals = 2) {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const dm = decimals < 0 ? 0 : decimals;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB'];
    
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
}

/**
 * Formatiert Millisekunden in ein lesbares Zeitformat
 * @param {number} ms - Millisekunden
 * @returns {string} Formatierte Zeit
 */
function formatDuration(ms) {
    const seconds = Math.floor(ms / 1000);
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const remainingSeconds = seconds % 60;
    
    let result = '';
    
    if (hours > 0) {
        result += hours + ' Std. ';
    }
    
    if (minutes > 0 || hours > 0) {
        result += minutes + ' Min. ';
    }
    
    result += remainingSeconds + ' Sek.';
    
    return result;
}
