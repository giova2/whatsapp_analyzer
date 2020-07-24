document.addEventListener("DOMContentLoaded", function (event) {
  console.log("DOM fully loaded and parsed");
  let $help = document.querySelector(".help");
  $help.addEventListener("click", (e) => {
    e.preventDefault();
    let holapepe = $help.classList.contains("open");
    if (holapepe) {
      $("#multiCollapseExample1").collapse("hide");
      setTimeout(() => {
        $help.classList.remove("open");
      }, 500);
    } else {
      $help.classList.add("open");
      setTimeout(() => {
        $("#multiCollapseExample1").collapse("show");
      }, 300);
    }
  });
});
