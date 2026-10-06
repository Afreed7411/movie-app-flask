// Auto-dismiss flash messages
document.querySelectorAll(".flash").forEach(function (el) {
  setTimeout(function () { el.style.display = "none"; }, 4000);
});

// Live title filter on the movies page
var live = document.getElementById("live-search");
if (live) {
  live.addEventListener("input", function () {
    var term = live.value.trim().toLowerCase();
    document.querySelectorAll("#movie-grid .card").forEach(function (card) {
      card.style.display = card.dataset.title.indexOf(term) !== -1 ? "" : "none";
    });
  });
}

// Password confirmation on register form
var form = document.getElementById("register-form");
if (form) {
  form.addEventListener("submit", function (e) {
    if (document.getElementById("password").value !== document.getElementById("confirm").value) {
      e.preventDefault();
      alert("Passwords do not match.");
    }
  });
}
