function toggleMenu() {
    let menu = document.getElementById("profileMenu");
    if (menu.classList.contains("show")) {
        menu.classList.remove("show");
    } else {
        menu.classList.add("show");
        document.addEventListener('click', closeMenuOnClickOutside, {once: true});
    }
}

function closeMenuOnClickOutside(event) {
    let menu = document.getElementById("profileMenu");
    if (!menu.contains(event.target) && !event.target.matches('.profile-icon')) {
        menu.classList.remove("show");
    } else {
        document.addEventListener('click', closeMenuOnClickOutside, {once: true});
    }
}


document.getElementById("logoutLink").addEventListener("click", function (event) {
    event.preventDefault();
    fetch('/logout/', {
        method: 'POST',
    })
        .then(response => response.json())
        .then(data => {
            console.log(data.message);
            window.location.href = "/signIn/";
        })
        .catch(error => console.error('Error:', error));
});