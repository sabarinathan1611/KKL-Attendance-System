console.log("filter.js");
const all_rows = document.querySelectorAll(".today-attendance-table tbody tr");
const all_shiftDisplay = document.querySelectorAll(".currentShift");

let shiftSelect = document.getElementById("shift");

shiftSelect.addEventListener("change",()=>{
    let shift = shiftSelect.value;
    if (shift == "" || shift.lenght <= 0) {
        let currentShift = getCurrentShift();
        filter(currentShift)
    }else{
        filter(shift.toLowerCase());
    }
    

})

function filter(currentShift){
    all_rows.forEach(row => {

        if ((currentShift) == (row.getAttribute("data-shift").toLowerCase())) {
            row.style.display = "";
        }else{
            row.style.display = "none";
        }
    });

    all_shiftDisplay.forEach(display => {
        display.children[0].innerHTML = currentShift.toUpperCase();
    });
}

function getCurrentShift() {
    const currentTime = new Date();
    const currentHour = currentTime.getHours();

    if (currentHour >= 6 && currentHour < 14) {
        return '8a';
    } else if (currentHour >= 14 && currentHour < 22) {
        return '8b';
    } else if (currentHour >= 22 && currentHour < 6){
        return '8c';
    }else{
        return '8a'; 
    }
}

const currentShift = getCurrentShift();
filter(currentShift);

all_rows.forEach(row => {
    let id = row.querySelector(".id").innerHTML;
    let intime = (row.querySelector(".intime"));
    let outtime = (row.querySelector(".outtime"));
    if ((intime && (intime.innerHTML == "-" || intime.innerHTML =="")) || (outtime && (outtime.innerHTML == "-" || outtime.innerHTML ==""))) {
      row.classList.add("mis-pinch");
      if (intime.innerHTML == "-") {
        intime.innerHTML = `<div class="table-tag">Punch in</div>`;
      }else{
        outtime.innerHTML = `<div class="table-tag">Punch out</div>`;
      }

      row.querySelector(".action").innerHTML = (`
        <form class="btns-container">
            <input type="hidden" name="empid" value="${id}">
            <button type="button" class="table-btn cancel">Cancel</button>
            <button type="button" class="table-btn continue">Continue</button>
        </form>
      `)

    }else{
      row.classList.remove("mis-pinch");
    }
  
  });