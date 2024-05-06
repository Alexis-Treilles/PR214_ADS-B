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
    // Appeler la fonction de chargement des données au démarrage
    loadAirportData();

    return map;
}
function updateSidebar(type, content) {
    const sidebar = document.getElementById('sidebar');
    if (!sidebar) {
        console.error("La barre latérale n'a pas été trouvée.");
        return;
    }

    const flightSidebar = document.getElementById('flight-info-sidebar');
    const airportSidebar = document.getElementById('airport-info-sidebar');

    // Vérifier si la barre latérale est fermée
    const isSidebarClosed = sidebar.style.display === 'none';

    if (type === 'flight') {
        if (!flightSidebar) {
            console.error("La barre latérale des informations de vol n'a pas été trouvée.");
            return;
        }
        flightSidebar.innerHTML = content;
        flightSidebar.style.display = 'block';
        if (airportSidebar) {
            airportSidebar.style.display = 'none';
        }
    } else if (type === 'airport') {
        if (!airportSidebar) {
            console.error("La barre latérale des informations d'aéroport n'a pas été trouvée.");
            return;
        }
        airportSidebar.innerHTML = content;
        airportSidebar.style.display = 'block';
        if (flightSidebar) {
            flightSidebar.style.display = 'none';
        }
    } else {
        // Si le type n'est ni "flight" ni "airport", masquer les deux sidebars
        if (flightSidebar) {
            flightSidebar.style.display = 'none';
        }
        if (airportSidebar) {
            airportSidebar.style.display = 'none';
        }
    }

    // Si la barre latérale était fermée, la réouvrir
    if (isSidebarClosed) {
        sidebar.style.display = 'block';
    }
}



// Fonction pour masquer la barre latérale
function closeSidebar() {
    const sidebar = document.getElementById('sidebar');
    sidebar.style.display = 'none';
    document.getElementById('header').style.display = 'none';
    const flightSidebar = document.getElementById('flight-info-sidebar');
    const airportSidebar = document.getElementById('airport-info-sidebar');
    flightSidebar.innerHTML = ''; // Efface le contenu de la barre latérale des informations de vol
    airportSidebar.innerHTML = ''; // Efface le contenu de la barre latérale des informations d'aéroport
}
// Fonction pour supprimer tous les tracés de la carte
function removePolylines(map) {
    map.eachLayer(function(layer) {
        if (layer instanceof L.Polyline) {
            map.removeLayer(layer);
        }
    });
}


function displayAirportsFromCSV(airportData) {
    if (!Array.isArray(airportData)) {
        console.error("Les données chargées ne sont pas un tableau");
        return;
    }
    airportData.forEach(airport => {
        const airportIcon = createAirportIcon();
        const marker = L.marker([parseFloat(airport.lat), parseFloat(airport.lon)], {icon: airportIcon});
        marker.on('click', function() {
            updateSidebarAirport(airport);
        });
        //marker.bindPopup(`<b>${airport.name}</b><br/>${airport.city}, ${airport.country}`);
        airportsLayerGroup.addLayer(marker);
    });
}



// Fonction pour créer une icône d'aéroport avec une taille réduite
function createAirportIcon() {
    return L.icon({
        iconUrl: './img/airport.png', // Assurez-vous d'avoir une icône appropriée pour les aéroports
        iconSize: [20, 20], // Taille originale réduite d'un facteur 3 (ajustez selon la taille originale de votre icône)
        iconAnchor: [10, 10], // Ajustement de l'ancre pour que l'icône soit centrée sur la position
    });
}


async function loadAirportData() {
    try {
        const response = await fetch('json/european_airports.json');
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        let airportData = await response.json();

        // Convertir l'objet en tableau si nécessaire
        if (!Array.isArray(airportData)) {
            // Conversion en supposant que l'objet est de la forme {key1: obj1, key2: obj2, ...}
            airportData = Object.values(airportData);
        }

        displayAirportsFromCSV(airportData);
    } catch (error) {
        console.error("Erreur lors du chargement des données des aéroports :", error);
    }
}



