/**
 * Enhanced Statistics Module für das Anime-Loads Dashboard
 * Erstellt verbesserte Datenvisualisierungen und Statistikauswertungen
 */

// Chart.js Konfigurationen
const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
        legend: {
            position: 'right',
            labels: {
                padding: 20,
                boxWidth: 15,
                font: {
                    size: 12
                }
            }
        },
        tooltip: {
            padding: 12,
            boxPadding: 6
        }
    }
};

// Farbpaletten für Diagramme
const colorPalette = [
    '#4e73df', '#1cc88a', '#36b9cc', '#f6c23e', '#e74a3b', 
    '#5a5c69', '#6f42c1', '#20c9a6', '#fd7e14', '#6610f2'
];

// Farbpalette für spezifische Kategorien
const categoryColors = {
    resolutions: {
        '4K': '#6a0dad',
        'Full HD': '#2e5cb8',
        'HD': '#17a2b8',
        'SD': '#6c757d'
    },
    codecs: {
        'HEVC': '#5cb85c',
        'AV1': '#d9534f',
        'AVC': '#5bc0de',
        'VP9': '#f0ad4e',
        'MPEG': '#777777'
    },
    hdr: {
        'HDR10': '#e6a919',
        'HDR10+': '#ff9500',
        'Dolby Vision': '#a50034',
        'HLG': '#bf5700',
        'Kein HDR': '#aaaaaa'
    }
};

/**
 * Initialisiert alle erweiterten Statistik-Diagramme
 */
function initEnhancedStats() {
    // API-Endpunkt für die Statistikdaten
    fetch('/api/stats')
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            // Diagramme erstellen, wenn Daten verfügbar sind
            if (data) {
                // Separate API-Aufrufe für spezifische Diagramme, um Fehler zu vermeiden
                // und Belastung zu verteilen
                loadResolutionCharts();
                loadCodecCharts();
                loadHDRChart();
                loadStorageChart();
                updateGeneralStats(data);
                
                // Top-Animes laden
                loadTopAnimes('episodes');
                loadTopAnimes('size');
            }
        })
        .catch(error => {
            console.error('Fehler beim Laden der Statistikdaten:', error);
            document.querySelectorAll('.loading-container').forEach(container => {
                container.innerHTML = '<div class="alert alert-danger">Fehler beim Laden der Daten</div>';
            });
        });
}

/**
 * Erstellt Auflösungs-Diagramme
 */
function createResolutionCharts(data) {
    console.log('Resolution data received:', data);
    
    // Prüfen auf die erwartete Datenstruktur
    if (!data.distribution || !data.distribution.length) {
        console.error('Keine Auflösungsverteilung gefunden:', data);
        return;
    }

    // Vorbereiten der Daten für Tortendiagramm
    const labels = [];
    const values = [];
    const colors = [];

    // Array-Format verarbeiten
    data.distribution
        .sort((a, b) => b.count - a.count)
        .forEach(item => {
            labels.push(item.resolution || 'Unbekannt');
            values.push(item.count);
            colors.push(categoryColors.resolutions[item.resolution] || getRandomColor());
        });

    // Auflösungsverteilung als Tortendiagramm
    const resolutionPieCtx = document.getElementById('resolutionPieChart');
    if (resolutionPieCtx) {
        new Chart(resolutionPieCtx, {
            type: 'pie',
            data: {
                labels: labels,
                datasets: [{
                    data: values,
                    backgroundColor: colors,
                    borderWidth: 1
                }]
            },
            options: {
                ...chartOptions,
                plugins: {
                    ...chartOptions.plugins,
                    title: {
                        display: true,
                        text: 'Auflösungsverteilung'
                    }
                }
            }
        });
    }

    // Verteilung nach Auflösung als Balkendiagramm mit Prozentangaben
    const resolutionBarCtx = document.getElementById('resolutionBarChart');
    if (resolutionBarCtx) {
        // Gesamtzahl berechnen
        const total = values.reduce((sum, value) => sum + value, 0);
        
        // Prozentsätze berechnen
        const percentages = values.map(value => ((value / total) * 100).toFixed(1));
        
        // Labels mit Prozentangaben
        const labelsWithPercentage = labels.map((label, index) => 
            `${label} (${percentages[index]}%)`);

        new Chart(resolutionBarCtx, {
            type: 'bar',
            data: {
                labels: labelsWithPercentage,
                datasets: [{
                    label: 'Anzahl Episoden',
                    data: values,
                    backgroundColor: colors,
                    borderWidth: 1
                }]
            },
            options: {
                ...chartOptions,
                indexAxis: 'y',
                scales: {
                    x: {
                        beginAtZero: true
                    }
                },
                plugins: {
                    ...chartOptions.plugins,
                    title: {
                        display: true,
                        text: 'Anzahl Episoden pro Auflösung'
                    }
                }
            }
        });
    }

    // Lade-Anzeige entfernen
    document.getElementById('resolutionStats').innerHTML = '';
}
    
