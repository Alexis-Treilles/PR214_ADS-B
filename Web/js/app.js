import { initializeApp } from "https://www.gstatic.com/firebasejs/9.1.1/firebase-app.js";
import { getDatabase, ref, onValue } from "https://www.gstatic.com/firebasejs/9.1.1/firebase-database.js";

// Configuration de Firebase
const firebaseConfig = {
    apiKey: "AIzaSyBm35l7_I-2Y19OVxxuLKIaysUmqBnhWSI",
    authDomain: "test-349ac.firebaseapp.com",
    databaseURL: "https://test-349ac-default-rtdb.europe-west1.firebasedatabase.app",
    projectId: "test-349ac",
    storageBucket: "test-349ac.appspot.com",
    messagingSenderId: "1082188343275",
    appId: "1:1082188343275:web:b9466faefd2172d5d45bae"
};
const app = initializeApp(firebaseConfig);
const db = getDatabase();

// Déclaration des variables globales pour stocker le marqueur sélectionné et son chemin associé
let selectedMarker = null;
let selectedPath = null;

// Fonction pour initialiser la carte Leaflet
function initializeMap() {
    const map = L.map('map').setView([44.805938, -0.606223], 9);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 19,
        attribution: '© OpenStreetMap contributors'
    }).addTo(map);

    map.on('click', function() {
        closeSidebar();
        removePolylines(map);
    });

    return map;
}

// Fonction pour masquer la barre latérale
function closeSidebar() {
    document.getElementById('sidebar').style.display = 'none';
}

// Fonction pour supprimer tous les tracés de la carte
function removePolylines(map) {
    map.eachLayer(function(layer) {
        if (layer instanceof L.Polyline) {
            map.removeLayer(layer);
        }
    });
}

// Fonction pour mettre à jour le tracé de la trajectoire en temps réel
function updatePathOnDataChange(selectedMarker, selectedPath, icao, path_table) {
    const latestPathData = path_table[icao][0];
    const pathCoordinates = path_table[icao].map(point => [point.latitude, point.longitude]);

    // Si le marqueur sélectionné correspond à l'icao des nouvelles données
    if (selectedMarker && selectedMarker.options.icao === icao) {
        // Supprimer l'ancien chemin
        if (selectedPath) {
            map.removeLayer(selectedPath);
        }
        
        // Mettre à jour le chemin associé avec les nouvelles données
        selectedPath = L.polyline(pathCoordinates, { color: 'red' }).addTo(map);
    }
}

// Fonction pour écouter les changements en temps réel et mettre à jour le tracé de la trajectoire
function listenForChangesAndUpdatePath(db, map) {
    const the_ref = ref(db, '/');

    onValue(the_ref, (snapshot) => {
        const allFlightData = snapshot.val();
        const { icao_list, path_table } = processFlightData(allFlightData);

        // Mettre à jour le tracé de la trajectoire si le marqueur sélectionné existe
        if (selectedMarker) {
            updatePathOnDataChange(selectedMarker, selectedPath, selectedMarker.options.icao, path_table);
        }

        // Appeler la fonction pour afficher les positions les plus récentes des avions sur la carte
        displayLatestPositions(map, icao_list, path_table);
    });
}


// Fonction pour traiter les données de vol
function processFlightData(allFlightData) {
    const icao_list = [];
    const path_table = {};

    for (const key in allFlightData) {
        if (allFlightData.hasOwnProperty(key)) {
            const rawFlightData = allFlightData[key];
            const flightData = {
                latitude: rawFlightData.latitude,
                longitude: rawFlightData.longitude,
                timestamp: rawFlightData.timestamp,
                icao: rawFlightData.icao,
                aircraft_type: rawFlightData.aircraft_type,
                velocity: rawFlightData.velocity,
                heading: rawFlightData.heading
            };

            if (!icao_list.includes(flightData.icao)){
                icao_list.push(flightData.icao);
                path_table[flightData.icao] = [];
            }
            path_table[flightData.icao].push(flightData);
        }
    }

    for (const icao in path_table) {
        path_table[icao].sort((a, b) => b.timestamp - a.timestamp);
    }

    return { icao_list, path_table };
}

