import { initializeApp } from "https://www.gstatic.com/firebasejs/9.1.1/firebase-app.js";
import { getDatabase, ref, onValue } from "https://www.gstatic.com/firebasejs/9.1.1/firebase-database.js";

// Configuration de Firebase
var firebaseConfig = {
    apiKey: "AIzaSyBm35l7_I-2Y19OVxxuLKIaysUmqBnhWSI",
    authDomain: "test-349ac.firebaseapp.com",
    databaseURL: "https://test-349ac-default-rtdb.europe-west1.firebasedatabase.app",
    projectId: "test-349ac",
    storageBucket: "test-349ac.appspot.com",
    messagingSenderId: "1082188343275",
    appId: "1:1082188343275:web:b9466faefd2172d5d45bae"
};
const app = initializeApp(firebaseConfig);
var db = getDatabase();

        // Initialiser la carte Leaflet
        var map = L.map('map').setView([44.805938, -0.606223], 7);
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            maxZoom: 19,
            attribution: '© OpenStreetMap contributors'
        }).addTo(map);
    
        
        map.on('click', function() {
            // Fermer la sidebar
            document.getElementById('sidebar').style.display = 'none';
            
            // Supprimer tous les tracés (polyline) de la carte
            map.eachLayer(function(layer) {
                if (layer instanceof L.Polyline) {
                    map.removeLayer(layer);
                }
            });
        });
        // Référence à la base de données
        var the_ref = ref(db, '/');

        // Stocker les marqueurs des avions
        var airplaneMarkers = {};

        // Écouter les changements en temps réel
        onValue(the_ref, (snapshot) => {
            // Supprimer les anciens marqueurs
            for (let key in airplaneMarkers) {
                map.removeLayer(airplaneMarkers[key]);
            }
            airplaneMarkers = {};
        
            var icao_list = [];
            var path_table = [];
            const allFlightData = snapshot.val();
        
            // Initialiser un objet pour stocker les données triées
            var sortedPathData = {};
        
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
                        path_table[icao_list.indexOf(flightData.icao)] = [];
                    }
                    path_table[icao_list.indexOf(flightData.icao)].push(flightData);
                }
            }
            // Trier et choisir le dernier paquet pour chaque ICAO
            // Supposons que map et airplaneMarkers sont déjà définis

            // Supprimer les trajectoires existantes avant d'en afficher une nouvelle
            let currentPolyline = null;

            for (let i = 0; i < icao_list.length; i++) {
                path_table[i].sort((a, b) => b.timestamp - a.timestamp);
                const mostRecentFlightData = path_table[i][0];
                let angle = 0;
                if (path_table[i].length > 1) {
                    
                    const secondMostRecentFlightData = path_table[i][1];

                    
                    // Conversion des latitudes et longitudes en radians
                    const phi1 = mostRecentFlightData.latitude * Math.PI / 180;
                    const phi2 = secondMostRecentFlightData.latitude * Math.PI / 180;
                    const deltaLambda = (secondMostRecentFlightData.longitude - mostRecentFlightData.longitude) * Math.PI / 180;
                    
                    // Calcul du cap
                    angle = Math.atan2(Math.sin(deltaLambda) * Math.cos(phi2), Math.cos(phi1) * Math.sin(phi2) - Math.sin(phi1) * Math.cos(phi2) * Math.cos(deltaLambda)) * 180 / Math.PI;
                    angle+=180
                    // Correction si l'angle est négatif
                    if (angle < 0) {
                        angle += 360;
                    }
                    angle = Number(angle.toFixed(0));
                    var airplaneIcon = L.divIcon({
                        className: 'avion-container',
                        html: '<img src="./img/icons8-plane-30.png" class="avion-img" style="transform: rotate(' + angle + 'deg);">',
                        iconSize: [30, 30], // Taille initiale de l'icône
                        iconAnchor: [15, 15]
                    });
                }
                // Utilisation d'une IIFE pour capturer le contexte de chaque marqueur
                (function(icao, flightData, angle) {
                    var marker = L.marker([flightData.latitude, flightData.longitude], {icon: airplaneIcon}).addTo(map);
                    marker.on('click', function(e) {
                        // Masquer tous les marqueurs sauf celui-ci et supprimer la trajectoire précédente
                        marker.setOpacity(1); // Assurez-vous que ce marqueur reste visible

                        if (currentPolyline) {
                            map.removeLayer(currentPolyline);
                        }

                        // Dessiner la nouvelle trajectoire
                        const pathCoordinates = path_table[icao_list.indexOf(icao_list[i])].map(point => [point.latitude, point.longitude]);
                        currentPolyline = L.polyline(pathCoordinates, { color: 'red' }).addTo(map);
                        document.getElementById('flight-info-sidebar').innerHTML = `
                            <p>Latitude: ${flightData.latitude}</p>
                            <p>Longitude: ${flightData.longitude}</p>
                            <p>Timestamp: ${new Date(flightData.timestamp * 1000).toLocaleString()}</p>
                            <p>Aircraft_type: ${flightData.aircraft_type}</p>
                            <p>Vitesse: ${flightData.velocity}</p>
                            <p>Cap: ${angle}°</p>
                        `;
                        // Afficher la sidebar
                        document.getElementById('sidebar').style.display = 'block';
                    });
                    airplaneMarkers[icao_list[i]] = marker;
                })(icao_list[i], mostRecentFlightData, angle);
            }

            // Gestionnaires pour le clic sur la carte et la touche Échap pour réafficher tous les marqueurs et supprimer la trajectoire
            map.on('click', function() {
                for (let key in airplaneMarkers) {
                    airplaneMarkers[key].setOpacity(1); // Réaffiche tous les marqueurs
                }
                if (currentPolyline) {
                    map.removeLayer(currentPolyline);
                    currentPolyline = null;
                }
            });

            document.onkeydown = function(evt) {
                evt = evt || window.event;
                if (evt.key === "Escape") {
                    for (let key in airplaneMarkers) {
                        airplaneMarkers[key].setOpacity(1); // Réaffiche tous les marqueurs
                    }
                    if (currentPolyline) {
                        map.removeLayer(currentPolyline);
                        currentPolyline = null;
                    }
                }
            }
        });
                    
        