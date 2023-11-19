function toggle(id) {
    let thing = document.getElementById(id)
    if (thing.style.display == "none")
        thing.style.display = ""
    else
        thing.style.display = "none"
}

function flash(before, message) {
    before.insertAdjacentHTML('beforebegin', '<div class="flash">' + message + '</div>');
}
