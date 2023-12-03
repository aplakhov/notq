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

function addanswermenu(after, post, comment, cancomment) {
    const answermenu=`
    <form method="post" action="addcomment" style="display:block">
      <input type="hidden" name="parentcomment" value="${comment}">
      <input type="hidden" name="parentpost" value="${post}">
      <textarea name="text" style="width:100%"></textarea><br/>
      <input type="submit" name="send" value="Ответить"/>
      <input type="button" onclick="toggle('moar${comment}')" value="..."/>
      <div id='moar${comment}' style="display:none">
        <label for="authorship">Подпись</label>
        <div>
            <input style="margin-top:8px" type="radio" id="thisuser" name="authorship" value="thisuser" checked />
            <label for="thisuser">от своего имени</label>
        </div>
        <div>
          <input type="radio" id="anon" name="authorship" value="anon"/>
          <label for="anon">анонимно</label>
        </div>
        <div>
          <input type="checkbox" name="newpost">
          <label for="newpost"/>отдельным постом</input>
        </div>
      </div>
      <details style="margin-left: 8px; margin-bottom:2em"><summary style="color:gray; list-style:revert; font-size:small">форматирование ответов</summary>
        <p>notq использует <a href="http://daringfireball.net/projects/markdown/syntax">Markdown</a> с некоторыми расширенными возможностями</p>
        <table><thead><tr><th>Вы вводите</th><th>Что получается</th></tr></thead>
        <tr><td>*курсив*</td><td><em>курсив</em></td></tr>
        <tr><td>**жирный шрифт**</td><td><strong>жирный шрифт</strong></td></tr>
        <tr><td>[Пример ссылки](http://example.net)</td><td><a href="http://example.net">Пример ссылки</a></td></tr>
        <tr><td>/u/username</td><td><a class="username" href="/u/username"><img src="/static/silver.png"/>username</a></td></tr>
        <tr><td>> цитата</td><td><blockquote>цитата</blockquote></td></tr>
        <tr><td>%%спойлер%%</td><td><span class="spoiler">спойлер</span></td></tr>
        <tr><td>* пункт 1<br/>* пункт 2</td><td><ul><li>пункт 1</li><li>пункт 2</li></ul></td></tr>
        </table>
      </details>
    </form>
    `
    if (cancomment)
      after.insertAdjacentHTML('afterend', answermenu)
    else
      flash(after, "Чтобы оставлять комментарии, <a href='/auth/register'>зарегистрируйтесь</a>")
    after.style.display = "none"
    event.preventDefault()
}
