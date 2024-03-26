console.log("chart.js");

var myData, total_present, kkl_employee, dr_employee, ft_employee;
fetch("/get_chart")
  .then((response) => response.json())
  .then((data) => {
    console.log(data);
    myData = data;
    processData(myData);
  })
  .catch((error) => console.error("Error fetching data:", error));

function processData(data) {
  total_present = (data.total_present).length;
  kkl_employee = (data.kkl_employee).length;
  dr_employee = (data.dr_employee).length;
  ft_employee = (data.ft_employee).length;

  console.log(data);

  let table = document.querySelector('.analysis-table');
  data.total_present.forEach((data)=>{
    table.innerHTML += ` <tr>
                            <td>${data.emp_id}</td>
                            <td>${data.name}</td>
                            <td>${data.branch}</td>
                          </tr> `;
  })

  let totalData = [
    { label: "KKL Present", value: kkl_employee },
    { label: "DR Present", value: dr_employee },
    { label: "FT Present", value: ft_employee },
  ];

  let ctx = document.getElementById("myPieChart").getContext("2d");
  let myPieChart; // Declare myPieChart in the global scope

  function employeeDisplay(title, employee) {
    let all_data = document.querySelector(".details");
    all_data.innerHTML = "";
    all_data.innerHTML = `
    <li class="detail title">
        <span class="detail_title"><span class="tota">${title}</span></span>
    </li>
    <li class="detail">
        <span><span class="tota">Total Employees ${total_present}</span></span>
    </li>
    `;
    employee.forEach((data) => {
      let li = document.createElement("li");
      li.className = "detail";
      li.innerHTML = ` <span class="detail_title">${data.label} : <span class="tota">${data.value}</span></span>`;
      all_data.appendChild(li);
    });

    // Destroy existing chart if it exists
    if (myPieChart) {
      myPieChart.destroy();
    }

    myPieChart = new Chart(ctx, {
      type: "pie",
      data: {
        labels: employee.map((emp) => emp.label),
        datasets: [
          {
            label: "Employee Distribution",
            data: employee.map((emp) => emp.value),
            backgroundColor: [
              "rgb(255, 99, 132)",
              "rgb(54, 162, 235)",
              "rgb(255, 205, 86)",
            ],
            hoverOffset: 4,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
      },
    });
  }

  employeeDisplay("today employee", totalData);



  document
    .querySelector(".downloadImage")
    .addEventListener("click", function () {
      // Select the chart container element
      const chartContainer = document.querySelector(".chart_container");
      let fileName = document
        .querySelector(".chart_container .details .title")
        .textContent.trim();
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
}
