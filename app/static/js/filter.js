console.log("filter.js");
const all_rows = document.querySelectorAll(".today-attendance-table tbody tr");
const all_shiftDisplay = document.querySelectorAll(".currentShift");

const employe_rows = document.querySelectorAll(".employee-table tbody tr");

let shiftSelect = document.getElementById("shift");

shiftSelect.addEventListener("change", () => {
  let shift = shiftSelect.value;
  if (shift == "" || shift.lenght <= 0) {
    let currentShift = getCurrentShift();
    filter(currentShift);
  } else {
    filter(shift.toLowerCase());
  }
});
function sendAlert(id,action) {
  console.log("ID: ", id);

  // Create an object with the ID
  const data = { id: id };
  let route='';
  if (action === 'cancel') { route = '/send_message' }
  else if (action === 'continue') { route = '/send_continue_message' }
  let cancel = document.querySelector(`.cancel-${id}`);
  let continueBtn = document.querySelector(`.continue-${id}`);
  
  cancel.disabled='true';
  cancel.style.cursor = 'not-allowed';
  continueBtn.disabled='true';
  continueBtn.style.cursor = 'not-allowed';

  fetch(route, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(data),
  })
    .then((response) => response.json())
    .then((data) => {
      console.log(data);
      cancel.disabled='false';
      cancel.style.cursor = 'pointer';
      continueBtn.disabled='false';
      continueBtn.style.cursor = 'pointer';
      window.location.href = "";
    });
}

function CancelOt(id) {
  let cancel = document.querySelector(`.cancel-${id}`);
  let continueBtn = document.querySelector(`.continue-${id}`);
  
  cancel.disabled='false';
  cancel.style.cursor = 'pointer';
  continueBtn.disabled='false';
  continueBtn.style.cursor = 'pointer';
}

function filter(currentShift) {
  all_rows.forEach((row) => {
    if (currentShift == row.getAttribute("data-shift").toLowerCase()) {
      row.style.display = "";
    } else {
      row.style.display = "none";
    }
  });

  all_shiftDisplay.forEach((display) => {
    display.children[0].innerHTML = currentShift.toUpperCase();
  });
}

employe_rows.forEach((row) => {
  let status = row.querySelector(".status");
  if (status.innerHTML.trim().toLowerCase() == "freezed") {
    row.classList.add("freezed");
    status.innerHTML = `<div class="inner-tag">Freezed</div>`;
  } else {
    row.classList.remove("freezed");
    status.innerHTML = `<div class="tag">Active</div>`;
  }
});
// function getCurrentShift() {
//   const currentTime = new Date();
//   const currentHour = currentTime.getHours();

//   if (currentHour >= 6 && currentHour < 14) {
//     return "8a";
//   } else if (currentHour >= 14 && currentHour < 22) {
//     return "8b";
//   } else if (currentHour >= 22 && currentHour < 6) {
//     return "8c";
//   } else {
//     return "8a";
//   }
// }

// const currentShift = getCurrentShift();
// filter(currentShift);

all_rows.forEach((row) => {
  let id = row.querySelector(".id").innerHTML;
  let intime = row.querySelector(".intime");
  let outtime = row.querySelector(".outtime");
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
        <form class="btns-container">
            <input type="hidden" name="empid" value="${id}">
            <button type="button" onclick="sendAlert(${id},'cancel')"  class="table-btn cancel cancel-${id}">Cancel</button>
            <button type="button" onclick="sendAlert(${id},'continue')" class="table-btn continue continue-${id}">Continue</button>
        </form>
      `;
    console.log(row.querySelector('.status').innerHTML);
    if (row.querySelector('.status').textContent.trim().toLowerCase() == `ot`) {
      row.querySelector(".action").innerHTML = `
        <form class="btns-container">
            <input type="hidden" name="empid" value="${id}">
            <button type="button" onclick="CancelOt(${id})" class="table-btn cancel-ot cancel-ot-${id}">Cancel OT</button>
        </form>
      `;
    }
  } else {
    row.classList.remove("mis-pinch");
  }
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
  let lastShift;
  if (shift.shiftName === '8A') { lastShift = '8C' }
  else if(shift.shiftName==='8B'){lastShift='8A'}
  else if (shift.shiftName === '8C') { lastShift = '8B' }
  console.log(lastShift);
  if (currentTime === shift.shiftChecktime) {
  // if (1==1) {
    if (canRefresh) {
      fetch(`/send_message_data?currentShift=${shift.shiftName}&lastShift=${lastShift}`, {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
        },
      })
        .then((response) => response.json())
        .then((data) => {
          console.log(data);
        });

      // Disable refresh for 2 seconds
      canRefresh = false;
      setTimeout(() => {
        canRefresh = true;
      }, 2000);
    }
  }
}, 1000);