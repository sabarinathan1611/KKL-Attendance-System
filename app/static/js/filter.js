console.log("filter.js");
const all_rows = document.querySelectorAll(".today-attendance-table tbody tr");
const all_shiftDisplay = document.querySelectorAll(".currentShift");

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
function sendAlert(id) {
  console.log("ID: ", id);

  // Create an object with the ID
  const data = { id: id };

  fetch("/send_message", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(data),
  })
    .then((response) => response.json())
    .then((data) => {
      console.log(data                                                                                                           );
      let cancel=document.querySelector(`.cancel-${id}`);
      cancel.disabled='true';
      cancel.style.cursor='not-allowed';
    });
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

function getCurrentShift() {
  const currentTime = new Date();
  const currentHour = currentTime.getHours();

  if (currentHour >= 6 && currentHour < 14) {
    return "8a";
  } else if (currentHour >= 14 && currentHour < 22) {
    return "8b";
  } else if (currentHour >= 22 && currentHour < 6) {
    return "8c";
  } else {
    return "8a";
  }
}

const currentShift = getCurrentShift();
filter(currentShift);

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
            <button type="button" onclick="sendAlert(${id})"  class="table-btn cancel cancel-${id}">Cancel</button>
            <button type="button" class="table-btn continue">Continue</button>
        </form>
      `;
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

let alertSent = false;
let elapsedMinutes = 0; // Declare elapsedMinutes outside the functions

function getCurrentShiftInfo(currentTime) {
  const [currentHours, currentMinutes] = currentTime.split(":").map(Number);

  for (const shift of shiftDetails) {
    const shiftIntime = shift.shiftIntime.split(":").map(Number);
    const shiftOuttime = shift.shiftOuttime.split(":").map(Number);

    if (
      (currentHours > shiftIntime[0] ||
        (currentHours === shiftIntime[0] &&
          currentMinutes >= shiftIntime[1])) &&
      (currentHours < shiftOuttime[0] ||
        (currentHours === shiftOuttime[0] && currentMinutes < shiftOuttime[1]))
    ) {
      const remainingMinutes =
        shiftOuttime[0] * 60 +
        shiftOuttime[1] -
        (currentHours * 60 + currentMinutes);
      const shiftStartTime = `${shiftIntime[0]}:${shiftIntime[1]}`;

      return {
        currentShift: shift.shiftName,
        timeRemaining: remainingMinutes,
        shiftStartTime: shiftStartTime,
        totalShiftTime: shiftOuttime[0] * 60 + shiftOuttime[1],
      };
    }
  }

  return {
    currentShift: "No shift found",
    timeRemaining: 0,
    shiftStartTime: "N/A",
    totalShiftTime: 0,
  };
}

function convertMinutesToHoursAndMinutes(minutes) {
  const hours = Math.floor(minutes / 60);
  const remainingMinutes = minutes % 60;
  return { hours, minutes: remainingMinutes };
}

function getTimeSinceShiftStarted(shiftStartTime, currentTime) {
  const [startHours, startMinutes] = shiftStartTime.split(":").map(Number);
  const [currentHours, currentMinutes] = currentTime.split(":").map(Number);

  const startTotalMinutes = startHours * 60 + startMinutes;
  const currentTotalMinutes = currentHours * 60 + currentMinutes;

  return currentTotalMinutes - startTotalMinutes;
}

function calculatePercentage(timeTaken, totalShiftTime) {
  return (timeTaken / totalShiftTime) * 100;
}

function calculateShiftProgress(elapsedMinutes, totalShiftTime) {
  const progressPercentage = (elapsedMinutes / totalShiftTime) * 100;
  return progressPercentage.toFixed(2);
}

function calculateCompletionPercentage(elapsedMinutes, totalShiftTime) {
  const completionPercentage = calculatePercentage(
    elapsedMinutes,
    totalShiftTime
  );
  console.log(`Percentage of Completion: ${completionPercentage.toFixed(2)}%`);
}

function sendAlertMsg(currentShift, lastShift) {
  if (!alertSent) {
    // console.log(currentShift,lastShift);

    fetch(
      `/send_message_data?current_shift=${currentShift}&last_shift=${lastShift}`,
      {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
        },
      }
    )
      .then((response) => response.json())
      .then((data) => {
        console.log(data);
      });
  }
}

function logElapsedTime() {
  const currentTime = new Date();
  const currentHours = currentTime.getHours();
  const currentMinutes = currentTime.getMinutes();
  const formattedCurrentTime = `${currentHours}:${currentMinutes}`;

  const shiftInfo = getCurrentShiftInfo(formattedCurrentTime);
  // Calculate time elapsed since the shift started
  if (shiftInfo.currentShift !== "No shift found") {
    elapsedMinutes = getTimeSinceShiftStarted(
      shiftInfo.shiftStartTime,
      formattedCurrentTime
    );
    const elapsedHoursAndMinutes =
      convertMinutesToHoursAndMinutes(elapsedMinutes);
    //   console.log(`Time Elapsed Since Shift Started: ${elapsedHoursAndMinutes.hours} hours ${elapsedHoursAndMinutes.minutes} minutes`);

    // Log the "Time Remaining for Next Shift" message
    //   console.log(`Time Remaining for Next Shift: ${convertMinutesToHoursAndMinutes(shiftInfo.timeRemaining).hours} hours ${convertMinutesToHoursAndMinutes(shiftInfo.timeRemaining).minutes} minutes`);
    let lastShift;
    if (shiftInfo.currentShift === "8A") {
      lastShift = "8C";
    } else if (shiftInfo.currentShift === "8B") {
      lastShift = "8A";
    } else if (shiftInfo.currentShift === "8C") {
      lastShift = "8B";
    } else {
      console.log("shift not found");
    }
    let current_last_shift = [shiftInfo.currentShift, lastShift];
    // console.log(current_last_shift);
    return current_last_shift;
  } else {
    console.log("No shift found. Unable to calculate elapsed time.");
  }
}

function checkElapsedTime() {
  let current_last_shift = logElapsedTime();

  // Check if 17 minutes have elapsed and alert has not been sent
  if (elapsedMinutes >= 10 && !alertSent) {
    console.log("Alert: 10 minutes have elapsed since the shift started!");
    if (!alertSent) {
      sendAlertMsg(current_last_shift[0], current_last_shift[1]);
    } // Set flag to true to indicate that the alert has been sent
    alertSent = true;
  }
}

setInterval(checkElapsedTime, 1000); // Check every 1000 milliseconds (1 second)
setInterval(logElapsedTime, 10000); // Log every 10 seconds
