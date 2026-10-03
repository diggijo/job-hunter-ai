const searchInput = document.getElementById("job-search");
const locationFilter = document.getElementById("location-filter");
const sortJobs = document.getElementById("sort-jobs");
const jobList = document.querySelector(".job-list");
const jobCards = document.querySelectorAll(".job-card");
const originalJobCards = Array.from(jobCards);
const jobCount = document.getElementById("job-count");

function filterJobs() {
    const searchTerm = searchInput.value.toLowerCase();
    const selectedLocation = locationFilter.value.toLowerCase();

    let visibleCount = 0;

    jobCards.forEach(function (card) {
        const cardText = card.textContent.toLowerCase();

        const matchesSearch = cardText.includes(searchTerm);
        const matchesLocation = cardText.includes(selectedLocation);

        if (matchesSearch && matchesLocation) {
            card.style.display = "";
            visibleCount++;
        } else {
            card.style.display = "none";
        }
    });

    jobCount.textContent = visibleCount;
}

function sortJobCards() {
    const sortBy = sortJobs.value;

    let cards = Array.from(jobCards);

    if (sortBy === "default") {
        cards = Array.from(originalJobCards);
    }
    
    if (sortBy === "title") {
    cards.sort(function (a, b) {
        const titleA = a.querySelector("h2").textContent.trim();
        const titleB = b.querySelector("h2").textContent.trim();

        return titleA.localeCompare(titleB, undefined, {
            numeric: true,
            sensitivity: "base"
        });
    });
}

    if (sortBy === "company") {
    cards.sort(function (a, b) {
        const companyA = a.querySelector(".company").textContent.trim();
        const companyB = b.querySelector(".company").textContent.trim();

        return companyA.localeCompare(companyB, undefined, {
            numeric: true,
            sensitivity: "base"
        });
    });
}

    cards.forEach(function (card) {
        jobList.appendChild(card);
    });
}

searchInput.addEventListener("input", filterJobs);
locationFilter.addEventListener("change", filterJobs);
sortJobs.addEventListener("change", sortJobCards);