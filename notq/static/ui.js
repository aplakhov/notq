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

function addanswermenu(after, post, comment) {
    const answermenu=`
    <form method="post" action="addcomment" style="display:block">
      <input type="hidden" name="thing" value="${comment}">
      <input type="hidden" name="parent" value="${post}">
      <textarea name="text" style="width:100%"></textarea><br/>
      <input type="submit" name="send" value="Ответить"/>
      <input type="button" onclick="toggle('moar${comment}')" value="..."/>
      <div id='moar${comment}' style="display:none">
		<details style="margin-left: 8px; margin-bottom:2em"><summary style="color:gray; list-style:revert; font-size:small">подсказка по синтаксису</summary>
		<ul><p><strong>notq использует расширенный markdown.</strong> *курсив*, **жирный шрифт** и т.п.</p></details>
        <label for="authorship">Подпись</label>
        <div>
            <input style="margin-top:8px" type="radio" id="thisuser" name="authorship" value="thisuser" checked />
            <label for="thisuser">finder</label>
        </div>
        <div>
          <input type="radio" id="anon" name="authorship" value="anon"/>
          <label for="anon">анонимно (с получением кармы)</label>
        </div>
        <div>
          <input type="radio" id="paranoid" name="authorship" value="paranoid"/>
          <label for="paranoid">совершенно анонимно</label>
        </div>
        <div> <input type="checkbox" id="newpost" style="margin-right:8px"/><label for="newpost"/>отдельным постом</input>
      </div>
    </form>
    `
    after.insertAdjacentHTML('afterend', answermenu)
    after.style.display = "none"
    event.preventDefault()
}