/**
 * Erstellt Codec-Diagramme
 */
function createCodecCharts(data) {
    console.log('Codec data received:', data);
    
    if (!data.distribution || !data.distribution.length) {
        console.error('Keine Codec-Verteilung gefunden:', data);
        return;
    }
    
    // Vorbereiten der Daten für Tortendiagramm
    const labels = [];
    const values = [];
    const colors = [];
    
    // Array-Format verarbeiten
    data.distribution
        .sort((a, b) => b.count - a.count)
        .slice(0, 5) // Nur die Top 5 anzeigen
        .forEach(item => {
            // Codec-Namen für bessere Lesbarkeit kürzen
            let codec = item.codec || 'Unbekannt';
            if (codec.includes('HEVC') || codec.includes('x265')) {
                codec = 'HEVC';
            } else if (codec.includes('AVC') || codec.includes('x264')) {
                codec = 'AVC';
            } else if (codec.length > 15) {
                codec = codec.substring(0, 15) + '...';
            }
            
            labels.push(codec);
            values.push(item.count);
            colors.push(categoryColors.codecs[codec] || getRandomColor());
        });
        }
        colors.push(color);
    });

    // Codec-Verteilung als Tortendiagramm
    const codecPieCtx = document.getElementById('codecPieChart');
    if (codecPieCtx) {
        new Chart(codecPieCtx, {
            type: 'doughnut',
            data: {
                labels: labels,
                datasets: [{
                    data: values,
                    backgroundColor: colors,
                    borderWidth: 1
                }]
            },
            options: {
                ...chartOptions,
                plugins: {
                    ...chartOptions.plugins,
                    title: {
                        display: true,
                        text: 'Codec-Verteilung'
                    }
                }
            }
        });
    }

    // Lade-Anzeige entfernen
    document.getElementById('codecStats').innerHTML = '';
}

/**
                    backgroundColor: [
                        categoryColors.hdr['HDR10'],
                        categoryColors.hdr['Kein HDR']
                    ],
                    borderWidth: 1
                }]
            },
            options: {
                ...chartOptions,
                cutout: '70%',
                plugins: {
                    ...chartOptions.plugins,
                    title: {
                        display: true,
                        text: 'HDR-Verteilung'
                    }
                }
            }
        });
    }

    // Lade-Anzeige entfernen
    document.getElementById('hdrStats').innerHTML = '';
}

/**
 * Erstellt HDR-Diagramm
 */
function createHDRChart(data) {
    if (!data.hdr_distribution) return;

    const hdrChartCtx = document.getElementById('hdrChart');
    if (hdrChartCtx) {
        // HDR vs. Nicht-HDR Verteilung
        const labels = ['HDR', 'Kein HDR'];
        const values = [data.hdr_distribution.hdr || 0, data.hdr_distribution.non_hdr || 0];
        const colors = [categoryColors.hdr['HDR10'], categoryColors.hdr['Kein HDR']];

        new Chart(hdrChartCtx, {
            type: 'doughnut',
            data: {
                labels: labels,
                datasets: [{
                    data: values,
                    backgroundColor: colors,
                    borderWidth: 1
                }]
            },
            options: {
                ...chartOptions,
                plugins: {
                    ...chartOptions.plugins,
                    title: {
                        display: true,
                        text: 'HDR-Unterstützung'
                    }
                }
            }
        });

        // Detaillierte HDR-Informationen anzeigen, wenn verfügbar
        if (data.hdr_types && Object.keys(data.hdr_types).length > 0) {
            let hdrTypesHtml = '<div class="mt-3"><h6>HDR-Formate:</h6><ul class="list-group">';
            Object.entries(data.hdr_types).forEach(([type, count]) => {
                hdrTypesHtml += `<li class="list-group-item d-flex justify-content-between align-items-center">
                    ${type}
                    <span class="badge bg-primary rounded-pill">${count}</span>
                </li>`;
            });
            hdrTypesHtml += '</ul></div>';
            document.getElementById('hdrStats').innerHTML = hdrTypesHtml;
        } else {
            document.getElementById('hdrStats').innerHTML = '';
        }
    }
}

/**
 * Erstellt Speicherverbrauchsdiagramm
 */
