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
            position: "right",
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
    "#4e73df", "#1cc88a", "#36b9cc", "#f6c23e", "#e74a3b", 
    "#5a5c69", "#6f42c1", "#20c9a6", "#fd7e14", "#6610f2"
];

// Farbpalette für spezifische Kategorien
const categoryColors = {
    resolutions: {
        "4K": "#6a0dad",
        "Full HD": "#2e5cb8",
        "HD": "#17a2b8",
        "SD": "#6c757d"
    },
    codecs: {
        "HEVC": "#5cb85c",
        "AV1": "#d9534f",
        "AVC": "#5bc0de",
        "VP9": "#f0ad4e",
        "MPEG": "#777777"
    },
    hdr: {
        "HDR10": "#e6a919",
        "HDR10+": "#ff9500",
        "Dolby Vision": "#a50034",
        "HLG": "#bf5700",
        "Kein HDR": "#aaaaaa"
    }
};

// Flag zum Vermeiden von mehrfacher Initialisierung
let statsInitialized = false;

/**
 * Initialisiert alle erweiterten Statistik-Diagramme
 */
function initEnhancedStats() {
    // console.log('Initialisiere erweiterte Statistiken...'); // Für Produktion entfernt
    
    // Informationssammlung aus der API
    fetch("/api/stats")
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            // Diagramme erstellen, wenn Daten verfügbar sind
            if (data) {
                // console.log('Stats-Daten erhalten:', data); // Für Produktion entfernt
                
                // Die allgemeinen Statistiken aktualisieren
                updateGeneralStats(data);
                
                // Separate API-Aufrufe für spezifische Diagramme, um Fehler zu vermeiden
                // und Belastung zu verteilen
                loadResolutionCharts();
                loadCodecCharts();
                loadHDRChart();
                loadStorageChart();
                loadContainerChart();
                
                // Top-Animes laden
                loadTopAnimes("episodes");
                loadTopAnimes("size");
            }
        })
        .catch(error => {
            console.error("Fehler beim Laden der Statistikdaten:", error);
            document.querySelectorAll(".loading-container").forEach(container => {
                container.innerHTML = "<div class=\"alert alert-danger\">Fehler beim Laden der Daten</div>";
            });
        });
}

/**
 * Aktualisiert die allgemeinen Statistiken
 */
function updateGeneralStats(data) {
    // Lade-Anzeige entfernen
    const generalStatsElement = document.getElementById("generalStats");
    const storageStatsElement = document.getElementById("storageStats");
    const hdrStatsElement = document.getElementById("hdrStats");
    const uhd4kStatsElement = document.getElementById("uhd4kStats");
    
    if (generalStatsElement) {
        if (!data.animes_count && !data.seasons_count && !data.episodes_count) {
            generalStatsElement.innerHTML = "<div class=\"alert alert-warning\">Keine Daten verfügbar</div>";
        } else {
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
    }
    
    if (storageStatsElement) {
        if (!data.total_size_formatted && !data.total_duration_formatted) {
            storageStatsElement.innerHTML = "<div class=\"alert alert-warning\">Keine Daten verfügbar</div>";
        } else {
            storageStatsElement.innerHTML = `
                <div class="d-flex flex-column">
                    <div class="stat-item mb-2">
                        <span class="stat-label">Gesamtgröße:</span>
                        <span class="stat-value" id="totalStorageSize">
                            ${data.total_size_formatted || "Unbekannt"}
                        </span>
                    </div>
                    <div class="stat-item mb-2">
                        <span class="stat-label">Gesamtdauer:</span>
                        <span class="stat-value">
                            ${data.total_duration_formatted || "Unbekannt"}
                        </span>
                    </div>
                </div>
            `;
        }
    }
    
    // Aktualisiere auch die HDR-Statistiken
    if (hdrStatsElement && data.hdr_distribution) {
        const hdrCount = data.hdr_distribution.hdr || 0;
        const totalCount = hdrCount + (data.hdr_distribution.non_hdr || 0);
        const percentage = totalCount > 0 ? Math.round((hdrCount / totalCount) * 100) : 0;
        
        hdrStatsElement.innerHTML = `
            <h3 class="display-4 text-warning">${percentage}%</h3>
            <p class="mb-0">${hdrCount} von ${totalCount} Episoden</p>
        `;
    }
    
    // Aktualisiere die 4K-Statistiken
    if (uhd4kStatsElement && data.resolution_distribution) {
        const uhd4kCount = data.resolution_distribution["4K"] || 0;
        const totalCount = Object.values(data.resolution_distribution).reduce((sum, count) => sum + count, 0);
        const percentage = totalCount > 0 ? Math.round((uhd4kCount / totalCount) * 100) : 0;
        
        uhd4kStatsElement.innerHTML = `
            <h3 class="display-4 text-info">${percentage}%</h3>
            <p class="mb-0">${uhd4kCount} von ${totalCount} Episoden</p>
        `;
    }
}

/**
 * Lädt Daten für Auflösungsdiagramme
 */
function loadResolutionCharts() {
    fetch("/api/stats/resolution")
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            // console.log('Auflösungsdaten erhalten:', data); // Für Produktion entfernt
            
            // Element für Fehleranzeige zurücksetzen
            const resolutionContainer = document.getElementById("resolutionPieChart");
            if (resolutionContainer) {
                resolutionContainer.closest(".chart-container").innerHTML = "<canvas id=\"resolutionPieChart\"></canvas>";
            }
            
            createResolutionCharts(data);
        })
        .catch(error => {
            console.error("Fehler beim Laden des Auflösungsdiagramms:", error);
            
            // Fehleranzeige in der UI
            const resolutionContainer = document.getElementById("resolutionPieChart");
            if (resolutionContainer) {
                resolutionContainer.closest(".chart-container").innerHTML = 
                    "<div class=\"alert alert-danger m-3\">Fehler beim Laden der Auflösungsdaten</div>";
            }
        });
}

