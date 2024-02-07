This is the source code of [notq](https://notq.ru). You can read more about notq [here](https://notq.ru/238) (in Russian). **TLDR** is that it's a web community not dissimilar to Hackernews, if not that popular (yet?)

As most of its members are native Russian speakers, details follow in Russian.

Перед вами исходный код [notq](https://notq.ru). Вы можете почитать больше о том, что это за сервис, [здесь](https://notq.ru/238).

## Используемые технологии
notq - очень простой сервис, написанный с минимальным использованием фреймворков и других дополнительных зависимостей. Код основан на Flask, в качестве базы данных используется Postgres, а html и js сейчас написаны вручную и очень просты. Свойство минимальности кода и зависимостей хочется поддерживать и впредь.

## Организация кода
- notq - основной код "бекенда"
- notq/static - статика, включая js-код UI и css
- notq/templates - шаблоны HTML
- tests - тесты (pytest-style)

## Как развернуть у себя и протестировать изменения
TBD