function createStorageDistributionChart(data) {
    if (!data.storage_by_resolution) return;

    // Vorbereiten der Daten für Speichernutzungsdiagramm
    const labels = [];
    const values = [];
    const colors = [];

    // Sortieren nach Speicherverbrauch (absteigend)
    const sortedStorage = Object.entries(data.storage_by_resolution)
        .sort((a, b) => b[1] - a[1]);
    
    // Daten für Chart sammeln
    sortedStorage.forEach(([resolution, size]) => {
        // Größe in GB umrechnen
        const sizeGB = (size / (1024 * 1024 * 1024)).toFixed(1);
        
        labels.push(resolution);
        values.push(sizeGB);
        
        // Farbe aus vordefinierter Palette auswählen
        let color;
        if (resolution.includes('4K')) {
            color = categoryColors.resolutions['4K'];
        } else if (resolution.includes('Full HD') || resolution.includes('1080p')) {
            color = categoryColors.resolutions['Full HD'];
        } else if (resolution.includes('HD') || resolution.includes('720p')) {
            color = categoryColors.resolutions['HD'];
        } else {
            color = categoryColors.resolutions['SD'];
        }
        colors.push(color);
    });

    // Speicherverteilung als Balkendiagramm
    const storageChartCtx = document.getElementById('storageDistributionChart');
    if (storageChartCtx) {
        new Chart(storageChartCtx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Speicherplatz (GB)',
                    data: values,
                    backgroundColor: colors,
                    borderWidth: 1
                }]
            },
            options: {
                ...chartOptions,
                plugins: {
                    ...chartOptions.plugins,
                    title: {
                        display: true,
                        text: 'Speicherverbrauch nach Auflösung (GB)'
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });
    }

    // Lade-Anzeige entfernen
    document.getElementById('storageDistribution').innerHTML = '';
    
    // Gesamtspeicherplatz aktualisieren
    if (data.total_size_formatted) {
        document.getElementById('totalStorageSize').textContent = data.total_size_formatted;
    }
}

/**
 * Aktualisiert die allgemeinen Statistiken
 */
function updateGeneralStats(data) {
    // Lade-Anzeige entfernen
    const generalStatsElement = document.getElementById('generalStats');
    const storageStatsElement = document.getElementById('storageStats');
    
    if (generalStatsElement) {
        generalStatsElement.innerHTML = `
            <div class="d-flex flex-column">
                <div class="stat-item mb-2">
                    <span class="stat-label">Animes:</span>
                    <span class="stat-value">${data.animes_count || 0}</span>
                </div>
                <div class="stat-item mb-2">
                    <span class="stat-label">Staffeln:</span>
                    <span class="stat-value">${data.seasons_count || 0}</span>
                </div>
                <div class="stat-item">
                    <span class="stat-label">Episoden:</span>
                    <span class="stat-value">${data.episodes_count || 0}</span>
                </div>
            </div>
        `;
    }
    
    if (storageStatsElement) {
        storageStatsElement.innerHTML = `
            <div class="d-flex flex-column">
                <div class="stat-item mb-2">
                    <span class="stat-label">Gesamtgröße:</span>
                    <span class="stat-value" id="totalStorageSize">
                        ${data.total_size_formatted || 'Unbekannt'}
                    </span>
                </div>
                <div class="stat-item mb-2">
                    <span class="stat-label">Gesamtdauer:</span>
                    <span class="stat-value">
                        ${data.total_duration_formatted || 'Unbekannt'}
                    </span>
                </div>
            </div>
        `;
    }
}

/**
 * Erzeugt eine zufällige Farbe im Hex-Format
 */
function getRandomColor() {
    const letters = '0123456789ABCDEF';
    let color = '#';
    for (let i = 0; i < 6; i++) {
        color += letters[Math.floor(Math.random() * 16)];
    }
    return color;
}

/**
 * Lädt Daten für Auflösungsdiagramme
 */
function loadResolutionCharts() {
    fetch('/api/stats/resolution')
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            // Prüfen auf verschiedene Datenstrukturen
            if (data) {
                // Element für Fehleranzeige
                const resolutionContainer = document.getElementById('resolutionPieChart');
                if (resolutionContainer) {
                    resolutionContainer.closest('.chart-container').innerHTML = 
                        '<canvas id="resolutionPieChart"></canvas>';
                }
                createResolutionCharts(data);
            }
        })
        .catch(error => {
            console.error('Fehler beim Laden des Auflösungsdiagramms:', error);
            // Fehleranzeige in der UI
            const resolutionContainer = document.getElementById('resolutionPieChart');
            if (resolutionContainer) {
                resolutionContainer.closest('.chart-container').innerHTML = 
                    '<div class="alert alert-danger m-3">Fehler beim Laden der Auflösungsdaten</div>';
            }
        });
}