/**
 * Erstellt Auflösungs-Diagramme
 */
function createResolutionCharts(data) {
    // Stellt sicher, dass wir eine gültige Datenstruktur haben
    if (!data.distribution || !data.distribution.length) {
        console.error("Keine gültige Auflösungsdatenstruktur:", data);
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
            const resolution = item.resolution || "Unbekannt";
            labels.push(resolution);
            values.push(item.count);
            colors.push(categoryColors.resolutions[resolution] || getRandomColor());
        });
    
    // Auflösungsverteilung als Tortendiagramm
    const resolutionPieCtx = document.getElementById("resolutionPieChart");
    if (resolutionPieCtx) {
        new Chart(resolutionPieCtx, {
            type: "pie",
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
                        text: "Auflösungsverteilung"
                    }
                }
            }
        });
    }
}

/**
 * Lädt Daten für Codec-Diagramme
 */
function loadCodecCharts() {
    fetch("/api/stats/codec")
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            // console.log('Codec-Daten erhalten:', data); // Für Produktion entfernt
            
            // Element für Fehleranzeige zurücksetzen
            const codecContainer = document.getElementById("codecPieChart");
            if (codecContainer) {
                codecContainer.closest(".chart-container").innerHTML = "<canvas id=\"codecPieChart\"></canvas>";
            }
            
            createCodecCharts(data);
        })
        .catch(error => {
            console.error("Fehler beim Laden des Codec-Diagramms:", error);
            
            // Fehleranzeige in der UI
            const codecContainer = document.getElementById("codecPieChart");
            if (codecContainer) {
                codecContainer.closest(".chart-container").innerHTML = 
                    "<div class=\"alert alert-danger m-3\">Fehler beim Laden der Codec-Daten</div>";
            }
        });
}

/**
 * Erstellt Codec-Diagramme
 */
function createCodecCharts(data) {
    // Stellt sicher, dass wir eine gültige Datenstruktur haben
    if (!data.distribution || !data.distribution.length) {
        console.error("Keine gültige Codec-Datenstruktur:", data);
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
            let codec = item.codec || "Unbekannt";
            if (codec.includes("HEVC") || codec.includes("x265")) {
                codec = "HEVC";
            } else if (codec.includes("AVC") || codec.includes("x264")) {
                codec = "AVC";
            } else if (codec.length > 15) {
                codec = codec.substring(0, 15) + "...";
            }
            
            labels.push(codec);
            values.push(item.count);
            colors.push(categoryColors.codecs[codec] || getRandomColor());
        });
    
    // Codec-Verteilung als Tortendiagramm
    const codecPieCtx = document.getElementById("codecPieChart");
    if (codecPieCtx) {
        new Chart(codecPieCtx, {
            type: "doughnut",
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
                        text: "Codec-Verteilung"
                    }
                }
            }
        });
    }
}

