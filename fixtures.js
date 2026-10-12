// Replace with your exact connection host and connection string from Neon
const NEON_HOST = "ep-patient-cloud-21452490.eu-central-1.aws.neon.tech"; 
const NEON_API_KEY = "YOUR_NEON_CONNECTION_STRING_HERE";

async function fetchFixturesFromNeon(season) {
  const status = document.getElementById("status");
  const tbody = document.getElementById("tableBody");
  
  if (!status || !tbody) return;

  // Split season dropdown value (e.g., "2025-2026")
  const [startYear, endYear] = season.split("-");
  const startDate = `${startYear}-08-01`;
  const endDate = `${endYear}-05-31`;

  status.textContent = "Loading fixtures from database...";

  try {
    const response = await fetch(`https://${NEON_HOST}/sql`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${NEON_API_KEY}`
      },
      body: JSON.stringify({
        query: `
          SELECT * FROM fixtures 
          WHERE match_date >= $1 AND match_date <= $2 
          ORDER BY match_date ASC
        `,
        params: [startDate, endDate]
      })
    });

    const data = await response.json();
    const rows = data.rows || [];

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
  const selectedSeason = document.getElementById("seasonSelect").value;
  fetchFixturesFromNeon(selectedSeason);
}

// Automatically load default selected season when page loads
document.addEventListener("DOMContentLoaded", () => {
  filterBySeason();
});