/**
 * Lädt Daten für Codec-Diagramme
 */
function loadCodecCharts() {
    fetch('/api/stats/codec')
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            // Prüfen auf verschiedene Datenstrukturen
            if (data) {
                // Element für Fehleranzeige zurücksetzen
                const codecContainer = document.getElementById('codecPieChart');
                if (codecContainer) {
                    codecContainer.closest('.chart-container').innerHTML = 
                        '<canvas id="codecPieChart"></canvas>';
                }
                createCodecCharts(data);
            }
        })
        .catch(error => {
            console.error('Fehler beim Laden des Codec-Diagramms:', error);
            // Fehleranzeige in der UI
            const codecContainer = document.getElementById('codecPieChart');
            if (codecContainer) {
                codecContainer.closest('.chart-container').innerHTML = 
                    '<div class="alert alert-danger m-3">Fehler beim Laden der Codec-Daten</div>';
            }
        });
}

/**
 * Lädt Daten für HDR-Diagramme
 */
function loadHDRChart() {
    fetch('/api/stats/hdr?chart=true')
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            // Prüfen auf verschiedene Datenstrukturen
            if (data) {
                // Element für Fehleranzeige zurücksetzen
                const hdrContainer = document.getElementById('hdrChart');
                if (hdrContainer) {
                    hdrContainer.closest('.chart-container').innerHTML = 
                        '<canvas id="hdrChart"></canvas>';
                }
                createHDRChart(data);
            }
        })
        .catch(error => {
            console.error('Fehler beim Laden des HDR-Format-Diagramms:', error);
            // Fehleranzeige in der UI
            const hdrContainer = document.getElementById('hdrChart');
            if (hdrContainer) {
                hdrContainer.closest('.chart-container').innerHTML = 
                    '<div class="alert alert-danger m-3">Fehler beim Laden der HDR-Daten</div>';
            }
        });
}

/**
 * Lädt Daten für Speicherdiagramme
 */
function loadStorageChart() {
    fetch('/api/stats/resolution')
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            if (data && data.storage) {
                createStorageDistributionChart(data);
            }
        })
        .catch(error => {
            console.error('Fehler beim Laden der Speicherverteilung:', error);
        });
}

/**
 * Lädt Top-Animes nach verschiedenen Kriterien
 */
function loadTopAnimes(sortBy) {
    const containerId = sortBy === 'size' ? 'topAnimesSize' : 'topAnimesEpisodes';
    const container = document.getElementById(containerId);
    
    if (!container) return;
    
    // Ladezustand anzeigen
    container.innerHTML = `
        <div class="text-center p-4">
            <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">Laden...</span>
            </div>
        </div>
    `;
    
    fetch(`/api/stats/top_animes?sort_by=${sortBy}`)
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            if (!data || data.length === 0) {
                container.innerHTML = '<div class="text-center p-3">Keine Daten verfügbar</div>';
                return;
            }
            
            let html = '<div class="list-group list-group-flush">';
            
            data.forEach((anime, index) => {
                let detailText, badgeClass;
                
                if (sortBy === 'size') {
                    detailText = anime.size_formatted || 'Unbekannt';
                    badgeClass = 'bg-info';
                } else {
                    detailText = `${anime.episode_count || 0} Episoden`;
                    badgeClass = 'bg-primary';
                }
                
                html += `
                    <a href="/anime/${anime.id}" class="list-group-item list-group-item-action d-flex justify-content-between align-items-center">
                        <div>
                            <span class="badge bg-secondary me-2">#${index + 1}</span>
                            ${anime.name || 'Unbekannt'}
                        </div>
                        <span class="badge ${badgeClass} rounded-pill">${detailText}</span>
                    </a>
                `;
            });
            
            html += '</div>';
            container.innerHTML = html;
        })
        .catch(error => {
            console.error(`Fehler beim Laden der Top-Animes (${sortBy}):`, error);
            container.innerHTML = '<div class="alert alert-danger m-3">Fehler beim Laden der Daten</div>';
        });
}

// Verhindere mehrfache Initialisierung mit einer Flag
let statsInitialized = false;

// Initialisierung beim Laden der Seite
document.addEventListener('DOMContentLoaded', function() {
    // Nur initialisieren, wenn das Dashboard existiert und noch nicht initialisiert wurde
    if (document.querySelector('.stats-dashboard') && !statsInitialized) {
        statsInitialized = true;
        console.log('Initialisiere erweiterte Statistiken...');
        initEnhancedStats();
    }
});
