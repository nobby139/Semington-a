async function fetchFixturesFromNeon(season) {
  const status = document.getElementById("status");
  const tbody = document.getElementById("tableBody");
  
  if (!status || !tbody) return;

  status.textContent = "Loading fixtures from database...";

  try {
    const response = await fetch(`/api/fixtures?season=${season}`);
    if (!response.ok) throw new Error('API fetch failed');
    
    const rows = await response.json();

    if (rows.length === 0) {
      tbody.innerHTML = `<tr><td colspan="7">No fixtures found for season ${season}.</td></tr>`;
      status.textContent = "";
      return;
    }

    tbody.innerHTML = rows.map(r => {
      // Format date nicely
      const matchDate = new Date(r.match_date).toLocaleDateString("en-GB", {
        day: "2-digit",
        month: "short",
        year: "2-digit"
      });

      const pointsDisplay = (r.home_points !== null && r.away_points !== null)
        ? `${r.home_points} - ${r.away_points}`
        : '';

      return `
        <tr>
          <td>${matchDate}</td>
          <td>${r.day || ''}</td>
          <td>${r.home_team} vs ${r.away_team}</td>
          <td>${pointsDisplay}</td>
          <td>${r.venue || ''}</td>
          <td>${r.alley || ''}</td>
          <td>${r.competition || ''}</td>
        </tr>
      `;
    }).join("");

    status.textContent = `Showing ${rows.length} matches for season ${season}.`;
  } catch (err) {
    status.style.color = "red";
    status.textContent = "Error loading data: " + err.message;
  }
}

function filterBySeason() {
  const seasonSelect = document.getElementById("seasonSelect");
  if (!seasonSelect) return;
  const selectedSeason = seasonSelect.value;
  fetchFixturesFromNeon(selectedSeason);
}

// Automatically load default selected season when page loads
document.addEventListener("DOMContentLoaded", () => {
  filterBySeason();
});