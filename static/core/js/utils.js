document.addEventListener('DOMContentLoaded', function() {
    const latitudeElement = document.getElementById('latitude');
    const longitudeElement = document.getElementById('longitude');
    const geolocationDataElement = document.getElementById('geolocation-data');
    const inRangeElement = document.getElementById('in-range');

    // Predefined latitude and longitude
    const predefinedLatitude = 3.952541; // ict u latitude
    const predefinedLongitude = 11.348383; // ict u longitude

    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(showPosition, showError);
    } else {
        alert("Geolocation is not supported by this browser.");
    }

    function showPosition(position) {
        const latitude = position.coords.latitude;
        const longitude = position.coords.longitude;

        latitudeElement.textContent = latitude;
        longitudeElement.textContent = longitude;

        // Print the entire geolocation data object
        geolocationDataElement.textContent = JSON.stringify(position, null, 2);

        // Calculate the distance between the two points
        const distance = calculateDistance(latitude, longitude, predefinedLatitude, predefinedLongitude);

        // Check if the distance is within 20 meters
        if (distance <= 20) {
            inRangeElement.textContent = "Yes";
        } else {
            inRangeElement.textContent = "No";
        }
    }

    function showError(error) {
        switch(error.code) {
            case error.PERMISSION_DENIED:
                alert("User denied the request for Geolocation.");
                break;
            case error.POSITION_UNAVAILABLE:
                alert("Location information is unavailable.");
                break;
            case error.TIMEOUT:
                alert("The request to get user location timed out.");
                break;
            case error.UNKNOWN_ERROR:
                alert("An unknown error occurred.");
                break;
        }
    }

    function calculateDistance(lat1, lon1, lat2, lon2) {
        const R = 6371e3; // Radius of the Earth in meters
        const φ1 = lat1 * Math.PI / 180;
        const φ2 = lat2 * Math.PI / 180;
        const Δφ = (lat2 - lat1) * Math.PI / 180;
        const Δλ = (lon2 - lon1) * Math.PI / 180;

        const a = Math.sin(Δφ / 2) * Math.sin(Δφ / 2) +
                  Math.cos(φ1) * Math.cos(φ2) *
                  Math.sin(Δλ / 2) * Math.sin(Δλ / 2);
        const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));

        const distance = R * c; // Distance in meters
        return distance;
    }
});