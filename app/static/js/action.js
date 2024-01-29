console.log("action.js");

const all_btns = document.querySelectorAll(".action-menu");
const all_pages = document.querySelectorAll(".page-action");

all_btns.forEach((btn) => {
  btn.addEventListener("click", () => {
    let index = btn.getAttribute("index");
    all_pages.forEach((page) => {
      let pageIndex = page.getAttribute("index");
      if (index == pageIndex) {
        page.style.display = "block";
      } else {
        page.style.display = "none";
      }
    });
    all_btns.forEach((buttons) => {
      buttons.classList.remove("active");
    });
    btn.classList.add("active");
  });
});

const tag_btns = document.querySelectorAll(".click");
const all_frame = document.querySelectorAll(".frame");

tag_btns.forEach((btn) => {
  btn.addEventListener("click", () => {
    let index = btn.getAttribute("index");
    all_frame.forEach((page) => {
      let pageIndex = page.getAttribute("index");
      if (index == pageIndex) {
        page.style.display = "block";
      } else {
        page.style.display = "none";
      }
    });
    tag_btns.forEach((buttons) => {
      buttons.classList.remove("active");
    });
    btn.classList.add("active");
  });
});

const btn_display = document.querySelectorAll(".btn-display");
const display_box = document.querySelectorAll(".empdisplay");

btn_display.forEach((btn) => {
  btn.addEventListener("click", () => {
    let btnIndex = btn.getAttribute("index");
    console.log(btnIndex);
    display_box.forEach((box) => {
      let boxIndex = box.getAttribute("index");
      if (btnIndex == boxIndex) {
        box.style.display = "flex";
      } else {
        box.style.display = "none";
      }
    });
    btn_display.forEach((display) => {
      display.classList.remove("active");
    });
    btn.classList.add("active");
  });
});