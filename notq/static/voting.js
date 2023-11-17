function vote_any(id, newVal, suffix, handler) {
    let v = document.getElementById("nv" + suffix + id)
    let u = document.getElementById("uv" + suffix + id)
    let d = document.getElementById("dv" + suffix + id)
    let curVal = 0
    if (u.style.color)
        curVal = 1
    else if (d.style.color)
        curVal = -1
    if (newVal == curVal)
        newVal = 0
    v.textContent = Number(v.textContent) - curVal + newVal
    if (newVal > 0)
        u.style.color = "#00a000"
    else
        u.style.color = ""
    if (newVal < 0)
        d.style.color = "#f00000"
    else
        d.style.color = ""
    let urlVal = newVal + 1
    fetch(handler + urlVal, { method: "POST", headers: { "Content-Type": "application/json" }, body: "{}" })
}

function vote(postid, newVal) {
    const handler = "/" + postid + "/vote/"
    vote_any(postid, newVal, "", handler)
}

function votec(postid, commentid, newVal) {
    const handler = "/" + postid + "/votec/" + commentid + "/"
    vote_any(commentid, newVal, "c", handler)
}