// Fonction pour mettre à jour le tracé de la trajectoire en temps réel
function updatePathOnDataChange(selectedMarker, selectedPath, icao, path_table,map) {
    const latestPathData = path_table[icao][0];
    const pathCoordinates = path_table[icao].map(point => [point.latitude, point.longitude]);

    // Si le marqueur sélectionné correspond à l'icao des nouvelles données
    if (selectedMarker && selectedMarker.options.icao === icao) {
        // Supprimer l'ancien chemin
        if (selectedPath) {
            map.removeLayer(selectedPath);
        }
        
        // Mettre à jour le chemin associé avec les nouvelles données
        const color = getColorForVelocity(latestPathData.velocity);
        selectedPath = L.polyline(pathCoordinates, { color }).addTo(map);
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
            updatePathOnDataChange(selectedMarker, selectedPath, selectedMarker.options.icao, path_table,map);
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
// Déclarer un objet pour stocker les angles précédents de chaque avion
const anglesPrecedents = {};

function displayLatestPositions(map, icao_list, path_table) {
    planesLayerGroup.clearLayers(); // Supprime tous les marqueurs d'avions précédents

    for (const icao of icao_list) {
        const flightData = path_table[icao][0];
        const anglePrecedent = anglesPrecedents[icao]; // Obtenir l'angle précédent de cet avion
        const angle = calculateAngle(path_table[icao], anglePrecedent); // Passer l'angle précédent à la fonction calculateAngle
        anglesPrecedents[icao] = angle; // Stocker l'angle actuel comme l'angle précédent pour la prochaine itération
        const color = getColorForVelocity(flightData.velocity);
        const airplaneIcon = createAirplaneIcon(angle,color);

        const marker = L.marker([flightData.latitude, flightData.longitude], {icon: airplaneIcon, icao: icao}).addTo(map);

        addMarkerClickListener(map, marker, icao, flightData, path_table);

        planesLayerGroup.addLayer(marker);
    }
}

// Fonction pour calculer l'angle de rotation de l'avion
function calculateAngle(pathData, anglePrecedent) {
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
        if (angle == 180) {
            angle = anglePrecedent; // Utiliser l'angle précédent si l'angle calculé est égal à 180
        }
        angle = Number(angle.toFixed(0));
    }
    
    return angle;
}


// Fonction pour créer l'icône d'avion avec une couleur spécifiée
function createAirplaneIcon(angle,color) {
    return L.divIcon({
        className: 'avion-container',
        html: `<img src="./img/icons8-plane-30.png" class="avion-img" style="transform: rotate(${angle}deg);filter: drop-shadow(2px 4px 6px ${color});">`,
        iconSize: [30, 30],
        iconAnchor: [15, 15]
    });
}

// Fonction pour ajouter le gestionnaire de clic sur le marqueur
function addMarkerClickListener(map, marker, icao, flightData, path_table) {
    marker.on('click', function() {
        marker.setOpacity(1);
        removePolylines(map);

        const pathCoordinates = path_table[icao].map(point => [point.latitude, point.longitude]);
        const color = getColorForVelocity(flightData.velocity); // Obtenir la couleur en fonction de la vitesse
        const currentPath = L.polyline(pathCoordinates, { color }).addTo(map); // Utiliser la même couleur que l'avion
        
        planesLayerGroup.addLayer(currentPath);

        selectedMarker = marker;
        selectedPath = currentPath;

        updateSidebarFlight(flightData);

        document.getElementById('sidebar').style.display = 'block';
        document.getElementById('header').style.display = 'block';
    });
}

function updateSidebarFlight(flightData) {
    const flightSidebar = document.getElementById('flight-info-sidebar'); // Ajout de cette ligne pour récupérer à nouveau flightSidebar
    const sidebarContent = `
        <h3>Flight Details</h3>
        <p><strong>ICAO:</strong> ${flightData.icao}</p>
        <p><strong>Latitude:</strong> ${flightData.latitude}</p>
        <p><strong>Longitude:</strong> ${flightData.longitude}</p>
        <p><strong>Timestamp:</strong> ${new Date(flightData.timestamp * 1000).toLocaleString()}</p>
        <p><strong>Aircraft Type:</strong> ${flightData.aircraft_type}</p>
        <p><strong>Velocity:</strong> ${flightData.velocity} km/h</p>
        <p><strong>Heading:</strong> ${flightData.heading}°</p>
    `;
    updateSidebar('flight', sidebarContent);
}

function updateSidebarAirport(airport) {
    const sidebarContent = `
        <h2>${airport.name}</h2>
        <p><strong>City:</strong> ${airport.city}</p>
        <p><strong>Country:</strong> ${airport.country}</p>
        <p><strong>Latitude:</strong> ${airport.lat}</p>
        <p><strong>Longitude:</strong> ${airport.lon}</p>
        <p><strong>ICAO:</strong> ${airport.icao || 'N/A'}</p>
        <p><strong>IATA:</strong> ${airport.iata_code || 'N/A'}</p>
    `;
    updateSidebar('airport', sidebarContent);
}

// Initialisation de la carte et écoute des changements
const map = initializeMap();

let airportsLayerGroup = L.layerGroup().addTo(map);
let planesLayerGroup = L.layerGroup().addTo(map);
listenForChangesAndUpdatePath(db, map);

// Gestionnaire pour le clic sur la carte
map.on('click', function() {
    closeSidebar();
    removePolylines(map);
})

// Gestionnaire pour la touche Échap
document.onkeydown = function(evt) {
    evt = evt || window.event;
    if (evt.key === "Escape") {
        closeSidebar();
        removePolylines(map);
    }
};
function getColorForVelocity(velocity) {
    const Mach = 1224  ; // Unité pour la vitesse du son
   if (velocity <= 0.15*Mach) {
       return 'blue';
   } else if (velocity <=  0.30*Mach) {
       return 'purple';
   } else if (velocity <=  0.45*Mach) {
       return 'yellow';
   } else if (velocity <=  0.60*Mach) {
       return 'orange';
   } else if (velocity <=  0.75*Mach) {
       return 'red';
   } else if (velocity <= 0.90*Mach) {
       return '#8B008B'; // Rouge violet
   }else if (velocity <= 6.70*Mach) {
       return 'black';
   }
}