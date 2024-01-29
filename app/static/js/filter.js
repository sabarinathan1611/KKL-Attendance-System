console.log("filter.js");
const all_rows = document.querySelectorAll(".today-attendance-table tbody tr");
const all_shiftDisplay = document.querySelectorAll(".currentShift");

let shiftSelect = document.getElementById("shift");

shiftSelect.addEventListener("change", () => {
  let shift = shiftSelect.value;
  if (shift == "" || shift.lenght <= 0) {
    filter(currentShift.shiftName.toLowerCase());
  } else {
    filter(shift.toLowerCase());
  }
});

function filter(currentShift) {
  all_rows.forEach((row) => {
    if (
      currentShift.toUpperCase() == row.getAttribute("data-shift").toUpperCase()
    ) {
      row.style.display = "";
    } else {
      row.style.display = "none";
    }
  });

  all_shiftDisplay.forEach((display) => {
    display.children[0].innerHTML = `<span class="tag">${currentShift.toUpperCase()}</span>`;
  });
}

all_rows.forEach((row) => {
  let intime = row.querySelector(".intime");
  let outtime = row.querySelector(".outtime");
  let status = row.querySelector(".status");
  if (
    (intime && (intime.innerHTML == "-" || intime.innerHTML == "")) ||
    (outtime && (outtime.innerHTML == "-" || outtime.innerHTML == ""))
  ) {
    row.classList.add("mis-pinch");
    if (intime.innerHTML == "-") {
      intime.innerHTML = `<div class="table-tag">Punch in</div>`;
    } else {
      outtime.innerHTML = `<div class="table-tag">Punch out</div>`;
    }

    row.querySelector(".action").innerHTML = `
        <div class="btns-container">
            <button type="button" class="table-btn cancel">Cancel</button>
            <button type="button" class="table-btn continue">Continue</button>
        </div>
      `;
  } else {
    row.classList.remove("mis-pinch");
  }

  if (status.textContent.toLowerCase().trim() == "wrong shift") {
    status.innerHTML = `<p class="table-tag">Wrong Shift</p>`;
    row.classList.add("wrongShift");
    row.querySelector(".action").innerHTML = `
        <div class="btns-container">
            <input type="hidden" name="type" id="type" value="wrongShift">
            <button type="button" class="table-btn cancel">Cancel</button>
            <button type="button" class="table-btn continue">Continue</button>
        </div>
      `;
  } else if (status.textContent.toLowerCase().trim() == "ot") {
    status.innerHTML = `<p class="table-tag">OT</p>`;
    row.classList.add("overTime");
  } else {
    row.classList.remove("wrongShift");
    row.classList.remove("overTime");
  }

  console.log(status.textContent.trim());
});

let shiftDetails = [
  {
    shiftName: "8A",
    shiftIntime: "06:00",
    shiftOuttime: "14:00",
  },
  {
    shiftName: "8B",
    shiftIntime: "14:00",
    shiftOuttime: "22:00",
  },
  {
    shiftName: "8C",
    shiftIntime: "22:00",
    shiftOuttime: "06:00",
  },
];

// Function to add 5 minutes to a given time
function addMinutes(time, minutes) {
  const [hours, mins] = time.split(":").map(Number);
  const newTime = new Date(2022, 0, 1, hours, mins + minutes);
  return newTime.toLocaleTimeString("en-US", { hour12: false });
}

// Iterate through shiftDetails and add 5 minutes to shiftIntime
shiftDetails.forEach((shift) => {
  shift.shiftChecktime = addMinutes(shift.shiftIntime, 5);
});

function getCurrentShift(currentTime, shiftDetails) {
  for (const shift of shiftDetails) {
    const shiftIntime = shift.shiftIntime;
    const shiftOuttime = shift.shiftOuttime;

    if (
      (shiftIntime <= shiftOuttime &&
        currentTime >= shiftIntime &&
        currentTime < shiftOuttime) ||
      (shiftIntime > shiftOuttime &&
        (currentTime >= shiftIntime || currentTime < shiftOuttime))
    ) {
      return shift;
    }
  }

  return null; // No shift found for the current time
}

// Provide the current time as a string in 24-hour format
// Function to get the current time in 24-hour format
function getCurrentTime24Hrs() {
  const currentTime = new Date();
  const hours = currentTime.getHours();
  const minutes = currentTime.getMinutes();
  const seconds = currentTime.getSeconds();

  // Format the time to ensure two digits for hours, minutes, and seconds
  const formattedTime = `${String(hours).padStart(2, "0")}:${String(
    minutes
  ).padStart(2, "0")}:${String(seconds).padStart(2, "0")}`;

  return formattedTime;
}

// Get the current time in 24-hour format
const currentTime24Hrs = getCurrentTime24Hrs();

// Parse the current time as a string
const currentTimeString = "01:59:00";

// Compare the current time with the provided time string
if (currentTime24Hrs === currentTimeString) {
  console.log("The current time matches the provided time string.");
} else {
  console.log("The current time does not match the provided time string.");
}

// Find the current shift
const currentShift = getCurrentShift(currentTime24Hrs, shiftDetails);

// Display the current shift
if (currentShift) {
  console.log(`Current shift: ${currentShift.shiftName}`);
} else {
  console.log("No shift currently");
}

filter(currentShift.shiftName);

let canRefresh = true;

window.addEventListener("beforeunload", (event) => {
  if (!canRefresh) {
    // Display a confirmation dialog
    const message = "You are about to leave the page. Are you sure?";
    event.returnValue = message;
    return message;
  }
});

setInterval(() => {
  let currentTime = getCurrentTime24Hrs();
  let shift = getCurrentShift(currentTime, shiftDetails);

  if (currentTime == shift.shiftIntime) {
    filter(shift.shiftName);
  }

  if (currentTime === shift.shiftChecktime) {
    if (canRefresh) {
      console.log("message call");

      // Disable refresh for 2 seconds
      canRefresh = false;
      setTimeout(() => {
        canRefresh = true;
      }, 2000);
    }
  }
}, 1000);
