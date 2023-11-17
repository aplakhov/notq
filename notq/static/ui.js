function toggle(id) {
    let thing = document.getElementById(id)
    if (thing.style.display == "none")
        thing.style.display = ""
    else
        thing.style.display = "none"
}
