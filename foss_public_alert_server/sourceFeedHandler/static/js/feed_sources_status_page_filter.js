function toggleButtonActiveClass(buttonId) {
    const button = document.getElementById(buttonId);
    if(button.classList.contains("active")) {
        // button is active, set as unactive
        button.classList.remove("active")
    } else {
        button.classList.add("active");
    }
}

// add event listener to filter missing geo button
const filterGeoButton = document.getElementById("filterMissingGeoButtonId");
filterGeoButton.addEventListener("click", function () {
    var filterValue;
    console.log("Pressed");

    const cookieValue = getSessionCookie("filterMissingGeoOn");
    console.log(typeof cookieValue);
    if(cookieValue == "true") {
        filterValue = false;
    } else {
        filterValue = true;
        // disable other filter
        setSessionCookie("filterFetchStatusOn", false);
    }

    // Toggle filter value
    setSessionCookie("filterMissingGeoOn", filterValue);
    console.log(filterValue);

    const table = document.getElementById("source_feed_status_table");
    const rows = table.getElementsByTagName("tr");
    for (let i = 1; i < rows.length; i++) {
        const cell = rows[i].getElementsByTagName("td")[10]; // select missing geocode colum
        if (cell) {
            if (filterValue && !cell.classList.contains("last_fetch_status_failure")) {
                rows[i].style.display = "none";
            } else {
                rows[i].style.display = "";
            }
        }
    }
});


// add event listener to filter fetch status button
const filterFetchStatusButton = document.getElementById("filterFetchStatusButtonId");
filterFetchStatusButton.addEventListener("click", function () {
    var filterValue;
    console.log("Pressed");

    const cookieValue = getSessionCookie("filterFetchStatusOn");
    console.log(typeof cookieValue);
    if(cookieValue == "true") {
        filterValue = false;
    } else {
        filterValue = true;
        setSessionCookie("filterMissingGeoOn", false);
    }

    // Toggle filter value
    setSessionCookie("filterFetchStatusOn", filterValue);
    console.log(filterValue);

    const table = document.getElementById("source_feed_status_table");
    const rows = table.getElementsByTagName("tr");
    for (let i = 1; i < rows.length; i++) {
        const cell = rows[i].getElementsByTagName("td")[11]; // select fetch status colum
        if (cell) {
            if (filterValue && !cell.classList.contains("last_fetch_status_failure")) {
                rows[i].style.display = "none";
            } else {
                rows[i].style.display = "";
            }
        }
    }
});

// On page load, apply the filter if it was set
window.onload = function() {
    const filterValue = getSessionCookie("filterFetchStatusOn");
    if (filterValue === "true") {
        const table = document.getElementById("source_feed_status_table");
        const rows = table.getElementsByTagName("tr");
        for (let i = 1; i < rows.length; i++) {
            const cell = rows[i].getElementsByTagName("td")[11]; // select fetch status colum
            if (cell) {
                if (filterValue && !cell.classList.contains("last_fetch_status_failure")) {
                    rows[i].style.display = "none";
                } else {
                    rows[i].style.display = "";
                }
            }
        }
    };

    const geoFilterValue = getSessionCookie("filterMissingGeoOn");
    if (geoFilterValue === "true") {
        const table = document.getElementById("source_feed_status_table");
        const rows = table.getElementsByTagName("tr");
        for (let i = 1; i < rows.length; i++) {
            const cell = rows[i].getElementsByTagName("td")[10]; // select missing geocode colum
            if (cell) {
                if (geoFilterValue && !cell.classList.contains("last_fetch_status_failure")) {
                    rows[i].style.display = "none";
                } else {
                    rows[i].style.display = "";
                }
            }
        }
    }
};

// Function to set a session cookie
function setSessionCookie(name, value) {
    document.cookie = `${name}=${value}; Secure; SameSite=Strict; path=/;`;
}

// Function to get a session cookie
function getSessionCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(';').shift();
}