// Fonction pour afficher les positions les plus récentes des avions sur la carte
// Fonction pour afficher les positions les plus récentes des avions sur la carte
function displayLatestPositions(map, icao_list, path_table) {
    // Supprimer tous les marqueurs existants sur la carte
    map.eachLayer(function(layer) {
        if (layer instanceof L.Marker) {
            map.removeLayer(layer);
        }
    });

    // Ajouter les nouveaux marqueurs d'avion sur la carte
    for (const icao of icao_list) {
        const flightData = path_table[icao][0];
        const angle = calculateAngle(path_table[icao]);

        const airplaneIcon = createAirplaneIcon(angle);

        const marker = L.marker([flightData.latitude, flightData.longitude], {icon: airplaneIcon, icao: icao}).addTo(map);
        addMarkerClickListener(map, marker, icao, flightData, path_table);
    }
}


// Fonction pour calculer l'angle de rotation de l'avion
function calculateAngle(pathData) {
    let angle = 0;

    if (pathData.length > 1) {
        const mostRecentFlightData = pathData[0];
        const secondMostRecentFlightData = pathData[1];

        const phi1 = mostRecentFlightData.latitude * Math.PI / 180;
        const phi2 = secondMostRecentFlightData.latitude * Math.PI / 180;
        const deltaLambda = (secondMostRecentFlightData.longitude - mostRecentFlightData.longitude) * Math.PI / 180;

        angle = Math.atan2(Math.sin(deltaLambda) * Math.cos(phi2), Math.cos(phi1) * Math.sin(phi2) - Math.sin(phi1) * Math.cos(phi2) * Math.cos(deltaLambda)) * 180 / Math.PI;
        angle += 180;

        if (angle < 0) {
            angle += 360;
        }
        angle = Number(angle.toFixed(0));
    }

    return angle;
}

// Fonction pour créer l'icône d'avion
function createAirplaneIcon(angle) {
    return L.divIcon({
        className: 'avion-container',
        html: `<img src="./img/icons8-plane-30.png" class="avion-img" style="transform: rotate(${angle}deg);">`,
        iconSize: [30, 30],
        iconAnchor: [15, 15]
    });
}

// Fonction pour ajouter le gestionnaire de clic sur le marqueur
function addMarkerClickListener(map, marker, icao, flightData, path_table) {
    marker.on('click', function() {
        marker.setOpacity(1);

        const pathCoordinates = path_table[icao].map(point => [point.latitude, point.longitude]);
        const currentPath = L.polyline(pathCoordinates, { color: 'red' }).addTo(map);

        // Supprimer l'ancien chemin s'il existe
        if (selectedPath) {
            map.removeLayer(selectedPath);
        }

        // Mettre à jour le marqueur sélectionné et son chemin associé
        selectedMarker = marker;
        selectedPath = currentPath;

        document.getElementById('flight-info-sidebar').innerHTML = `
            <p>Latitude: ${flightData.latitude}</p>
            <p>Longitude: ${flightData.longitude}</p>
            <p>Timestamp: ${new Date(flightData.timestamp * 1000).toLocaleString()}</p>
            <p>Aircraft_type: ${flightData.aircraft_type}</p>
            <p>Vitesse: ${flightData.velocity}</p>
            <p>Cap: ${calculateAngle(path_table[icao])}°</p>
        `;

        document.getElementById('sidebar').style.display = 'block';
    });
}

// Initialisation de la carte et écoute des changements
const map = initializeMap();
listenForChangesAndUpdatePath(db, map);

// Gestionnaire pour le clic sur la carte
map.on('click', function() {
    closeSidebar();
    removePolylines(map);
});

// Gestionnaire pour la touche Échap
document.onkeydown = function(evt) {
    evt = evt || window.event;
    if (evt.key === "Escape") {
        closeSidebar();
        removePolylines(map);
    }
};