/**
 * Lädt Daten für HDR-Diagramme
 */
function loadHDRChart() {
    fetch("/api/stats/hdr?chart=true")
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            // console.log('HDR-Daten erhalten:', data); // Für Produktion entfernt
            
            // Element für Fehleranzeige zurücksetzen
            const hdrContainer = document.getElementById("hdrChart");
            if (hdrContainer) {
                hdrContainer.closest(".chart-container").innerHTML = "<canvas id=\"hdrChart\"></canvas>";
            }
            
            createHDRChart(data);
        })
        .catch(error => {
            console.error("Fehler beim Laden des HDR-Format-Diagramms:", error);
            
            // Fehleranzeige in der UI
            const hdrContainer = document.getElementById("hdrChart");
            if (hdrContainer) {
                hdrContainer.closest(".chart-container").innerHTML = 
                    "<div class=\"alert alert-danger m-3\">Fehler beim Laden der HDR-Daten</div>";
            }
        });
}

/**
 * Erstellt HDR-Diagramm
 */
function createHDRChart(data) {
    // Stellt sicher, dass wir eine gültige Datenstruktur haben
    if (!data.distribution || !data.distribution.length) {
        console.error("Keine gültige HDR-Datenstruktur:", data);
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
            const format = item.format || "Unbekannt";
            labels.push(format);
            values.push(item.count);
            colors.push(categoryColors.hdr[format] || getRandomColor());
        });
    
    // HDR-Verteilung als Tortendiagramm
    const hdrCtx = document.getElementById("hdrChart");
    if (hdrCtx) {
        new Chart(hdrCtx, {
            type: "pie",
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
                        text: "HDR-Formate"
                    }
                }
            }
        });
    }
}

/**
 * Lädt Daten für Speicherdiagramme
 */
function loadStorageChart() {
    fetch("/api/stats/resolution")
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            // console.log('Speicherdaten erhalten:', data); // Für Produktion entfernt
            if (data && data.storage) {
                createStorageDistributionChart(data);
            }
        })
        .catch(error => {
            console.error("Fehler beim Laden der Speicherverteilung:", error);
            
            // Fehleranzeige in der UI
            const storageContainer = document.getElementById("storageDistributionChart");
            if (storageContainer) {
                storageContainer.closest(".chart-container").innerHTML = 
                    "<div class=\"alert alert-danger m-3\">Fehler beim Laden der Speicherdaten</div>";
            }
        });
}

/**
 * Erstellt Speicherverbrauchsdiagramm
 */
function createStorageDistributionChart(data) {
    if (!data.storage || Object.keys(data.storage).length === 0) {
        console.error("Keine Speicherverteilungsdaten gefunden:", data);
        return;
    }
    
    // Vorbereiten der Daten für Balkendiagramm
    const labels = [];
    const values = [];
    const colors = [];
    
    // Sortieren nach Speicherverbrauch (absteigend)
    const sortedStorage = Object.entries(data.storage)
        .sort((a, b) => b[1] - a[1]);
    
    // Die größten Kategorien extrahieren (Top 5)
    const topStorage = sortedStorage.slice(0, 5);
    
    // Daten für Chart sammeln
    topStorage.forEach(([category, storage]) => {
        // Speichergröße in lesbares Format umwandeln
        let sizeFormatted;
        if (storage < 1024**3) {  // Kleiner als 1 GB
            sizeFormatted = `${(storage / 1024**2).toFixed(2)} MB`;
        } else {
            sizeFormatted = `${(storage / 1024**3).toFixed(2)} GB`;
        }
        
        labels.push(category);
        values.push(storage / 1024**3); // In GB umrechnen
        colors.push(categoryColors.resolutions[category] || getRandomColor());
    });
    
    // Speicherverteilung als Balkendiagramm
    const storageDistributionCtx = document.getElementById("storageDistributionChart");
    if (storageDistributionCtx) {
        new Chart(storageDistributionCtx, {
            type: "bar",
            data: {
                labels: labels,
                datasets: [{
                    label: "Speichergröße (GB)",
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
                        text: "Speicherverbrauch nach Auflösung"
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: "Speichergröße (GB)"
                        }
                    }
                }
            }
        });
    }
}

