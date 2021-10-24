# Ankiduo

## Config variables

`target_languages`, `native languages` - language codes to choose from using dropdown lists

`target_lang`, `native_lang` - default target/native language code, use deck rule notation (described below)

`ignored_words` - default ignored words, use deck rule notation; these words will be ignored when searching (e.g. for example articles)

`main_field` - default main field, use deck rule notation

`example_paste_format` - format used to paste examples, `{tl}` is replaced by target language version of the example, and `{nl}` is replaced by native language translation of the example.

`hide_example_translations` - if true, example translations won't be visible by default

## Deck rule notation
```
deck:value;deck2:value2;*:catch all value
```