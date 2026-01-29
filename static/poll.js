/**
 * Polling script for GitHub webhook events.
 * Polls the backend API every 15 seconds and displays new events.
 */

// Store the last seen timestamp to avoid duplicate entries
let lastSeenTimestamp = "";

// Polling interval in milliseconds (15 seconds)
const POLL_INTERVAL = 15000;

/**
 * Format timestamp for display.
 * Converts ISO 8601 UTC timestamp to readable format.
 *
 * @param {string} timestamp - ISO 8601 formatted timestamp string
 * @returns {string} Formatted date string
 */
function formatTimestamp(timestamp) {
  try {
    const date = new Date(timestamp);

    // Format: "1st April 2021 - 9:30 PM UTC"
    const day = date.getUTCDate();
    const daySuffix = getDaySuffix(day);
    const monthNames = [
      "January",
      "February",
      "March",
      "April",
      "May",
      "June",
      "July",
      "August",
      "September",
      "October",
      "November",
      "December",
    ];
    const month = monthNames[date.getUTCMonth()];
    const year = date.getUTCFullYear();

    // Format time
    let hours = date.getUTCHours();
    const minutes = date.getUTCMinutes();
    const ampm = hours >= 12 ? "PM" : "AM";
    hours = hours % 12;
    hours = hours ? hours : 12; // 0 should be 12
    const minutesStr = minutes < 10 ? "0" + minutes : minutes;

    return `${day}${daySuffix} ${month} ${year} - ${hours}:${minutesStr} ${ampm} UTC`;
  } catch (e) {
    console.error("Error formatting timestamp:", e);
    return timestamp;
  }
}

/**
 * Get day suffix (st, nd, rd, th).
 *
 * @param {number} day - Day of month
 * @returns {string} Suffix string
 */
function getDaySuffix(day) {
  if (day > 3 && day < 21) return "th";
  switch (day % 10) {
    case 1:
      return "st";
    case 2:
      return "nd";
    case 3:
      return "rd";
    default:
      return "th";
  }
}

/**
 * Format event message based on action type.
 *
 * @param {Object} event - Event object from API
 * @returns {string} Formatted event message
 */
function formatEventMessage(event) {
  const author = event.author || "Unknown";
  const timestamp = formatTimestamp(event.timestamp);

  switch (event.action) {
    case "PUSH":
      return `"${author}" pushed to "${event.to_branch}" on ${timestamp}`;

    case "PULL_REQUEST":
      return `"${author}" submitted a pull request from "${event.from_branch}" to "${event.to_branch}" on ${timestamp}`;

    case "MERGE":
      return `"${author}" merged branch "${event.from_branch}" to "${event.to_branch}" on ${timestamp}`;

    default:
      return `"${author}" performed ${event.action} on ${timestamp}`;
  }
}

/**
 * Get CSS class for event type.
 *
 * @param {string} action - Action type
 * @returns {string} CSS class name
 */
function getEventClass(action) {
  const actionLower = action.toLowerCase();
  if (actionLower === "push") return "push";
  if (actionLower === "pull_request") return "pull_request";
  if (actionLower === "merge") return "merge";
  return "";
}

/**
 * Create HTML element for an event.
 *
 * @param {Object} event - Event object
 * @returns {HTMLElement} Event element
 */
function createEventElement(event) {
  const eventDiv = document.createElement("div");
  eventDiv.className = `event-item ${getEventClass(event.action)}`;

  const eventText = document.createElement("div");
  eventText.className = "event-text";
  eventText.textContent = formatEventMessage(event);

  const eventMeta = document.createElement("div");
  eventMeta.className = "event-meta";
  eventMeta.textContent = `Action: ${event.action} | Request ID: ${event.request_id}`;

  eventDiv.appendChild(eventText);
  eventDiv.appendChild(eventMeta);

  return eventDiv;
}

/**
 * Fetch events from the backend API.
 *
 * @returns {Promise<Array>} Array of event objects
 */
async function fetchEvents() {
  try {
    const url = lastSeenTimestamp
      ? `/webhook/events?since=${encodeURIComponent(lastSeenTimestamp)}`
      : "/webhook/events";

    const response = await fetch(url);

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const events = await response.json();
    return Array.isArray(events) ? events : [];
  } catch (error) {
    console.error("Error fetching events:", error);
    return [];
  }
}

/**
 * Update the UI with new events.
 *
 * @param {Array} events - Array of new event objects
 */
function updateUI(events) {
  const container = document.getElementById("eventsContainer");

  // Remove empty state if it exists
  const emptyState = container.querySelector(".empty-state");
  if (emptyState && events.length > 0) {
    emptyState.remove();
  }

  // Add new events to the top of the container
  events.forEach((event) => {
    const eventElement = createEventElement(event);
    container.insertBefore(eventElement, container.firstChild);
  });

  // Update last seen timestamp if we have events
  if (events.length > 0) {
    // Use the latest timestamp (events are sorted ascending)
    const latestEvent = events[events.length - 1];
    lastSeenTimestamp = latestEvent.timestamp;
  }

  // Update last update time
  const lastUpdateEl = document.getElementById("lastUpdate");
  if (lastUpdateEl) {
    const now = new Date();
    lastUpdateEl.textContent = `Last update: ${now.toLocaleTimeString()}`;
  }
}

/**
 * Poll for new events.
 */
async function pollEvents() {
  const events = await fetchEvents();

  if (events.length > 0) {
    updateUI(events);
  }
}

/**
 * Initialize polling.
 */
function initPolling() {
  // Initial fetch
  pollEvents();

  // Set up interval polling every 15 seconds
  setInterval(pollEvents, POLL_INTERVAL);
}

// Start polling when page loads
document.addEventListener("DOMContentLoaded", initPolling);