/**
 * Lädt Daten für das Container-Diagramm
 */
function loadContainerChart() {
    fetch("/api/container")
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            // console.log('Container-Daten erhalten:', data); // Für Produktion entfernt
            if (data && data.container_distribution) {
                createContainerChart(data.container_distribution);
            }
        })
        .catch(error => {
            console.error("Fehler beim Laden des Container-Diagramms:", error);
            
            // Fehleranzeige in der UI
            const containerChart = document.getElementById("containerChart");
            if (containerChart) {
                containerChart.closest(".chart-container").innerHTML = 
                    "<div class=\"alert alert-danger m-3\">Fehler beim Laden der Container-Daten</div>";
            }
        });
}

/**
 * Erstellt Container-Diagramm
 */
function createContainerChart(data) {
    if (!data || data.length === 0) {
        console.error("Keine Container-Daten gefunden");
        return;
    }
    
    // Vorbereiten der Daten für Balkendiagramm
    const labels = data.map(item => item.container);
    const values = data.map(item => item.count);
    
    // Farben für Container-Formate
    const backgroundColors = [
        "#607D8B", "#795548", "#9E9E9E", "#FF5722", "#FFEB3B",
        "#CDDC39", "#4CAF50", "#009688", "#00BCD4", "#03A9F4"
    ];
    
    const ctx = document.getElementById("containerChart");
    if (ctx) {
        new Chart(ctx, {
            type: "bar",
            data: {
                labels: labels,
                datasets: [{
                    label: "Anzahl",
                    data: values,
                    backgroundColor: backgroundColors.slice(0, labels.length),
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
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
}

/**
 * Lädt Top-Animes nach verschiedenen Kriterien
 */
function loadTopAnimes(sortBy) {
    const containerId = sortBy === "size" ? "topAnimesSize" : "topAnimesEpisodes";
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
            // console.log(`Top-Animes (${sortBy}) erhalten:`, data); // Für Produktion entfernt
            
            if (!data || data.length === 0) {
                container.innerHTML = "<div class=\"text-center p-3\">Keine Daten verfügbar</div>";
                return;
            }
            
            let html = "<div class=\"list-group list-group-flush\">";
            
            data.forEach((anime, index) => {
                let detailText, badgeClass;
                
                if (sortBy === "size") {
                    detailText = anime.size_formatted || "Unbekannt";
                    badgeClass = "bg-info";
                } else {
                    detailText = `${anime.episode_count || 0} Episoden`;
                    badgeClass = "bg-primary";
                }
                
                html += `
                    <a href="/anime/${anime.id}" class="list-group-item list-group-item-action d-flex justify-content-between align-items-center">
                        <div>
                            <span class="badge bg-secondary me-2">#${index + 1}</span>
                            ${anime.name || "Unbekannt"}
                        </div>
                        <span class="badge ${badgeClass} rounded-pill">${detailText}</span>
                    </a>
                `;
            });
            
            html += "</div>";
            container.innerHTML = html;
        })
        .catch(error => {
            console.error(`Fehler beim Laden der Top-Animes (${sortBy}):`, error);
            container.innerHTML = "<div class=\"alert alert-danger m-3\">Fehler beim Laden der Daten</div>";
        });
}

/**
 * Erzeugt eine zufällige Farbe im Hex-Format
 */
function getRandomColor() {
    const letters = "0123456789ABCDEF";
    let color = "#";
    for (let i = 0; i < 6; i++) {
        color += letters[Math.floor(Math.random() * 16)];
    }
    return color;
}

// Initialisierung beim Laden der Seite
document.addEventListener("DOMContentLoaded", function() {
    // Nur initialisieren, wenn das Dashboard existiert und noch nicht initialisiert wurde
    if (document.querySelector(".stats-dashboard") && !statsInitialized) {
        statsInitialized = true;
        // console.log('Starte Initialisierung der erweiterten Statistiken...'); // Für Produktion entfernt
        initEnhancedStats();
    }
});
