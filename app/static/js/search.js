let fromDate = document.getElementById("startDate");
let toDate = document.getElementById("endDate");

let okBtn = document.querySelector(".okBtn");

okBtn.addEventListener("click", () => {
  if (
    (fromDate.value.length > 0 && toDate.value.length > 0) ||
    (fromDate.value.length <= 0 && toDate.value.length <= 0)
  ) {
    let emp_id = document.getElementById('empsearch').value;
  let startDate = document.getElementById('startDate').value;
  let endDate = document.getElementById('endDate').value;
  let data = {
    emp_id: emp_id,
    startDate: startDate,
    endDate: endDate
  }
  let displayPage = document.querySelector('.card_display');
  fetch('/searchEmployee', {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(data),
  })
  .then((response) => response.json()) // Adjust if the response is JSON
  .then((data) => {
    
    displayPage.innerHTML =`<div class="serac_card">
    <div class="emp_profile">
      <img src="../static/img/${data.gender}.jpeg" alt="emp image" />
    </div>
    <ul class="emp_details">
    <div class="half">
    <li class="empDetail line">
      Emp ID : <span>${data.emp_id}</span>
    </li>
    <li class="empDetail line">
      Emp Name : <span>${data.name}</span>
    </li>
    <li class="empDetail line">
      No Of Present : <span>${data.present}</span>
    </li>
    <li class="empDetail line">
      No Of Absent : <span>${data.absent}</span>
    </li>
    <li class="empDetail line">
      No Of Wrong shift : <span>${data.wrongShift}</span>
    </li>
    <li class="empDetail line">
      No Of Half day : <span>${data.halfDay}</span>
    </li>
  </div>
  <div class="half">
    <li class="empDetail line">
      No Of Week Off : <span>${data.weekOff}</span>
    </li>
    <li class="empDetail line">
      No Of Week Off Present : <span>${data.wop}</span>
    </li>
    <li class="empDetail line">
      No Of Leave : <span>${data.leave}</span>
    </li>
    <li class="empDetail line">
      No Of Call duty : <span>${data.callDuty}</span>
    </li>
    <li class="empDetail line">
      No Of Holiday : <span>${data.holiday}</span>
    </li>
    <li class="empDetail line">
      No Of Holiday Present : <span>${data.hp}</span>
    </li>
    <li class="empDetail line">
      No Of Rest: <span>${data.rest}</span>
    </li>
  </div>
  </ul>
  </div>`
    
  });
  } else {
    alert("fill two date fields");
  }
});

let submitBtn = document.querySelector('.okBtn');
submitBtn.addEventListener('click', () => {
  
})

document
  .querySelector(".donwload_search")
  .addEventListener("click", function () {
    // Select the chart container element
    const chartContainer = document.querySelector(".searchEmployeeSection");
    let fileName = "Employee Detail";
    // Use html2canvas to capture the content of the chart container
    html2canvas(chartContainer).then((canvas) => {
      // Convert the canvas to a data URL
      const dataURL = canvas.toDataURL();

      // Create a temporary link element
      const link = document.createElement("a");
      link.href = dataURL;
      link.download = `${fileName}.png`; // Set the download filename

      // Append the link to the document and trigger a click event to download the image
      document.body.appendChild(link);
      link.click();

      // Remove the temporary link from the document
      document.body.removeChild(link);
    });
  });
