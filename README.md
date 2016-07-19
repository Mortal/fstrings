## Translate string formatting into string interpolation

Python 3.6 introduces [F-strings](https://lwn.net/Articles/656898/)
as a new way of doing string formatting.

Instead of writing this:

```
def say(greeting='hello', target='world'):
    print('%s, %s!' % (greeting.title(), target))
```

... you can now write this:

```
def say(greeting='hello', target='world'):
    print(f'{greeting.title()}, {target}!')
```

This project provides automatic translation of old `%`-style formatting
to the new string interpolation method using F-strings.


### Editor integration

If you use Vim, then simply source the `fstrings.vim` file.
Select a set of lines (with `V`) and press `=` to update the selection.

If you use another editor, you can invoke the `fstrings.py` script as follows:

```sh
python3.6 fstrings.py 40 50 < input.py > tmp.py
```

This parses all of `input.py` and outputs just lines 40-50 to `tmp.py`.
